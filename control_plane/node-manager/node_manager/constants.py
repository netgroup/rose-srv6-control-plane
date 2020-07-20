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
# File containing several constants used in different scripts
#
# @author Carmine Scarpitta <carmine.scarpitta@uniroma2.it>
#


'''
This file contains several constants used in different scripts
'''

# Proto dependencies
from srv6_manager_pb2 import FwdEngine


# Forwarding Engine
FWD_ENGINE = {
    'VPP': FwdEngine.Value('VPP'),
    'Linux': FwdEngine.Value('Linux'),
    'P4': FwdEngine.Value('P4'),
}  # pylint: disable=no-member
