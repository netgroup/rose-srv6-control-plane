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


class CleanCommand(Command):
    """Custom clean command to tidy up the project root."""
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        os.system('rm -vrf ./build ./dist ./*.pyc ./*.tgz ./*.egg-info')
        os.system('rm -vrf ./db_update/build ./db_update/dist ./db_update/*.pyc ./db_update/*.tgz ./db_update/*.egg-info')
        os.system('rm -vrf ./control_plane/controller/build ./control_plane/controller/dist ./control_plane/controller/*.pyc ./control_plane/controller/*.tgz ./control_plane/controller/*.egg-info')
        os.system('rm -vrf ./control_plane/controller/cli/build ./control_plane/controller/cli/dist ./control_plane/controller/cli/*.pyc ./control_plane/controller/cli/*.tgz ./control_plane/controller/cli/*.egg-info')
        os.system('rm -vrf ./control_plane/examples/build ./control_plane/examples/dist ./control_plane/examples/*.pyc ./control_plane/examples/*.tgz ./control_plane/examples/*.egg-info')
        os.system('rm -vrf ./control_plane/examples/arangodb/build ./control_plane/examples/arangodb/dist ./control_plane/examples/arangodb/*.pyc ./control_plane/examples/arangodb/*.tgz ./control_plane/examples/arangodb/*.egg-info')
        os.system('rm -vrf ./control_plane/examples/srv6_pm/build ./control_plane/examples/srv6_pm/dist ./control_plane/examples/srv6_pm/*.pyc ./control_plane/examples/srv6_pm/*.tgz ./control_plane/examples/srv6_pm/*.egg-info')
        os.system('rm -vrf ./control_plane/examples/srv6_tunnels/build ./control_plane/examples/srv6_tunnels/dist ./control_plane/examples/srv6_tunnels/*.pyc ./control_plane/examples/srv6_tunnels/*.tgz ./control_plane/examples/srv6_tunnels/*.egg-info')
        os.system('rm -vrf ./control_plane/protos/gen-py/build ./control_plane/protos/gen-py/dist ./control_plane/protos/gen-py/*.pyc ./control_plane/protos/gen-py/*.tgz ./control_plane/protos/gen-py/*.egg-info')


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
requirements_path = os.path.join(proj_dir, 'control_plane/controller/requirements.txt')
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
    name="rose-srv6-control-plane",
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
    entry_points={'console_scripts': ['controller = control_plane.controller.controller:__main']},
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
        'clean': CleanCommand,
    }
)
