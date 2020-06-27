# Building documentation

This folder contains the project documentation source.

We currently use Sphinx for generating the API and reference documentation for rose-srv6-control-plane.

Pre-build docs for the latest release are available at

http://netgroup.github.io/rose-srv6-control-plane


## Instructions

To build the documentation, first you need to install rose-srv6-control-plane.
Then, ``cd`` to the ``docs`` folder and install the Python packages required to build the documentation by entering:

```console
$ pip install -r requirements.txt
```

To build the HTML documentation, ``cd`` to the ``docs`` folder and type:

```console
$ make html
```

Sphinx will generate a build/html subdirectory containing the built documentation.

To build the PDF documentation you need to install Latex, then ``cd`` to the ``docs`` folder and enter this command:

```console
$ make latexpdf
```
