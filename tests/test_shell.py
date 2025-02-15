# pylint: disable=import-error

import json
import os

from ocrd import run_processor
from ocrd_utils import MIMETYPE_PAGE
from ocrd_models.constants import NAMESPACES
from ocrd_modelfactory import page_from_file

from ocrd_wrap.cli import ShellPreprocessor

from .assets import assets


PARAM = {
    "command": "cp @INFILE @OUTFILE",
    "input_mimetype": "image/png",
    "output_mimetype": "image/tiff",
    "input_feature_filter": "binarized",
    "output_feature_added": "dummy",
}

def analyse_result(ws, level, grp):
    assert os.path.isdir(os.path.join(ws.directory, grp))
    out_files = list(ws.find_files(fileGrp=grp, mimetype=MIMETYPE_PAGE))
    assert len(out_files), "found no output PAGE file"
    out_images = list(ws.find_files(fileGrp=grp, mimetype="//^image/.*"))
    assert len(out_images), "found no output image file"
    out_pcgts = page_from_file(out_files[0])
    assert out_pcgts is not None
    out_images = out_pcgts.etree.xpath('//page:%s/page:AlternativeImage[contains(@comments,"dummy")]' % level, namespaces=NAMESPACES)
    assert len(out_images) > 0, "found no denoised AlternativeImages in output PAGE file"

def test_page(workspace_sbb):
    run_processor(ShellPreprocessor,
                  input_file_grp="OCR-D-IMG",
                  output_file_grp="OCR-D-CPY",
                  parameter={'level-of-operation': 'page', **PARAM},
                  **workspace_sbb,
    )
    ws = workspace_sbb['workspace']
    ws.save_mets()
    analyse_result(ws, 'Page', 'OCR-D-CPY')

def test_regions(workspace_aufklaerung):
    run_processor(ShellPreprocessor,
                  input_file_grp="OCR-D-GT-PAGE",
                  output_file_grp="OCR-D-GT-PAGE-CPY",
                  parameter={'level-of-operation': 'region', **PARAM},
                  **workspace_aufklaerung,
    )
    ws = workspace_aufklaerung['workspace']
    ws.save_mets()
    analyse_result(ws, 'TextRegion', 'OCR-D-GT-PAGE-CPY')

def test_lines(workspace_aufklaerung):
    run_processor(ShellPreprocessor,
                  input_file_grp="OCR-D-GT-PAGE",
                  output_file_grp="OCR-D-GT-PAGE-CPY",
                  parameter={'level-of-operation': 'line', **PARAM},
                  **workspace_aufklaerung,
    )
    ws = workspace_aufklaerung['workspace']
    ws.save_mets()
    analyse_result(ws, 'TextLine', 'OCR-D-GT-PAGE-CPY')
