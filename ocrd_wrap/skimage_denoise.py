from __future__ import absolute_import

import os.path
from PIL import Image
import numpy as np
from skimage.morphology import (
    remove_small_objects,
    remove_small_holes
)

from ocrd import Processor
from ocrd_utils import (
    getLogger,
    make_file_id,
    assert_file_grp_cardinality,
    MIMETYPE_PAGE
)
from ocrd_modelfactory import page_from_file
from ocrd_models.ocrd_page import (
    AlternativeImageType,
    to_xml
)
from .config import OCRD_TOOL

TOOL = 'ocrd-skimage-denoise'

class SkimageDenoise(Processor):

    def __init__(self, *args, **kwargs):
        kwargs['ocrd_tool'] = OCRD_TOOL['tools'][TOOL]
        kwargs['version'] = OCRD_TOOL['version']
        super(SkimageDenoise, self).__init__(*args, **kwargs)
    
    def process(self):
        """Performs binary denoising of segment or page images with scikit-image on the workspace.
        
        Open and deserialize PAGE input files and their respective images,
        then iterate over the element hierarchy down to the requested
        ``level-of-operation`` in the element hierarchy.
        
        For each segment element, retrieve a segment image according to
        the layout annotation (from an existing AlternativeImage, or by
        cropping via coordinates into the higher-level image, and -
        when applicable - deskewing), in binarized form.
        
        Next, denoise the image by removing too small connected components
        with skimage.
        
        Then write the new image to the workspace along with the output fileGrp,
        and using a file ID with suffix ``.IMG-DEN`` with further identification
        of the input element.
        
        Produce a new PAGE output file by serialising the resulting hierarchy.
        """
        LOG = getLogger('processor.SkimageDenoise')
        assert_file_grp_cardinality(self.input_file_grp, 1)
        assert_file_grp_cardinality(self.output_file_grp, 1)
        oplevel = self.parameter['level-of-operation']
        
        for (n, input_file) in enumerate(self.input_files):
            file_id = make_file_id(input_file, self.output_file_grp)
            page_id = input_file.pageId or input_file.ID
            LOG.info("INPUT FILE %i / %s", n, page_id)
            
            pcgts = page_from_file(self.workspace.download_file(input_file))
            self.add_metadata(pcgts)
            page = pcgts.get_Page()
            
            for page in [page]:
                page_image, page_coords, page_image_info = self.workspace.image_from_page(
                    page, page_id, feature_selector='binarized')
                if self.parameter['dpi'] > 0:
                    dpi = self.parameter['dpi']
                    LOG.info("Page '%s' images will use %d DPI from parameter override", page_id, dpi)
                elif page_image_info.resolution != 1:
                    dpi = page_image_info.resolution
                    if page_image_info.resolutionUnit == 'cm':
                        dpi = round(dpi * 2.54)
                    LOG.info("Page '%s' images will use %d DPI from image meta-data", page_id, dpi)
                else:
                    dpi = 300
                    LOG.info("Page '%s' images will use 300 DPI from fall-back", page_id)
                maxsize = self.parameter['maxsize'] # in pt
                maxsize *= dpi/72 # in px
                #maxsize **= 2 # area
                
                if oplevel == 'page':
                    self._process_segment(page, page_image, page_coords, maxsize,
                                          "page '%s'" % page_id, input_file.pageId,
                                          file_id + '.IMG-DEN')
                    continue
                regions = page.get_AllRegions(classes=['Text'])
                if not regions:
                    LOG.warning("Page '%s' contains no text regions", page_id)
                for region in regions:
                    region_image, region_coords = self.workspace.image_from_segment(
                        region, page_image, page_coords, feature_selector='binarized')
                    if oplevel == 'region':
                        self._process_segment(region, region_image, region_coords, maxsize,
                                              "region '%s'" % region.id, input_file.pageId,
                                              file_id + '.IMG-DEN_' + region.id)
                        continue
                    lines = region.get_TextLine()
                    if not lines:
                        LOG.warning("Region '%s' contains no text lines", region.id)
                    for line in lines:
                        line_image, line_coords = self.workspace.image_from_segment(
                            line, region_image, region_coords, feature_selector='binarized')
                        if oplevel == 'line':
                            self._process_segment(line, line_image, line_coords, maxsize,
                                                  "line '%s'" % line.id, input_file.pageId,
                                                  file_id + '.IMG-DEN_' + line.id)
                            continue
                        words = line.get_Word()
                        if not words:
                            LOG.warning("Line '%s' contains no words", line.id)
                        for word in words:
                            word_image, word_coords = self.workspace.image_from_segment(
                                word, line_image, line_coords, feature_selector='binarized')
                            if oplevel == 'word':
                                self._process_segment(word, word_image, word_coords, maxsize,
                                                      "word '%s'" % word.id, input_file.pageId,
                                                      file_id + '.IMG-DEN_' + word.id)
                                continue
                            glyphs = word.get_Glyph()
                            if not glyphs:
                                LOG.warning("Word '%s' contains no glyphs", word.id)
                            for glyph in glyphs:
                                glyph_image, glyph_coords = self.workspace.image_from_segment(
                                    glyph, word_image, word_coords, feature_selector='binarized')
                                self._process_segment(glyph, glyph_image, glyph_coords, maxsize,
                                                      "glyph '%s'" % glyph.id, input_file.pageId,
                                                      file_id + '.IMG-DEN_' + glyph.id)
            
            pcgts.set_pcGtsId(file_id)
            self.workspace.add_file(
                ID=file_id,
                file_grp=self.output_file_grp,
                pageId=input_file.pageId,
                mimetype=MIMETYPE_PAGE,
                local_filename=os.path.join(self.output_file_grp,
                                            file_id + '.xml'),
                content=to_xml(pcgts))
    
    def _process_segment(self, segment, image, coords, maxsize, where, page_id, file_id):
        LOG = getLogger('processor.SkimageDenoise')
        features = coords['features'] # features already applied to image
        features += ',despeckled'
        array = np.array(image).astype('bool')
        # suppress bg specks in fg (holes in binary-inverted)
        remove_small_objects(array, min_size=maxsize, in_place=True)
        # suppress fg specks in bg (blobs in binary-inverted)
        remove_small_holes(array, area_threshold=maxsize, in_place=True)
        image = Image.fromarray(array)
        # annotate results
        file_path = self.workspace.save_image_file(
            image,
            file_id,
            file_grp=self.output_file_grp,
            page_id=page_id)
        segment.add_AlternativeImage(AlternativeImageType(
            filename=file_path, comments=features))
        LOG.debug("Despeckled image for %s saved as '%s'", where, file_path)
