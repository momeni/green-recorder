#!/usr/bin/env python
import os
from setuptools import find_packages, setup
from subprocess import call
from glob import glob
from os.path import splitext, split
import re

_version_re = re.compile(r"__version__\s=\s'(.*)'")

data_files = [("share/green-recorder", ["ui/ui.glade"]),
              ("share/pixmaps", ["data/green-recorder.png"]),
              ("share/applications", ["data/green-recorder.desktop"])]

po_files = glob("po/*.po")
for po_file in po_files:
    lang = splitext(split(po_file)[1])[0]
    mo_path = "locale/{}/LC_MESSAGES/green-recorder.mo".format(lang)
    call("mkdir -p locale/{}/LC_MESSAGES/".format(lang), shell=True)
    call("msgfmt {} -o {}".format(po_file, mo_path), shell=True)
locales = map(lambda i: ('share/' + i, [i + '/green-recorder.mo', ]), glob('locale/*/LC_MESSAGES'))

data_files.extend(locales)

install_requires = [
    'pydbus',
    'PyGObject',
    'appdirs',
    # long story short, "configparser" Python 2 backport RPM package is no good because it strips init py
    # 'configparser>=3.7.1',
]
tests_requires = ["pytest>=4.4.0", "flake8", "pytest-xdist"]

with open("README.md", "r") as fh:
    long_description = fh.read()

base_dir = os.path.dirname(__file__)

with open(os.path.join(base_dir, "recorder", "__about__.py"), 'r') as f:
    version = _version_re.search(f.read()).group(1)

setup(
    name="green-recorder",
    version=version,
    author="M.Hanny Sabbagh, Danila Vershinin",
    author_email="mhsabbagh@outlook.com, info@getpagespeed.com",
    url="https://github.com/dvershinin/green-recorder",
    description="Record your desktop easily using a simple GUI",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(exclude=["tests"]),
    zip_safe=False,
    license="GPLv3",
    install_requires=install_requires,
    extras_require={
        "tests": install_requires + tests_requires,
    },
    tests_require=tests_requires,
    include_package_data=True,
    entry_points={"gui_scripts": ["green-recorder = recorder:main"]},
    data_files=data_files,
    classifiers=[
        "Intended Audience :: End Users/Desktop",
        "Topic :: Multimedia :: Video :: Capture",
    ],
)
