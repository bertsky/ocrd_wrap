# Change Log

Versioned according to [Semantic Versioning](http://semver.org/).

## Unreleased

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
