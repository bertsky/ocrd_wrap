"""
Installs:
    - ocrd-process-image
    - ocrd-skimage-normalize
    - ocrd-skimage-denoise-raw
    - ocrd-skimage-binarize
    - ocrd-skimage-denoise
"""

import codecs
import json
from setuptools import setup
from setuptools import find_packages

with codecs.open('README.md', encoding='utf-8') as f:
    README = f.read()

with open('./ocrd-tool.json', 'r') as f:
    version = json.load(f)['version']
    
setup(
    name='ocrd_wrap',
    version=version,
    description='OCR-D wrapper for arbitrary coords-preserving image operations',
    long_description=README,
    long_description_content_type='text/markdown',
    author='Robert Sachunsky',
    author_email='sachunsky@informatik.uni-leipzig.de',
    url='https://github.com/bertsky/ocrd_wrap',
    license='MIT',
    packages=find_packages(),
    include_package_data=True,
    install_requires=open('requirements.txt').read().split('\n'),
    package_data={
        '': ['*.json', '*.yml', '*.yaml', '*.csv.gz', '*.jar', '*.zip'],
    },
    entry_points={
        'console_scripts': [
            'ocrd-process-image=ocrd_wrap.cli:ocrd_process_image',
            'ocrd-skimage-binarize=ocrd_wrap.cli:ocrd_skimage_binarize',
            'ocrd-skimage-denoise=ocrd_wrap.cli:ocrd_skimage_denoise',
            'ocrd-skimage-denoise-raw=ocrd_wrap.cli:ocrd_skimage_denoise_raw',
        ]
    },
)
