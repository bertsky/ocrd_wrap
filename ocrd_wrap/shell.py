from __future__ import absolute_import

import os.path
from os import close, unlink, makedirs
from tempfile import mkstemp
import subprocess
from PIL import Image

from ocrd import Processor
from ocrd_utils import (
    getLogger,
    make_file_id,
    assert_file_grp_cardinality,
    MIMETYPE_PAGE,
    MIME_TO_PIL,
    MIME_TO_EXT
)
from ocrd_modelfactory import page_from_file
from ocrd_models.ocrd_page import (
    AlternativeImageType,
    to_xml
)
from .config import OCRD_TOOL

TOOL = 'ocrd-preprocess-image'

class ShellPreprocessor(Processor):

    def __init__(self, *args, **kwargs):
        kwargs['ocrd_tool'] = OCRD_TOOL['tools'][TOOL]
        kwargs['version'] = OCRD_TOOL['version']
        super(ShellPreprocessor, self).__init__(*args, **kwargs)
    
    def process(self):
        """Performs coords-preserving image operations via runtime shell calls anywhere.
        
        Open and deserialize PAGE input files and their respective images,
        then iterate over the element hierarchy down to the requested
        ``level-of-operation`` in the element hierarchy.
        
        For each segment element, retrieve a segment image according to
        the layout annotation (from an existing AlternativeImage, or by
        cropping via coordinates into the higher-level image, and -
        when applicable - deskewing.
        
        If ``input_feature_selector`` and/or ``input_feature_filter`` is
        non-empty, then select/filter among the @imageFilename image and
        the available AlternativeImages the last one which contains all
        of the selected, but none of the filtered features (i.e. @comments
        classes), or raise an error.
        
        Then write that image into a temporary PNG file, create a new METS file ID
        for the result image (based on the segment ID and the operation to be run),
        along with a local path for it, and pass ``command`` to the shell
        after replacing:
        - the string ``@INFILE`` with that input image path, and
        - the string ``@OUTFILE`` with that output image path.
        
        If the shell returns with a failure, skip that segment with an
        approriate error message.
        Otherwise, add the new image to the workspace along with the
        output fileGrp, and using a file ID with suffix ``.IMG-``,
        and further identification of the input element.
        
        Reference it as AlternativeImage in the element,
        adding ``output_feature_added`` to its @comments.
        
        Produce a new PAGE output file by serialising the resulting hierarchy.
        """
        LOG = getLogger('processor.ShellPreprocessor')
        oplevel = self.parameter['level-of-operation']
        feature_selector = self.parameter['input_feature_selector']
        feature_filter = self.parameter['input_feature_filter']
        command = self.parameter['command']
        if '@INFILE' not in command:
            raise Exception("command parameter requires @INFILE pattern")
        if '@OUTFILE' not in command:
            raise Exception("command parameter requires @OUTFILE pattern")
        assert_file_grp_cardinality(self.input_file_grp, 1)
        assert_file_grp_cardinality(self.output_file_grp, 1)
        
        for (n, input_file) in enumerate(self.input_files):
            file_id = make_file_id(input_file, self.output_file_grp)
            page_id = input_file.pageId or input_file.ID
            LOG.info("INPUT FILE %i / %s", n, page_id)
            pcgts = page_from_file(self.workspace.download_file(input_file))
            self.add_metadata(pcgts)
            page = pcgts.get_Page()

            for page in [page]:
                page_image, page_coords, _ = self.workspace.image_from_page(
                    page, page_id,
                    feature_filter=feature_filter, feature_selector=feature_selector)
                if oplevel == 'page':
                    self._process_segment(page, page_image, page_coords,
                                          "page '%s'" % page_id, input_file.pageId,
                                          file_id)
                    continue
                regions = page.get_AllRegions(classes=['Text'])
                if not regions:
                    LOG.warning("Page '%s' contains no text regions", page_id)
                for region in regions:
                    region_image, region_coords = self.workspace.image_from_segment(
                        region, page_image, page_coords,
                        feature_filter=feature_filter, feature_selector=feature_selector)
                    if oplevel == 'region':
                        self._process_segment(region, region_image, region_coords,
                                              "region '%s'" % region.id, None,
                                              file_id + '_' + region.id)
                        continue
                    lines = region.get_TextLine()
                    if not lines:
                        LOG.warning("Region '%s' contains no text lines", region.id)
                    for line in lines:
                        line_image, line_coords = self.workspace.image_from_segment(
                            line, region_image, region_coords,
                            feature_filter=feature_filter, feature_selector=feature_selector)
                        if oplevel == 'line':
                            self._process_segment(line, line_image, line_coords,
                                                  "line '%s'" % line.id, None,
                                                  file_id + '_' + line.id)
                            continue
                        words = line.get_Word()
                        if not words:
                            LOG.warning("Line '%s' contains no words", line.id)
                        for word in words:
                            word_image, word_coords = self.workspace.image_from_segment(
                                word, line_image, line_coords,
                                feature_filter=feature_filter, feature_selector=feature_selector)
                            if oplevel == 'word':
                                self._process_segment(word, word_image, word_coords,
                                                      "word '%s'" % word.id, None,
                                                      file_id + '_' + word.id)
                                continue
                            glyphs = word.get_Glyph()
                            if not glyphs:
                                LOG.warning("Word '%s' contains no glyphs", word.id)
                            for glyph in glyphs:
                                glyph_image, glyph_coords = self.workspace.image_from_segment(
                                    glyph, word_image, word_coords,
                                    feature_filter=feature_filter, feature_selector=feature_selector)
                                self._process_segment(glyph, glyph_image, glyph_coords,
                                                      "glyph '%s'" % glyph.id, None,
                                                      file_id + '_' + glyph.id)
            
            pcgts.set_pcGtsId(file_id)
            self.workspace.add_file(
                ID=file_id,
                file_grp=self.output_file_grp,
                pageId=input_file.pageId,
                mimetype=MIMETYPE_PAGE,
                local_filename=os.path.join(self.output_file_grp,
                                            file_id + '.xml'),
                content=to_xml(pcgts))
    
    def _process_segment(self, segment, image, coords, where, page_id, file_id):
        LOG = getLogger('processor.ShellPreprocessor')
        features = coords['features'] # features already applied to image
        feature_added = self.parameter['output_feature_added']
        if feature_added:
            features += ',' + feature_added
        command = self.parameter['command']
        input_mime = self.parameter['input_mimetype']
        output_mime = self.parameter['output_mimetype']
        # save retrieved segment image to temporary file
        in_fd, in_fname = mkstemp(suffix=file_id + MIME_TO_EXT[input_mime])
        image.save(in_fname, format=MIME_TO_PIL[input_mime])
        # prepare output file name
        out_id = file_id + '.IMG-' + feature_added.upper().replace(',', '-')
        out_fname = os.path.join(self.output_file_grp,
                                 out_id + MIME_TO_EXT[output_mime])
        if not os.path.exists(self.output_file_grp):
            makedirs(self.output_file_grp)
        # remove quotation around filename patterns, if any
        command = command.replace('"@INFILE"', '@INFILE')
        command = command.replace('"@OUTFILE"', '@OUTFILE')
        command = command.replace("'@INFILE'", '@INFILE')
        command = command.replace("'@OUTFILE'", '@OUTFILE')
        # replace filename patterns with actual paths, quoted
        command = command.replace('@INFILE', '"' + in_fname + '"')
        command = command.replace('@OUTFILE', '"' + out_fname + '"')
        # execute command pattern
        LOG.debug("Running command: '%s'", command)
        # pylint: disable=subprocess-run-check
        result = subprocess.run(command, shell=True,
                                universal_newlines=True,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        close(in_fd)
        unlink(in_fname)
        LOG.debug("Command for %s returned: %d", where, result.returncode)
        if result.stdout:
            LOG.info("Command for %s stdout: %s", where, result.stdout)
        if result.stderr:
            LOG.warning("Command for %s stderr: %s", where, result.stderr)
        if result.returncode != 0:
            LOG.error("Command for %s failed", where)
            if os.path.exists(out_fname):
                unlink(out_fname)
            return
        # check resulting image
        with Image.open(out_fname) as image2:
            if image.size != image2.size:
                LOG.error("Command for %s produced image of different size (%s vs %s)",
                          where, str(image.size), str(image2.size))
                return
        # annotate results
        self.workspace.add_file(
            ID=out_id,
            local_filename=out_fname,
            file_grp=self.output_file_grp,
            pageId=page_id,
            mimetype=output_mime)
        LOG.info("created file ID: %s, file_grp: %s, path: %s",
                 out_id, self.output_file_grp, out_fname)
        segment.add_AlternativeImage(AlternativeImageType(
            filename=out_fname, comments=features))
