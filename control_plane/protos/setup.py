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


with open("README.md", "r") as fh:
    long_description = fh.read()


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
    result = subprocess.call("%s -m grpc_tools.protoc %s" % (PYTHON_PATH, args), shell=True)
    if result != 0:
        exit(-1)


packages = [
    'db_update',
    'control_plane.controller',
    'control_plane.controller.cli',
    'control_plane.examples',
    'control_plane.examples.arangodb',
    'control_plane.examples.srv6_pm',
    'control_plane.examples.srv6_tunnels',
    '.'
]

setuptools.setup(
    name="rose-srv6-control-plane-protos",
    version="0.0.1",
    author="Carmine Scarpitta",
    author_email="carmine.scarpitta@uniroma2.it",
    description="Collection of control-plane modules for a Controller",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/netgroup/rose-srv6-control-plane",
    packages=packages,
    package_dir={
        '': 'control_plane/protos/gen_py',
        'control_plane': 'control_plane',
        'db_update': 'db_update'
    },
    install_requires=install_requires,
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: Linux',
        'Programming Language :: Python',
    ],
    python_requires='>=3.6',
    cmdclass={
        'develop': PostDevelopCommand,
        'install': PostInstallCommand,
    }
)
