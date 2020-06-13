#!/usr/bin/python


import os
import sys
import subprocess
import setuptools
from pathlib import Path
import shutil
from setuptools.command.develop import develop
from setuptools.command.install import install
from setuptools.command.egg_info import egg_info
from setuptools.command.sdist import sdist
from setuptools.command.build_py import build_py


with open("README.md", "r") as fh:
    long_description = fh.read()


# Read dependencies from requirements.txt
proj_dir = os.path.dirname(os.path.realpath(__file__))
requirements_path = os.path.join(proj_dir, 'requirements.txt')
install_requires = []
if os.path.isfile(requirements_path):
    with open(requirements_path) as f:
        install_requires = f.read().splitlines()


def build_protos():
    subprocess.call(['pip', 'install', 'grpcio-tools'])

    PYTHON_PATH = sys.executable

    dirpath = Path('./gen_py')
    if dirpath.exists() and dirpath.is_dir():
        shutil.rmtree(dirpath)

    os.makedirs('./gen_py')

    open('./gen_py/__init__.py', 'a').close()

    # Generate python grpc stubs from proto files
    print('Generation of python gRPC stubs')
    args = "-I. --proto_path=. --python_out=./gen_py --grpc_python_out=./gen_py ./*.proto"
    result = subprocess.call(
        "%s -m grpc_tools.protoc %s" %
        (PYTHON_PATH, args), shell=True)
    if result != 0:
        exit(-1)


# Compile the proto files before running the setup
build_protos()


packages = [
    '.',
]

setuptools.setup(
    name="rose-srv6-control-plane-protos",
    version="0.0.1",
    author="Carmine Scarpitta",
    author_email="carmine.scarpitta@uniroma2.it",
    description="Proto files collection for control-plane modules",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/netgroup/rose-srv6-control-plane",
    packages=packages,
    package_dir={
        '': 'gen_py',
    },
    install_requires=install_requires,
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: Linux',
        'Programming Language :: Python',
    ],
    python_requires='>=3.6',
)
