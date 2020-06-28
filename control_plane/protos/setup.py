#!/usr/bin/python


import os
import setuptools
import setuptools.command.install
import setuptools.command.develop


with open("README.md", "r") as fh:
    long_description = fh.read()


# Read dependencies from requirements.txt
proj_dir = os.path.dirname(os.path.realpath(__file__))
requirements_path = os.path.join(proj_dir, 'requirements.txt')
install_requires = []
if os.path.isfile(requirements_path):
    with open(requirements_path) as f:
        install_requires = f.read().splitlines()


class BuildPackageProtos(setuptools.Command):
    """Command to generate project *_pb2.py modules from proto files."""

    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        # Build protos with strict mode enabled
        # (i.e. exit with non-zero value if the proto compiling fails)
        from grpc.tools import command
        command.build_package_protos(self.distribution.package_dir[''], True)


class install(setuptools.command.install.install):

    def run(self):
        setuptools.command.install.install.run(self)
        # Build protos with strict mode enabled
        # (i.e. exit with non-zero value if the proto compiling fails)
        from grpc.tools import command
        command.build_package_protos('', True)


class develop(setuptools.command.develop.develop):

    def run(self):
        setuptools.command.develop.develop.run(self)
        # Build protos with strict mode enabled
        # (i.e. exit with non-zero value if the proto compiling fails)
        from grpc.tools import command
        command.build_package_protos('', True)


packages = [
    '',
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
        '': '.',
    },
    install_requires=install_requires,
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: Linux',
        'Programming Language :: Python',
    ],
    cmdclass={
        'build_proto_modules': BuildPackageProtos,
        'install': install,
    },
    python_requires='>=3.6',
)
