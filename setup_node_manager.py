#!/usr/bin/python


import os
import sys
import subprocess
import setuptools
from pathlib import Path
import shutil
from setuptools import Command
from setuptools.command.develop import develop
from setuptools.command.install import install
import pip
pip.main(['install', 'foo', 'bar'])    # call pip to install them


with open("README.md", "r") as fh:
    long_description = fh.read()


class CleanCommand(Command):
    """Custom clean command to tidy up the project root."""
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        os.system('rm -vrf ./build ./dist ./*.pyc ./*.tgz ./*.egg-info')


class PostDevelopCommand(develop):
    """Post-installation for development mode."""
    def run(self):
        develop.run(self)
        build_protos()


class PostInstallCommand(install):
    """Post-installation for installation mode."""

    def run(self):
        install.run(self)
        build_protos()


proj_dir = os.path.dirname(os.path.realpath(__file__))
requirements_path = os.path.join(proj_dir, 'control_plane/node-manager/requirements.txt')
install_requires = []
if os.path.isfile(requirements_path):
    with open(requirements_path) as f:
        install_requires = f.read().splitlines()


def build_protos():
    subprocess.call(['pip', 'install', 'grpcio-tools'])
    
    PYTHON_PATH = sys.executable

    dirpath = Path('./control_plane/protos/gen_py')
    if dirpath.exists() and dirpath.is_dir():
        shutil.rmtree(dirpath)

    os.makedirs('./control_plane/protos/gen_py')

    open('./control_plane/protos/gen_py/__init__.py', 'a').close()

    # Generate python grpc stubs from proto files
    print('Generation of python gRPC stubs')
    args = "-I./control_plane/protos --proto_path=./control_plane/protos --python_out=./control_plane/protos/gen_py --grpc_python_out=./control_plane/protos/gen_py ./control_plane/protos/*.proto"
    result = subprocess.call("%s -m grpc_tools.protoc %s" % (PYTHON_PATH, args), shell=True)
    if result != 0:
        exit(-1)


packages = [
    'control_plane.node_manager',
    '.'
]

setuptools.setup(
    name="rose-srv6-control-plane",
    version="0.0.1",
    author="Carmine Scarpitta",
    author_email="carmine.scarpitta@uniroma2.it",
    description="Collection of control-plane modules for a Node Manager",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/netgroup/rose-srv6-control-plane",
    packages=packages,
    package_dir={
        '': 'control_plane/protos/gen_py',
        'control_plane': 'control_plane'
    },
    install_requires=install_requires,
    entry_points={'console_scripts': ['node_manager = control_plane.node_manager.node_manager:__main']},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    cmdclass={
        'develop': PostDevelopCommand,
        'install': PostInstallCommand,
        'clean': CleanCommand,
    }
)
