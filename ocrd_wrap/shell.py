from __future__ import absolute_import

import os.path
from tempfile import TemporaryDirectory
from typing import Optional
import subprocess
from PIL import Image

from ocrd import Processor, OcrdPageResult, OcrdPageResultImage
from ocrd_utils import (
    MIME_TO_PIL,
    MIME_TO_EXT
)
from ocrd_models.ocrd_page import (
    AlternativeImageType,
    PageType,
    OcrdPage,
)

class ShellPreprocessor(Processor):

    @property
    def executable(self):
        return 'ocrd-preprocess-image'

    def setup(self):
        command = self.parameter['command']
        if '@INFILE' not in command:
            raise Exception("command parameter requires @INFILE pattern")
        if '@OUTFILE' not in command:
            raise Exception("command parameter requires @OUTFILE pattern")

    def process_page_pcgts(self, *input_pcgts: Optional[OcrdPage], page_id: Optional[str] = None) -> OcrdPageResult:
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
        pcgts = input_pcgts[0]
        result = OcrdPageResult(pcgts)
        page = pcgts.get_Page()
        oplevel = self.parameter['level-of-operation']
        feature_selector = self.parameter['input_feature_selector']
        feature_filter = self.parameter['input_feature_filter']

        page_image, page_coords, _ = self.workspace.image_from_page(
            page, page_id,
            feature_filter=feature_filter, feature_selector=feature_selector)
        if oplevel == 'page':
            image = self._process_segment(
                page, page_image, page_coords, "page '%s'" % page_id)
            if image:
                result.images.append(image)
            return result

        regions = page.get_AllRegions(classes=['Text'])
        if not regions:
            self.logger.warning("Page '%s' contains no text regions", page_id)
        for region in regions:
            region_image, region_coords = self.workspace.image_from_segment(
                region, page_image, page_coords,
                feature_filter=feature_filter, feature_selector=feature_selector)
            if oplevel == 'region':
                image = self._process_segment(
                    region, region_image, region_coords, "region '%s'" % region.id)
                if image:
                    result.images.append(image)
                continue

            lines = region.get_TextLine()
            if not lines:
                self.logger.warning("Region '%s' contains no text lines", region.id)
            for line in lines:
                line_image, line_coords = self.workspace.image_from_segment(
                    line, region_image, region_coords,
                    feature_filter=feature_filter, feature_selector=feature_selector)
                if oplevel == 'line':
                    image = self._process_segment(
                        line, line_image, line_coords, "line '%s'" % line.id)
                    if image:
                        result.images.append(image)
                    continue

                words = line.get_Word()
                if not words:
                    self.logger.warning("Line '%s' contains no words", line.id)
                for word in words:
                    word_image, word_coords = self.workspace.image_from_segment(
                        word, line_image, line_coords,
                        feature_filter=feature_filter, feature_selector=feature_selector)
                    if oplevel == 'word':
                        image = self._process_segment(
                            word, word_image, word_coords, "word '%s'" % word.id)
                        if image:
                            result.images.append(image)
                        continue

                    glyphs = word.get_Glyph()
                    if not glyphs:
                        self.logger.warning("Word '%s' contains no glyphs", word.id)
                    for glyph in glyphs:
                        glyph_image, glyph_coords = self.workspace.image_from_segment(
                            glyph, word_image, word_coords,
                            feature_filter=feature_filter, feature_selector=feature_selector)
                        image = self._process_segment(
                            glyph, glyph_image, glyph_coords, "glyph '%s'" % glyph.id)
                        if image:
                            result.images.append(image)
        return result

    def _process_segment(self, segment, image, coords, where) -> Optional[OcrdPageResultImage]:
        features = coords['features'] # features already applied to image
        feature_added = self.parameter['output_feature_added']
        if feature_added:
            features += ',' + feature_added
        command = self.parameter['command']
        input_mime = self.parameter['input_mimetype']
        output_mime = self.parameter['output_mimetype']
        in_fname = "in" + MIME_TO_EXT[input_mime]
        out_fname = "out" + MIME_TO_EXT[output_mime]
        with TemporaryDirectory(suffix=segment.id) as tmpdir:
            in_path = os.path.join(tmpdir, in_fname)
            out_path = os.path.join(tmpdir, out_fname)
            # save retrieved segment image to temporary file
            with open(in_path, 'wb') as in_file:
                image.save(in_file, format=MIME_TO_PIL[input_mime])
            # remove quotation around filename patterns, if any
            command = command.replace('"@INFILE"', '@INFILE').replace('"@OUTFILE"', '@OUTFILE')
            command = command.replace("'@INFILE'", '@INFILE').replace("'@OUTFILE'", '@OUTFILE')
            # replace filename patterns with actual paths, quoted
            command = command.replace('@INFILE', '"' + in_path + '"').replace('@OUTFILE', '"' + out_path + '"')
            # execute command pattern
            self.logger.debug("Running command: '%s'", command)
            # pylint: disable=subprocess-run-check
            result = subprocess.run(command, shell=True,
                                    universal_newlines=True,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
            self.logger.debug("Command for %s returned: %d", where, result.returncode)
            if result.stdout:
                self.logger.info("Command for %s stdout: %s", where, result.stdout)
            if result.stderr:
                self.logger.warning("Command for %s stderr: %s", where, result.stderr)
            if result.returncode != 0:
                self.logger.error("Command for %s failed", where)
                return None
            image2 = Image.open(out_path)
            # check resulting image
            if image.size != image2.size:
                self.logger.error("Command for %s produced image of different size (%s vs %s)",
                                  where, str(image.size), str(image2.size))
                return None
        # update PAGE (reference the image file):
        image_ref = AlternativeImageType(comments=features)
        segment.add_AlternativeImage(image_ref)
        suffix = "" if isinstance(segment, PageType) else segment.id
        return OcrdPageResultImage(
            image2,
            suffix + '.IMG-' + feature_added.upper().replace(',', '-'),
            image_ref
        )
