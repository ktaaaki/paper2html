import os
from os.path import join as pjoin
import re
from setuptools import setup, find_packages


def get_version(*file_paths):
    with open(pjoin(os.path.dirname(__file__), *file_paths), encoding="utf-8_sig") as fp:
        version_file = fp.read()
    version_match = re.search(r"^__version__ = '([^']*)'", version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")


with open("README.md", "r", encoding="utf-8_sig") as f:
    long_description = f.read()


setup(
    name='paper2html',
    description='PDF paper to html converter',
    version=get_version("paper2html", "__init__.py"),
    license='AGPL',
    classifiers=[
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)',
        'Operating System :: Microsoft :: Windows :: Windows 10',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: POSIX :: Linux',
    ],
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    package_data={"paper2html": ["templates/*.html", "templates/*.css", "templates/*.js"]},
    install_requires=[
        'pdf2image',
        'pdfminer.six >= 20200726',
        'fire',
        'pillow',
        'Flask',
    ],
    url='https://github.com/ktaaaki/paper2html',
    author='ktaaaki',
    author_email='kaneko.sadaha@gmail.com',
)
