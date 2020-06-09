import click

from ocrd.decorators import ocrd_cli_options, ocrd_cli_wrap_processor
from .shell import ShellPreprocessor
from .skimage_binarize import SkimageBinarize

@click.command()
@ocrd_cli_options
def ocrd_process_image(*args, **kwargs):
    return ocrd_cli_wrap_processor(ShellPreprocessor, *args, **kwargs)

@click.command()
@ocrd_cli_options
def ocrd_skimage_binarize(*args, **kwargs):
    return ocrd_cli_wrap_processor(SkimageBinarize, *args, **kwargs)
