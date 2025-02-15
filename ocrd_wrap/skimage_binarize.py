from __future__ import absolute_import

import os.path
from typing import Optional
from PIL import Image
import numpy as np
from skimage.filters import (
    threshold_niblack,
    threshold_li,
    threshold_local,
    threshold_otsu,
    threshold_sauvola,
    threshold_yen
)

from ocrd import Processor, OcrdPageResult, OcrdPageResultImage
from ocrd_models.ocrd_page import (
    AlternativeImageType,
    PageType,
    OcrdPage,
)


def odd(n):
    return int(n) + int((n+1)%2)

class SkimageBinarize(Processor):

    @property
    def executable(self):
        return 'ocrd-skimage-binarize'

    def process_page_pcgts(self, *input_pcgts: Optional[OcrdPage], page_id: Optional[str] = None) -> OcrdPageResult:
        """Performs binarization of segment or page images with scikit-image on the workspace.

        Open and deserialize PAGE input files and their respective images,
        then iterate over the element hierarchy down to the requested
        ``level-of-operation`` in the element hierarchy.

        For each segment element, retrieve a segment image according to
        the layout annotation (from an existing AlternativeImage, or by
        cropping via coordinates into the higher-level image, and -
        when applicable - deskewing).

        Next, binarize the image according to ``method`` with skimage.

        Then write the new image to the workspace along with the output fileGrp,
        and using a file ID with suffix ``.IMG-BIN`` with further identification
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

        params = dict(self.parameter)
        # guess a useful window size if not given
        if not params['window_size']:
            # use 1x1 inch square
            params['window_size'] = odd(dpi)
        if not params['k']:
            params['k'] = 0.34

        if oplevel == 'page':
            image = self._process_segment(page, page_image, page_coords, params)
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
                image = self._process_segment(region, region_image, region_coords, params)
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
                    image = self._process_segment(line, line_image, line_coords, params)
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
                        image = self._process_segment(word, word_image, word_coords, params)
                        if image:
                            result.images.append(image)
                        continue

                    glyphs = word.get_Glyph()
                    if not glyphs:
                        self.logger.warning("Word '%s' contains no glyphs", word.id)
                    for glyph in glyphs:
                        glyph_image, glyph_coords = self.workspace.image_from_segment(
                            glyph, word_image, word_coords, feature_filter='binarized')
                        image = self._process_segment(glyph, glyph_image, glyph_coords, params)
                        if image:
                            result.images.append(image)
        return result

    def _process_segment(self, segment, image, coords, params: dict) -> Optional[OcrdPageResultImage]:
        features = coords['features'] # features already applied to image
        features += ',binarized'
        method = params['method']
        array = np.array(image.convert('L'))
        if method == 'otsu':
            thres = threshold_otsu(array)
        elif method == 'li':
            thres = threshold_li(array)
        elif method == 'yen':
            thres = threshold_yen(array)
        elif method == 'gauss':
            thres = threshold_local(array, params['window_size'])
        elif method == 'niblack':
            thres = threshold_niblack(array, params['window_size'], params['k'])
        elif method == 'sauvola':
            thres = threshold_sauvola(array, params['window_size'], params['k'])
        array = array > thres
        image = Image.fromarray(array)
        # update PAGE (reference the image file):
        image_ref = AlternativeImageType(comments=features)
        segment.add_AlternativeImage(image_ref)
        suffix = "" if isinstance(segment, PageType) else segment.id
        return OcrdPageResultImage(image, suffix + '.IMG-BIN', image_ref)
