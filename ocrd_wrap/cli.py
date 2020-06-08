import click

from ocrd.decorators import ocrd_cli_options, ocrd_cli_wrap_processor
from .shell import ShellPreprocessor

@click.command()
@ocrd_cli_options
def ocrd_process_image(*args, **kwargs):
    return ocrd_cli_wrap_processor(ShellPreprocessor, *args, **kwargs)
