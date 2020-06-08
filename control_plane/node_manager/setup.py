#!/usr/bin/python


import os
import setuptools


with open("README.md", "r") as fh:
    long_description = fh.read()


proj_dir = os.path.dirname(os.path.realpath(__file__))
requirements_path = os.path.join(proj_dir, 'requirements.txt')
install_requires = []
if os.path.isfile(requirements_path):
    with open(requirements_path) as f:
        install_requires = f.read().splitlines()


dependency_links = [
    'https://github.com/netgroup/rose-srv6-control-plane#subdirectory=control_plane/protos',
    'https://github.com/netgroup/rose-srv6-data-plane'
]


packages = [
    ''
]

setuptools.setup(
    name="rose-srv6-control-plane-node-manager",
    version="0.0.1",
    author="Carmine Scarpitta",
    author_email="carmine.scarpitta@uniroma2.it",
    description="Collection of control-plane modules for a Node Manager",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/netgroup/rose-srv6-control-plane",
    packages=packages,
    install_requires=install_requires,
    dependency_links=dependency_links,
    entry_points={'console_scripts': ['node_manager = control_plane.node_manager.node_manager:__main']},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6'
)
