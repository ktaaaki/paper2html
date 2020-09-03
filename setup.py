import os
from os.path import join as pjoin
import re
from setuptools import setup, find_packages


def get_version(*file_paths):
    with open(pjoin(os.path.dirname(__file__), *file_paths)) as fp:
        version_file = fp.read()
    version_match = re.search(r"^__version__ = '([^']*)'", version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")


with open("README.md", "r") as f:
    long_description = f.read()


setup(
    name='paper2html',
    description='PDF paper to html converter',
    version=get_version("paper2html", "__init__.py"),
    license='AGPL',
    classifiers=[
        'Programming Language :: Python :: 3.5',
        'License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)',
        'Operating System :: MacOS :: MacOS X',
    ],
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=[
        'pdf2image',
        'pdfminer.six >= 20200726',
        'fire',
        'pillow',
    ],
    url='https://github.com/ktaaaki/paper2html',
    author='ktaaaki',
    author_email='kaneko.sadaha@gmail.com',
)
