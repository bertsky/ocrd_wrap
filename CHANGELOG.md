# Change Log

Versioned according to [Semantic Versioning](http://semver.org/).

## Unreleased

## [0.1.7] - 2021-03-07

Changed:

* `skimage-denoise`: change option `protect` from bool to pt

## [0.1.6] - 2021-03-05

Changed:

* `skimage-denoise`: option `protect` to keep small blobs near large ones
* `skimage-denoise`: interpret `maxsize` in pt instead of square pt again

## [0.1.5] - 2021-03-02

Fixed:

* `skimage-denoise`: be robust against wrong color depth in hdr

## [0.1.4] - 2020-11-03

Fixed:

 * `skimage-normlize`: fix typo in 0.1.3

## [0.1.3] - 2020-11-01

Fixed:

 * all: add pageId for sub-page-level derived images, too

## [0.1.2] - 2020-10-13

Changed:

 * `skimage-normalize`: expose black/white-point parameters

## [0.1.1] - 2020-09-24

Fixed:

 * set pcGtsId to METS file ID everwhere
 * logging according to OCR-D/core#599

## [0.1.0] - 2020-08-14

Changed:

 * put derived images under output fileGrp, using file ID suffixes

## [0.0.5] - 2020-07-08

Fixed:

 * update requirements (needs newer `ocrd, skimage, pillow`)
 * all: fix typo in `level-of-operation=region`
 * `ocrd-skimage-denoise-raw`: skip images with too little noise
 * `ocrd-skimage-*`: preserve color depth in image format

## [0.0.4] - 2020-06-10

Changed:

  * `ocrd-preprocess-image`: check constant image size

Added:

  * First set of example parameter files for ocrd-preprocess-image


## [0.0.3] - 2020-06-10

Changed:

  * Renamed `ocrd-process-image` to `ocrd-preprocess-image`
  
Added:

  * `ocrd-skimage-normalize` (wraps SciKit-Image `exposure` funcs)
  * `ocrd-skimage-denoise-raw` (wraps SciKit-Image `denoise_wavelet`)
  * `ocrd-skimage-denoise` (wraps SciKit-Image `remove_small_holes/objects`)

## [0.0.2] - 2020-06-09

Added:

  * `ocrd-skimage-binarize` (wraps SciKit-Image thresholding)

## [0.0.1] - 2020-06-08

Added:

  * `ocrd-process-image` (generic shell-wrapped image preprocessor)

<!-- link-labels -->
[0.1.7]: ../../compare/v0.1.6...v0.1.7
[0.1.6]: ../../compare/v0.1.5...v0.1.6
[0.1.5]: ../../compare/v0.1.4...v0.1.5
[0.1.4]: ../../compare/v0.1.3...v0.1.4
[0.1.3]: ../../compare/v0.1.2...v0.1.3
[0.1.2]: ../../compare/v0.1.1...v0.1.2
[0.1.1]: ../../compare/v0.1.0...v0.1.1
[0.1.0]: ../../compare/v0.0.5...v0.1.0
[0.0.5]: ../../compare/v0.0.4...v0.0.5
[0.0.4]: ../../compare/v0.0.3...v0.0.4
[0.0.3]: ../../compare/v0.0.2...v0.0.3
[0.0.2]: ../../compare/v0.0.1...v0.0.2
[0.0.1]: ../../compare/HEAD...v0.0.1
