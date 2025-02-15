from __future__ import absolute_import

import os.path
from typing import Optional
from PIL import Image
import numpy as np
from skimage.morphology import (
    binary_dilation, disk,
    reconstruction,
    remove_small_holes
)

from ocrd import Processor, OcrdPageResult, OcrdPageResultImage
from ocrd_models.ocrd_page import (
    AlternativeImageType,
    PageType,
    OcrdPage,
)


class SkimageDenoise(Processor):

    @property
    def executable(self):
        return 'ocrd-skimage-denoise'

    def setup(self):
        if self.parameter['protect']:
            assert self.parameter['protect'] <= self.parameter['maxsize'], \
                "'protect' parameter must not be larger than 'maxsize'"

    def process_page_pcgts(self, *input_pcgts: Optional[OcrdPage], page_id: Optional[str] = None) -> OcrdPageResult:
        """Performs binary denoising of segment or page images with scikit-image on the workspace.

        Open and deserialize PAGE input files and their respective images,
        then iterate over the element hierarchy down to the requested
        ``level-of-operation`` in the element hierarchy.

        For each segment element, retrieve a segment image according to
        the layout annotation (from an existing AlternativeImage, or by
        cropping via coordinates into the higher-level image, and -
        when applicable - deskewing), in binarized form.

        Next, denoise the image by removing too small connected components
        with skimage. (If ``protect`` is non-zero, then avoid removing specks
        near large connected components up to that distance.)

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
            page, page_id, feature_selector='binarized')
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
            image = self._process_segment(page, page_image, page_coords, dpi)
            if image:
                result.images.append(image)
            return result

        regions = page.get_AllRegions(classes=['Text'])
        if not regions:
            self.logger.warning("Page '%s' contains no text regions", page_id)
        for region in regions:
            region_image, region_coords = self.workspace.image_from_segment(
                region, page_image, page_coords, feature_selector='binarized')
            if oplevel == 'region':
                image = self._process_segment(region, region_image, region_coords, dpi)
                if image:
                    result.images.append(image)
                continue

            lines = region.get_TextLine()
            if not lines:
                self.logger.warning("Region '%s' contains no text lines", region.id)
            for line in lines:
                line_image, line_coords = self.workspace.image_from_segment(
                    line, region_image, region_coords, feature_selector='binarized')
                if oplevel == 'line':
                    image = self._process_segment(line, line_image, line_coords, dpi)
                    if image:
                        result.images.append(image)
                    continue

                words = line.get_Word()
                if not words:
                    self.logger.warning("Line '%s' contains no words", line.id)
                for word in words:
                    word_image, word_coords = self.workspace.image_from_segment(
                        word, line_image, line_coords, feature_selector='binarized')
                    if oplevel == 'word':
                        image = self._process_segment(word, word_image, word_coords, dpi)
                        if image:
                            result.images.append(image)
                        continue

                    glyphs = word.get_Glyph()
                    if not glyphs:
                        self.logger.warning("Word '%s' contains no glyphs", word.id)
                    for glyph in glyphs:
                        glyph_image, glyph_coords = self.workspace.image_from_segment(
                            glyph, word_image, word_coords, feature_selector='binarized')
                        image = self._process_segment(glyph, glyph_image, glyph_coords, dpi)
                        if image:
                            result.images.append(image)
        return result

    def _process_segment(self, segment, image, coords, dpi) -> Optional[OcrdPageResultImage]:
        features = coords['features'] # features already applied to image
        features += ',despeckled'
        maxsize = self.parameter['maxsize']
        maxsize *= dpi/72 # in px instead of pt
        maxsize **= 2 # area
        protect = self.parameter['protect']
        protect *= dpi/72 # in px instead of pt
        array = np.array(image)
        dtype = array.dtype
        scale = array.max()
        array = ~array.astype(bool)
        # suppress bg specks in fg (holes in binary-inverted)
        array1 = remove_small_holes(array, area_threshold=maxsize)
        # suppress fg specks in bg (blobs in binary-inverted)
        array2 = ~remove_small_holes(~array1, area_threshold=maxsize)
        if protect:
            # reconstruct fragments of larger objects
            recons = binary_dilation(array2, disk(protect))
            recons = reconstruction(recons & array1, array1)
            array2 |= recons.astype(bool)
        array = ~array2
        image = Image.fromarray(array.astype(dtype) * scale)
        # update PAGE (reference the image file):
        image_ref = AlternativeImageType(comments=features)
        segment.add_AlternativeImage(image_ref)
        suffix = "" if isinstance(segment, PageType) else segment.id
        return OcrdPageResultImage(image, suffix + '.IMG-DEN', image_ref)
