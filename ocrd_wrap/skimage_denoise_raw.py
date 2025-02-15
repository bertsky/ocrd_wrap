from __future__ import absolute_import

import os.path
from typing import Optional
from packaging.version import Version
from PIL import Image
from skimage import img_as_uint, img_as_ubyte, __version__ as skimage_version
from skimage.restoration import denoise_wavelet, estimate_sigma

from ocrd import Processor, OcrdPageResult, OcrdPageResultImage
from ocrd_models.ocrd_page import (
    AlternativeImageType,
    PageType,
    OcrdPage,
)


class SkimageDenoiseRaw(Processor):

    @property
    def executable(self):
        return 'ocrd-skimage-denoise-raw'

    def setup(self):
        if Version(skimage_version) >= Version('0.19'):
            def kwargs(rgb: bool) -> dict:
                if rgb:
                    return dict(channel_axis=-1, average_sigmas=True)
                else:
                    return dict(channel_axis=None, average_sigmas=False)
        else:
            def kwargs(rgb: bool) -> dict:
                return dict(multichannel=rgb, average_sigmas=rgb)
        self.skimage_kwargs = kwargs

    def process_page_pcgts(self, *input_pcgts: Optional[OcrdPage], page_id: Optional[str] = None) -> OcrdPageResult:
        """Performs raw denoising of segment or page images with scikit-image on the workspace.

        Open and deserialize PAGE input files and their respective images,
        then iterate over the element hierarchy down to the requested
        ``level-of-operation`` in the element hierarchy.

        For each segment element, retrieve a segment image according to
        the layout annotation (from an existing AlternativeImage, or by
        cropping via coordinates into the higher-level image, and -
        when applicable - deskewing), in raw (non-binarized) form.

        Next, denoise the image with a Wavelet transform scheme according
        to ``method`` in skimage.

        Then write the new image to the workspace along with the output fileGrp,
        and using a file ID with suffix ``.IMG-DEN`` with further identification
        of the input element.

        Produce a new PAGE output file by serialising the resulting hierarchy.
        """
        pcgts = input_pcgts[0]
        result = OcrdPageResult(pcgts)
        page = pcgts.get_Page()
        oplevel = self.parameter['level-of-operation']

        page_image, page_coords, page_image_info = self.workspace.image_from_page(
            page, page_id, feature_filter='binarized')
        if self.parameter['dpi'] > 0:
            dpi = self.parameter['dpi']
            self.logger.info("Page '%s' images will use %d DPI from parameter override", page_id, dpi)
        elif page_image_info.resolution != 1:
            dpi = page_image_info.resolution
            if page_image_info.resolutionUnit == 'cm':
                dpi = round(dpi * 2.54)
            self.logger.info("Page '%s' images will use %d DPI from image meta-data", page_id, dpi)
        else:
            dpi = 300
            self.logger.info("Page '%s' images will use 300 DPI from fall-back", page_id)

        if oplevel == 'page':
            image = self._process_segment(page, page_image, page_coords)
            if image:
                result.images.append(image)
            return result

        regions = page.get_AllRegions(classes=['Text'])
        if not regions:
            self.logger.warning("Page '%s' contains no text regions", page_id)
        for region in regions:
            region_image, region_coords = self.workspace.image_from_segment(
                region, page_image, page_coords, feature_filter='binarized')
            if oplevel == 'region':
                image = self._process_segment(region, region_image, region_coords)
                if image:
                    result.images.append(image)
                continue

            lines = region.get_TextLine()
            if not lines:
                self.logger.warning("Region '%s' contains no text lines", region.id)
            for line in lines:
                line_image, line_coords = self.workspace.image_from_segment(
                    line, region_image, region_coords, feature_filter='binarized')
                if oplevel == 'line':
                    image = self._process_segment(line, line_image, line_coords)
                    if image:
                        result.images.append(image)
                    continue

                words = line.get_Word()
                if not words:
                    self.logger.warning("Line '%s' contains no words", line.id)
                for word in words:
                    word_image, word_coords = self.workspace.image_from_segment(
                        word, line_image, line_coords, feature_filter='binarized')
                    if oplevel == 'word':
                        image = self._process_segment(word, word_image, word_coords)
                        if image:
                            result.images.append(image)
                        continue

                    glyphs = word.get_Glyph()
                    if not glyphs:
                        self.logger.warning("Word '%s' contains no glyphs", word.id)
                    for glyph in glyphs:
                        glyph_image, glyph_coords = self.workspace.image_from_segment(
                            glyph, word_image, word_coords, feature_filter='binarized')
                        image = self._process_segment(glyph, glyph_image, glyph_coords)
                        if image:
                            result.images.append(image)
        return result

    def _process_segment(self, segment, image, coords) -> Optional[OcrdPageResultImage]:
        features = coords['features'] # features already applied to image
        features += ',despeckled'
        method = self.parameter['method']
        self.logger.debug("processing %s image size %s mode %s with method %s",
                          coords['features'], str(image.size), str(image.mode), method)
        if image.mode == 'RGBA':
            image = image.convert('RGB')
        elif image.mode == 'LA':
            image = image.convert('L')
        kwargs = self.skimage_kwargs(image.mode == 'RGB')
        kwargs2 = dict(kwargs)
        kwargs2["convert2ycbcr"] = kwargs2.pop("average_sigmas")
        array = img_as_uint(image)
        # Estimate the average noise standard deviation across color channels.
        sigma_est = estimate_sigma(array, **kwargs)
        self.logger.debug("estimated sigma before: %s", sigma_est)
        if sigma_est < 1e-5:
            # avoid adverse effects of denoising already clean images
            return None
        array = denoise_wavelet(array,
                                # BayesShrink does not seem to do much, but ignores sigma;
                                # VisuShrink works but tends to underestimate sigma
                                #sigma=None if method == 'BayesShrink' else sigma_est/4,
                                method=method, mode='soft', rescale_sigma=True,
                                **kwargs2
        )
        sigma_est = estimate_sigma(array, **kwargs)
        self.logger.debug("estimated sigma after: %s", sigma_est)
        if image.mode in ['F', 'I']:
            array = img_as_uint(array)
        else:
            array = img_as_ubyte(array)
        image = Image.fromarray(array)
        # update PAGE (reference the image file):
        image_ref = AlternativeImageType(comments=features)
        segment.add_AlternativeImage(image_ref)
        suffix = "" if isinstance(segment, PageType) else segment.id
        return OcrdPageResultImage(image, suffix + '.IMG-DEN', image_ref)
