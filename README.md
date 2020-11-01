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

### [OCR-D processor](https://ocr-d.de/en/spec/cli) interface `ocrd-preprocess-image`

To be used with [PAGE-XML](https://github.com/PRImA-Research-Lab/PAGE-XML) documents in an [OCR-D](https://ocr-d.de/en/about) annotation workflow.

```
Usage: ocrd-preprocess-image [OPTIONS]

  Convert or enhance images

  > Performs coords-preserving image operations via runtime shell calls
  > anywhere.

  > Open and deserialize PAGE input files and their respective images,
  > then iterate over the element hierarchy down to the requested
  > ``level-of-operation`` in the element hierarchy.

  > For each segment element, retrieve a segment image according to the
  > layout annotation (from an existing AlternativeImage, or by cropping
  > via coordinates into the higher-level image, and - when applicable -
  > deskewing.

  > If ``input_feature_selector`` and/or ``input_feature_filter`` is
  > non-empty, then select/filter among the @imageFilename image and the
  > available AlternativeImages the last one which contains all of the
  > selected, but none of the filtered features (i.e. @comments
  > classes), or raise an error.

  > Then write that image into a temporary PNG file, create a new METS
  > file ID for the result image (based on the segment ID and the
  > operation to be run), along with a local path for it, and pass
  > ``command`` to the shell after replacing: - the string ``@INFILE``
  > with that input image path, and - the string ``@OUTFILE`` with that
  > output image path.

  > If the shell returns with a failure, skip that segment with an
  > approriate error message. Otherwise, add the new image to the
  > workspace along with the output fileGrp, and using a file ID with
  > suffix ``.IMG-``, and further identification of the input element.

  > Reference it as AlternativeImage in the element, adding
  > ``output_feature_added`` to its @comments.

  > Produce a new PAGE output file by serialising the resulting
  > hierarchy.

Options:
  -I, --input-file-grp USE        File group(s) used as input
  -O, --output-file-grp USE       File group(s) used as output
  -g, --page-id ID                Physical page ID(s) to process
  --overwrite                     Remove existing output pages/images
                                  (with --page-id, remove only those)
  -p, --parameter JSON-PATH       Parameters, either verbatim JSON string
                                  or JSON file path
  -P, --param-override KEY VAL    Override a single JSON object key-value pair,
                                  taking precedence over --parameter
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

#### presets

The following example recipes are included in the distribution:
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

### [OCR-D processor](https://ocr-d.de/en/spec/cli) interface `ocrd-skimage-normalize`

To be used with [PAGE-XML](https://github.com/PRImA-Research-Lab/PAGE-XML) documents in an [OCR-D](https://ocr-d.de/en/about) annotation workflow.

```
Usage: ocrd-skimage-normalize [OPTIONS]

  Equalize contrast/exposure of images with Scikit-image; stretches the color value/tone to the full dynamic range

  > Performs contrast-enhancing equalization of segment or page images
  > with scikit-image on the workspace.

  > Open and deserialize PAGE input files and their respective images,
  > then iterate over the element hierarchy down to the requested
  > ``level-of-operation`` in the element hierarchy.

  > For each segment element, retrieve a segment image according to the
  > layout annotation (from an existing AlternativeImage, or by cropping
  > via coordinates into the higher-level image, and - when applicable -
  > deskewing), in raw (non-binarized) form.

  > Next, normalize the image according to ``method`` in skimage.

  > Then write the new image to the workspace along with the output
  > fileGrp, and using a file ID with suffix ``.IMG-NRM`` with further
  > identification of the input element.

  > Produce a new PAGE output file by serialising the resulting
  > hierarchy.

Options:
  -I, --input-file-grp USE        File group(s) used as input
  -O, --output-file-grp USE       File group(s) used as output
  -g, --page-id ID                Physical page ID(s) to process
  --overwrite                     Remove existing output pages/images
                                  (with --page-id, remove only those)
  -p, --parameter JSON-PATH       Parameters, either verbatim JSON string
                                  or JSON file path
  -P, --param-override KEY VAL    Override a single JSON object key-value pair,
                                  taking precedence over --parameter
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
   "black-point" [number - 1.0]
    black point point in percent of luminance/value/tone histogram; up to
    ``black-point`` darkest pixels will be clipped to black when
    stretching
   "white-point" [number - 7.0]
    white point in percent of luminance/value/tone histogram; up to
    ``white-point`` brightest pixels will be clipped to white when
    stretching
   "method" [string - "stretch"]
    contrast-enhancing transformation to use after clipping; ``stretch``
    uses ``skimage.exposure.rescale_intensity`` (globally linearly
    stretching to full dynamic range) and ``adapthist`` uses
    ``skimage.exposure.equalize_adapthist`` (applying over tiles with
    context from 1/8th of the image's width)
    Possible values: ["stretch", "adapthist"]
```

### [OCR-D processor](https://ocr-d.de/en/spec/cli) interface `ocrd-skimage-denoise-raw`

To be used with [PAGE-XML](https://github.com/PRImA-Research-Lab/PAGE-XML) documents in an [OCR-D](https://ocr-d.de/en/about) annotation workflow.

```
Usage: ocrd-skimage-denoise-raw [OPTIONS]

  Denoise raw images with Scikit-image

  > Performs raw denoising of segment or page images with scikit-image
  > on the workspace.

  > Open and deserialize PAGE input files and their respective images,
  > then iterate over the element hierarchy down to the requested
  > ``level-of-operation`` in the element hierarchy.

  > For each segment element, retrieve a segment image according to the
  > layout annotation (from an existing AlternativeImage, or by cropping
  > via coordinates into the higher-level image, and - when applicable -
  > deskewing), in raw (non-binarized) form.

  > Next, denoise the image with a Wavelet transform scheme according to
  > ``method`` in skimage.

  > Then write the new image to the workspace along with the output
  > fileGrp, and using a file ID with suffix ``.IMG-DEN`` with further
  > identification of the input element.

  > Produce a new PAGE output file by serialising the resulting
  > hierarchy.

Options:
  -I, --input-file-grp USE        File group(s) used as input
  -O, --output-file-grp USE       File group(s) used as output
  -g, --page-id ID                Physical page ID(s) to process
  --overwrite                     Remove existing output pages/images
                                  (with --page-id, remove only those)
  -p, --parameter JSON-PATH       Parameters, either verbatim JSON string
                                  or JSON file path
  -P, --param-override KEY VAL    Override a single JSON object key-value pair,
                                  taking precedence over --parameter
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

### [OCR-D processor](https://ocr-d.de/en/spec/cli) interface `ocrd-skimage-binarize`

To be used with [PAGE-XML](https://github.com/PRImA-Research-Lab/PAGE-XML) documents in an [OCR-D](https://ocr-d.de/en/about) annotation workflow.

```
Usage: ocrd-skimage-binarize [OPTIONS]

  Binarize images with Scikit-image

  > Performs binarization of segment or page images with scikit-image on
  > the workspace.

  > Open and deserialize PAGE input files and their respective images,
  > then iterate over the element hierarchy down to the requested
  > ``level-of-operation`` in the element hierarchy.

  > For each segment element, retrieve a segment image according to the
  > layout annotation (from an existing AlternativeImage, or by cropping
  > via coordinates into the higher-level image, and - when applicable -
  > deskewing).

  > Next, binarize the image according to ``method`` with skimage.

  > Then write the new image to the workspace along with the output
  > fileGrp, and using a file ID with suffix ``.IMG-BIN`` with further
  > identification of the input element.

  > Produce a new PAGE output file by serialising the resulting
  > hierarchy.

Options:
  -I, --input-file-grp USE        File group(s) used as input
  -O, --output-file-grp USE       File group(s) used as output
  -g, --page-id ID                Physical page ID(s) to process
  --overwrite                     Remove existing output pages/images
                                  (with --page-id, remove only those)
  -p, --parameter JSON-PATH       Parameters, either verbatim JSON string
                                  or JSON file path
  -P, --param-override KEY VAL    Override a single JSON object key-value pair,
                                  taking precedence over --parameter
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

### [OCR-D processor](https://ocr-d.de/en/spec/cli) interface `ocrd-skimage-denoise`

To be used with [PAGE-XML](https://github.com/PRImA-Research-Lab/PAGE-XML) documents in an [OCR-D](https://ocr-d.de/en/about) annotation workflow.

```
Usage: ocrd-skimage-denoise [OPTIONS]

  Denoise binarized images with Scikit-image

  > Performs binary denoising of segment or page images with scikit-
  > image on the workspace.

  > Open and deserialize PAGE input files and their respective images,
  > then iterate over the element hierarchy down to the requested
  > ``level-of-operation`` in the element hierarchy.

  > For each segment element, retrieve a segment image according to the
  > layout annotation (from an existing AlternativeImage, or by cropping
  > via coordinates into the higher-level image, and - when applicable -
  > deskewing), in binarized form.

  > Next, denoise the image by removing too small connected components
  > with skimage.

  > Then write the new image to the workspace along with the output
  > fileGrp, and using a file ID with suffix ``.IMG-DEN`` with further
  > identification of the input element.

  > Produce a new PAGE output file by serialising the resulting
  > hierarchy.

Options:
  -I, --input-file-grp USE        File group(s) used as input
  -O, --output-file-grp USE       File group(s) used as output
  -g, --page-id ID                Physical page ID(s) to process
  --overwrite                     Remove existing output pages/images
                                  (with --page-id, remove only those)
  -p, --parameter JSON-PATH       Parameters, either verbatim JSON string
                                  or JSON file path
  -P, --param-override KEY VAL    Override a single JSON object key-value pair,
                                  taking precedence over --parameter
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

