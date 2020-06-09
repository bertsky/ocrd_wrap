import click

from ocrd.decorators import ocrd_cli_options, ocrd_cli_wrap_processor
from .shell import ShellPreprocessor
from .skimage_binarize import SkimageBinarize
from .skimage_denoise import SkimageDenoise
from .skimage_denoise_raw import SkimageDenoiseRaw
from .skimage_normalize import SkimageNormalize

@click.command()
@ocrd_cli_options
def ocrd_preprocess_image(*args, **kwargs):
    return ocrd_cli_wrap_processor(ShellPreprocessor, *args, **kwargs)

@click.command()
@ocrd_cli_options
def ocrd_skimage_normalize(*args, **kwargs):
    return ocrd_cli_wrap_processor(SkimageNormalize, *args, **kwargs)

@click.command()
@ocrd_cli_options
def ocrd_skimage_denoise_raw(*args, **kwargs):
    return ocrd_cli_wrap_processor(SkimageDenoiseRaw, *args, **kwargs)

@click.command()
@ocrd_cli_options
def ocrd_skimage_binarize(*args, **kwargs):
    return ocrd_cli_wrap_processor(SkimageBinarize, *args, **kwargs)

@click.command()
@ocrd_cli_options
def ocrd_skimage_denoise(*args, **kwargs):
    return ocrd_cli_wrap_processor(SkimageDenoise, *args, **kwargs)
