#!/usr/bin/python

##########################################################################
# Copyright (C) 2020 Carmine Scarpitta
# (Consortium GARR and University of Rome "Tor Vergata")
# www.garr.it - www.uniroma2.it/netgroup
#
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Utilities functions used by Controller CLI
#
# @author Carmine Scarpitta <carmine.scarpitta@uniroma2.it>
#


"""Utilities functions used by Controller CLI"""

# General imports
import glob as gb
import os.path as op
import readline

# Set the delimiters for the auto-completion
readline.set_completer_delims(' \t\n')


def complete_path(path):
    """Take a partial 'path' as argument and return a
    list of path names that match the 'path'"""

    if op.isdir(path):
        return gb.glob(op.join(path, '*'))
    return gb.glob(path + '*')
