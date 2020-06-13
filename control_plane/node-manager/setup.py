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


packages = [
    'node_manager'
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
    entry_points={
        'console_scripts': ['node_manager = node_manager.node_mgr:__main']},
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6')
