[![PyPI version](https://badge.fury.io/py/ocrd-wrap.svg)](https://badge.fury.io/py/ocrd-wrap)

# ocrd_wrap

    OCR-D wrapper for arbitrary coords-preserving image operations

  * [Introduction](#introduction)
  * [Installation](#installation)
  * [Usage](#usage)
     * [OCR-D processor interface ocrd-preprocess-image](#ocr-d-processor-interface-ocrd-preprocess-image)
     * [OCR-D processor interface ocrd-skimage-normalize](#ocr-d-processor-interface-ocrd-skimage-normalize)
     * [OCR-D processor interface ocrd-skimage-denoise-raw](#ocr-d-processor-interface-ocrd-skimage-denoise-raw)
     * [OCR-D processor interface ocrd-skimage-binarize](#ocr-d-processor-interface-ocrd-skimage-binarize)
     * [OCR-D processor interface ocrd-skimage-denoise](#ocr-d-processor-interface-ocrd-skimage-denoise)
  * [Testing](#testing)


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

In addition, this aims to wrap existing Python packages
for preprocessing as OCR-D processors (one at a time).

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

### [OCR-D processor](https://ocr-d.github.io/cli) interface `ocrd-preprocess-image`

To be used with [PAGE-XML](https://github.com/PRImA-Research-Lab/PAGE-XML) documents in an [OCR-D](https://ocr-d.github.io/) annotation workflow.

```
Usage: ocrd-preprocess-image [OPTIONS]

  Convert or enhance images

Options:
  -I, --input-file-grp USE        File group(s) used as input
  -O, --output-file-grp USE       File group(s) used as output
  -g, --page-id ID                Physical page ID(s) to process
  --overwrite                     Remove existing output pages/images
                                  (with --page-id, remove only those)
  -p, --parameter JSON-PATH       Parameters, either verbatim JSON string
                                  or JSON file path
  -m, --mets URL-PATH             URL or file path of METS to process
  -w, --working-dir PATH          Working directory of local workspace
  -l, --log-level [OFF|ERROR|WARN|INFO|DEBUG|TRACE]
                                  Log level
  -J, --dump-json                 Dump tool description as JSON and exit
  -h, --help                      This help message
  -V, --version                   Show version

Parameters:
   "level-of-operation" [string - "page"]
    PAGE XML hierarchy level to operate on
    Possible values: ["page", "region", "line", "word", "glyph"]
   "input_feature_selector" [string - ""]
    comma-separated list of required image features (e.g.
    binarized,despeckled)
   "input_feature_filter" [string - ""]
    comma-separated list of forbidden image features (e.g.
    binarized,despeckled)
   "output_feature_added" [string - REQUIRED]
    image feature(s) to be added after this operation (if multiple,
    separate by comma)
   "input_mimetype" [string - "image/png"]
    File format to save input images to (tool's expected input)
    Possible values: ["image/bmp", "application/postscript", "image/gif",
    "image/jpeg", "image/jp2", "image/png", "image/x-portable-pixmap",
    "image/tiff"]
   "output_mimetype" [string - "image/png"]
    File format to load output images from (tool's expected output)
    Possible values: ["image/bmp", "application/postscript", "image/gif",
    "image/jpeg", "image/jp2", "image/png", "image/x-portable-pixmap",
    "image/tiff"]
   "command" [string - REQUIRED]
    shell command to operate on image files, with @INFILE as place-holder
    for the input file path, and @OUTFILE as place-holder for the output
    file path
```

#### example recipes
- enhancement/conversion/denoising using
  - [x] ImageMagick: [param_im6convert-denoise-raw](ocrd_wrap/param_im6convert-denoise-raw.json)
  - [ ] GIMP [script-fu](https://gitlab.gnome.org/GNOME/gimp/-/tree/master/plug-ins/script-fu/scripts)
  - [ ] ...
- binarization using 
  - [x] Olena/Scribo: [param_scribo-cli-binarize-sauvola-ms-split](ocrd_wrap/param_scribo-cli-binarize-sauvola-ms-split.json)
  - [ ] https://github.com/ajgallego/document-image-binarization ...
  - [ ] https://github.com/qurator-spk/sbb_binarization ...
  - [ ] https://github.com/masyagin1998/robin ...
  - [ ] ...
- text/non-text segmentation using
  - [ ] Olena/Scribo ...
  - [ ] ...
- ...

### [OCR-D processor](https://ocr-d.github.io/cli) interface `ocrd-skimage-normalize`

To be used with [PAGE-XML](https://github.com/PRImA-Research-Lab/PAGE-XML) documents in an [OCR-D](https://ocr-d.github.io/) annotation workflow.

```
Usage: ocrd-skimage-normalize [OPTIONS]

  Equalize contrast/exposure of images with Scikit-image

Options:
  -I, --input-file-grp USE        File group(s) used as input
  -O, --output-file-grp USE       File group(s) used as output
  -g, --page-id ID                Physical page ID(s) to process
  --overwrite                     Remove existing output pages/images
                                  (with --page-id, remove only those)
  -p, --parameter JSON-PATH       Parameters, either verbatim JSON string
                                  or JSON file path
  -m, --mets URL-PATH             URL or file path of METS to process
  -w, --working-dir PATH          Working directory of local workspace
  -l, --log-level [OFF|ERROR|WARN|INFO|DEBUG|TRACE]
                                  Log level
  -J, --dump-json                 Dump tool description as JSON and exit
  -h, --help                      This help message
  -V, --version                   Show version

Parameters:
   "level-of-operation" [string - "page"]
    PAGE XML hierarchy level to operate on
    Possible values: ["page", "region", "line", "word", "glyph"]
   "dpi" [number - 0]
    pixel density in dots per inch (overrides any meta-data in the
    images); disabled when zero
   "method" [string - "stretch"]
    contrast-enhancing transformation to use
    Possible values: ["stretch", "adapthist"]
```

### [OCR-D processor](https://ocr-d.github.io/cli) interface `ocrd-skimage-denoise-raw`

To be used with [PAGE-XML](https://github.com/PRImA-Research-Lab/PAGE-XML) documents in an [OCR-D](https://ocr-d.github.io/) annotation workflow.

```
Usage: ocrd-skimage-denoise-raw [OPTIONS]

  Denoise raw images with Scikit-image

Options:
  -I, --input-file-grp USE        File group(s) used as input
  -O, --output-file-grp USE       File group(s) used as output
  -g, --page-id ID                Physical page ID(s) to process
  --overwrite                     Remove existing output pages/images
                                  (with --page-id, remove only those)
  -p, --parameter JSON-PATH       Parameters, either verbatim JSON string
                                  or JSON file path
  -m, --mets URL-PATH             URL or file path of METS to process
  -w, --working-dir PATH          Working directory of local workspace
  -l, --log-level [OFF|ERROR|WARN|INFO|DEBUG|TRACE]
                                  Log level
  -J, --dump-json                 Dump tool description as JSON and exit
  -h, --help                      This help message
  -V, --version                   Show version

Parameters:
   "level-of-operation" [string - "page"]
    PAGE XML hierarchy level to operate on
    Possible values: ["page", "region", "line", "word", "glyph"]
   "dpi" [number - 0]
    pixel density in dots per inch (overrides any meta-data in the
    images); disabled when zero
   "method" [string - "VisuShrink"]
    Wavelet filtering scheme to use
    Possible values: ["BayesShrink", "VisuShrink"]
```

### [OCR-D processor](https://ocr-d.github.io/cli) interface `ocrd-skimage-binarize`

To be used with [PAGE-XML](https://github.com/PRImA-Research-Lab/PAGE-XML) documents in an [OCR-D](https://ocr-d.github.io/) annotation workflow.

```
Usage: ocrd-skimage-binarize [OPTIONS]

  Binarize images with Scikit-image

Options:
  -I, --input-file-grp USE        File group(s) used as input
  -O, --output-file-grp USE       File group(s) used as output
  -g, --page-id ID                Physical page ID(s) to process
  --overwrite                     Remove existing output pages/images
                                  (with --page-id, remove only those)
  -p, --parameter JSON-PATH       Parameters, either verbatim JSON string
                                  or JSON file path
  -m, --mets URL-PATH             URL or file path of METS to process
  -w, --working-dir PATH          Working directory of local workspace
  -l, --log-level [OFF|ERROR|WARN|INFO|DEBUG|TRACE]
                                  Log level
  -J, --dump-json                 Dump tool description as JSON and exit
  -h, --help                      This help message
  -V, --version                   Show version

Parameters:
   "level-of-operation" [string - "page"]
    PAGE XML hierarchy level to operate on
    Possible values: ["page", "region", "line", "word", "glyph"]
   "dpi" [number - 0]
    pixel density in dots per inch (overrides any meta-data in the
    images); disabled when zero
   "method" [string - "sauvola"]
    Thresholding algorithm to use
    Possible values: ["sauvola", "niblack", "otsu", "gauss", "yen", "li"]
   "window_size" [number - 0]
    For Sauvola/Niblack/Gauss, the (odd) window size in pixels; when zero
    (default), set to DPI
   "k" [number - 0.34]
    For Sauvola/Niblack, formula parameter influencing the threshold
    bias; larger is lighter foreground
```

### [OCR-D processor](https://ocr-d.github.io/cli) interface `ocrd-skimage-denoise`

To be used with [PAGE-XML](https://github.com/PRImA-Research-Lab/PAGE-XML) documents in an [OCR-D](https://ocr-d.github.io/) annotation workflow.

```
Usage: ocrd-skimage-denoise [OPTIONS]

  Denoise binarized images with Scikit-image

Options:
  -I, --input-file-grp USE        File group(s) used as input
  -O, --output-file-grp USE       File group(s) used as output
  -g, --page-id ID                Physical page ID(s) to process
  --overwrite                     Remove existing output pages/images
                                  (with --page-id, remove only those)
  -p, --parameter JSON-PATH       Parameters, either verbatim JSON string
                                  or JSON file path
  -m, --mets URL-PATH             URL or file path of METS to process
  -w, --working-dir PATH          Working directory of local workspace
  -l, --log-level [OFF|ERROR|WARN|INFO|DEBUG|TRACE]
                                  Log level
  -J, --dump-json                 Dump tool description as JSON and exit
  -h, --help                      This help message
  -V, --version                   Show version

Parameters:
   "level-of-operation" [string - "page"]
    PAGE XML hierarchy level to operate on
    Possible values: ["page", "region", "line", "word", "glyph"]
   "dpi" [number - 0]
    pixel density in dots per inch (overrides any meta-data in the
    images); disabled when zero
   "maxsize" [number - 3]
    maximum component size of (bg holes or fg specks) noise in pt
```

## Testing

none yet

