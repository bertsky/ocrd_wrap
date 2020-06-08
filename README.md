# ocrd_wrap

    OCR-D wrapper for arbitrary coords-preserving image operations

## Introduction

This offers [OCR-D](https://ocr-d.de) compliant [workspace processors](https://ocr-d.de/en/spec/cli) for
any image processing tools which have some (usable) CLI
and do not modify/invalidate image coordinates.

It thus _wraps_ them for OCR-D without the need
to write and manage code for each of them individually
(exposing/passing/documenting their parameters and usage,
managing releases etc). It shifts all the burden to
**workflow configuration** (i.e. defining a suitable
parameter set on how to call what program on what data,
and installing all the required tools).

It is itself written in Python, and relies heavily on the
[OCR-D core API](https://github.com/OCR-D/core). This is
responsible for handling METS/PAGE, and providing the OCR-D
CLI.

## Installation

Create and activate a [virtual environment](https://packaging.python.org/tutorials/installing-packages/#creating-virtual-environments) as usual.

To install Python dependencies:

    make deps

Which is the equivalent of:

    pip install -r requirements.txt

To install this module, then do:

    make install

Which is the equivalent of:

    pip install .

## Usage

### [OCR-D processor](https://ocr-d.github.io/cli) interface `ocrd-process-image`

To be used with [PAGE-XML](https://github.com/PRImA-Research-Lab/PAGE-XML) documents in an [OCR-D](https://ocr-d.github.io/) annotation workflow.

```
Usage: ocrd-process-image [OPTIONS]

  Convert or enhance images

Options:
  -V, --version                   Show version
  -l, --log-level [OFF|ERROR|WARN|INFO|DEBUG|TRACE]
                                  Log level
  -J, --dump-json                 Dump tool description as JSON and exit
  -p, --parameter TEXT            Parameters, either JSON string or path 
                                  JSON file
  -g, --page-id TEXT              ID(s) of the pages to process
  -O, --output-file-grp TEXT      File group(s) used as output.
  -I, --input-file-grp TEXT       File group(s) used as input.
  -w, --working-dir TEXT          Working Directory
  -m, --mets TEXT                 METS to process
  -h, --help                      This help message

Parameters:
  "level-of-operation" [string - page] PAGE XML hierarchy level to operate on
    Possible values: ["page", "region", "line", "word", "glyph"]
  "input_feature_selector" [string - ] comma-separated list of required image features
    (e.g. binarized,despeckled)
  "input_feature_filter" [string - ] comma-separated list of forbidden image features
    (e.g. binarized,despeckled)
  "output_feature_added" [string - REQUIRED] image feature(s) to be added after this operation
    (if multiple, separate by comma)
  "input_mimetype" [string - image/png] File format to save input images to
    (tool's expected input)
    Possible values: ["image/bmp", "application/postscript", "image/gif", "image/jpeg",
      "image/jp2", "image/png", "image/x-portable-pixmap", "image/tiff"]
  "output_mimetype" [string - image/png] File format to load output images from
    (tool's expected output)
    Possible values: ["image/bmp", "application/postscript", "image/gif", "image/jpeg",
      "image/jp2", "image/png", "image/x-portable-pixmap", "image/tiff"]
  "command" [string - REQUIRED] shell command to operate on image files,
    with @INFILE as place-holder for the input file path,
    and @OUTFILE as place-holder for the output file path
```

TODO: add example recipes
- enhancement/conversion/denoising using
  * ImageMagick `convert`
  * GIMP [script-fu](https://gitlab.gnome.org/GNOME/gimp/-/tree/master/plug-ins/script-fu/scripts)
  * ...
- binarization using 
  * https://github.com/ajgallego/document-image-binarization
  * https://github.com/qurator-spk/sbb_binarization
  * https://github.com/masyagin1998/robin
  * ...
- text/non-text segmentation using
  * Olena `scribo-cli`
  * ...
- ...

## Testing

none yet

