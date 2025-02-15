from __future__ import absolute_import

import os.path
from typing import Optional
from PIL import Image
import numpy as np
from skimage import img_as_float, img_as_uint, img_as_ubyte
from skimage.color.adapt_rgb import adapt_rgb, hsv_value
from skimage.exposure import rescale_intensity, equalize_adapthist

from ocrd import Processor, OcrdPageResult, OcrdPageResultImage
from ocrd_models.ocrd_page import (
    AlternativeImageType,
    PageType,
    OcrdPage,
)


class SkimageNormalize(Processor):

    @property
    def executable(self):
        return 'ocrd-skimage-normalize'

    def process_page_pcgts(self, *input_pcgts: Optional[OcrdPage], page_id: Optional[str] = None) -> OcrdPageResult:
        """Performs contrast-enhancing equalization of segment or page images with scikit-image on the workspace.

        Open and deserialize PAGE input files and their respective images,
        then iterate over the element hierarchy down to the requested
        ``level-of-operation`` in the element hierarchy.

        For each segment element, retrieve a segment image according to
        the layout annotation (from an existing AlternativeImage, or by
        cropping via coordinates into the higher-level image, and -
        when applicable - deskewing), in raw (non-binarized) form.

        Next, normalize the image according to ``method`` in skimage.

        Then write the new image to the workspace along with the output fileGrp,
        and using a file ID with suffix ``.IMG-NRM`` with further identification
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
        features += ',normalized'
        method = self.parameter['method']
        black_point = self.parameter['black-point']
        white_point = self.parameter['white-point']
        self.logger.debug("processing %s image size %s mode %s with method %s [%.1f..%.1f]",
                          coords['features'], str(image.size), str(image.mode),
                          method, black_point, 100 - white_point)
        if image.mode == 'RGBA':
            image = image.convert('RGB')
        elif image.mode == 'LA':
            image = image.convert('L')
        rgb = image.mode == 'RGB'
        array = img_as_float(image)
        # Estimate the  noise standard deviation across color channels.
        pctiles = np.percentile(array, (0.2, 99.8), axis=(0, 1))
        self.logger.debug("2‰ percentiles before: %s", pctiles)
        if method == 'stretch':
            @adapt_rgb(hsv_value)
            def normalize(a):
                # defaults: stretch from in_range='image' to out_range='dtype'
                v_min, v_max = np.percentile(a, (black_point, 100 - white_point))
                return rescale_intensity(a, in_range=(v_min, v_max))
            array = normalize(array)
        elif method == 'adapthist':
            # (implicitly does hsv_value when RGB)
            # defaults: tiles with kernel_size 1/8 width and height
            limit = min(black_point, white_point) / 100
            array = equalize_adapthist(array, clip_limit=limit)
        pctiles = np.percentile(array, (0.2, 99.8), axis=(0, 1))
        self.logger.debug("2‰ percentiles after: %s", pctiles)
        if image.mode in ['F', 'I']:
            array = img_as_uint(array)
        else:
            array = img_as_ubyte(array)
        image = Image.fromarray(array)
        # update PAGE (reference the image file):
        image_ref = AlternativeImageType(comments=features)
        segment.add_AlternativeImage(image_ref)
        suffix = "" if isinstance(segment, PageType) else segment.id
        return OcrdPageResultImage(image, suffix + '.IMG-NRM', image_ref)
