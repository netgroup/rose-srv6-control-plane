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
# Implementation of SRv6-PM Manager for the Northbound gRPC client
#
# @author Carmine Scarpitta <carmine.scarpitta@uniroma2.it>
#


"""
This module provides an implementation of a SRv6-PM Manager for the Northbound
gRPC client.
"""

# Controller dependencies
import nb_commons_pb2
import srv6pm_manager_pb2
import srv6pm_manager_pb2_grpc


def set_configuration(controller_channel, sender, reflector,
                      sender_port, reflector_port, send_udp_port,
                      refl_udp_port, interval_duration, delay_margin,
                      number_of_color, pm_driver, in_interfaces=None,
                      out_interfaces=None):
    """
    Configure a node.
    """
    # pylint: disable=too-many-arguments
    #
    # Create request message
    request = srv6pm_manager_pb2.SRv6PMConfigurationRequest()
    # Set the gRPC IP address of the sender node
    request.sender.address = sender
    # Set the gRPC port number of the sender node
    request.sender.port = sender_port
    # Set the gRPC IP address of the reflector node
    request.reflector.address = reflector
    # Set the gRPC port number of the reflector node
    request.reflector.port = reflector_port
    # Set the UDP port used by the sender
    request.send_udp_port = send_udp_port
    # Set the UDP port used by the reflector
    request.refl_udp_port = refl_udp_port
    # Set the interval duration
    request.color_options.interval_duration = interval_duration
    # Set the delay margin
    request.color_options.delay_margin = delay_margin
    # Set the number of color
    request.color_options.numbers_of_color = number_of_color
    # Set the driver to be used for Performance Monitoring
    request.pm_driver = srv6pm_manager_pb2.Value(pm_driver)
    # Set the ingress interface to monitor
    if in_interfaces is not None:
        request.in_interfaces.extend(in_interfaces)
    # Set the egress interface to monitor
    if out_interfaces is not None:
        request.out_interfaces.extend(out_interfaces)
    #
    # Get the reference of the stub
    stub = srv6pm_manager_pb2_grpc.SRv6PMManagerStub(controller_channel)
    # Send the request to the gRPC server
    response = stub.SetConfiguration(request)
    # Check the status code
    if response.status != nb_commons_pb2.STATUS_SUCCESS:
        return False       # TODO raise an exception?
    # Done, success
    return True


def reset_configuration(controller_channel, sender, reflector,
                        sender_port, reflector_port):
    """
    Clear node configuration.
    """
    # Create request message
    request = srv6pm_manager_pb2.SRv6PMConfigurationRequest()
    # Set the gRPC IP address of the sender node
    request.sender.address = sender
    # Set the gRPC port number of the sender node
    request.sender.port = sender_port
    # Set the gRPC IP address of the reflector node
    request.reflector.address = reflector
    # Set the gRPC port number of the reflector node
    request.reflector.port = reflector_port
    #
    # Get the reference of the stub
    stub = srv6pm_manager_pb2_grpc.SRv6PMManagerStub(controller_channel)
    # Send the request to the gRPC server
    response = stub.ResetConfiguration(request)
    # Check the status code
    if response.status != nb_commons_pb2.STATUS_SUCCESS:
        return False       # TODO raise an exception?
    # Done, success
    return True


def start_experiment(controller_channel, sender, reflector,
                     sender_port, reflector_port, send_refl_dest,
                     refl_send_dest, send_refl_sidlist, refl_send_sidlist,
                     measurement_protocol, measurement_type,
                     authentication_mode, authentication_key,
                     timestamp_format, delay_measurement_mode,
                     padding_mbz, loss_measurement_mode, measure_id=None,
                     send_refl_localseg=None, refl_send_localseg=None,
                     force=False):
    """
    Start an experiment.
    """
    # pylint: disable=too-many-arguments, too-many-locals
    #
    # Create request message
    request = srv6pm_manager_pb2.SRv6PMExperimentRequest()
    # Set the gRPC address of the sender
    request.sender.address = sender
    # Set the gRPC port number of the sender
    request.sender.port = sender_port
    # Set the gRPC address of the reflector
    request.reflector.address = reflector
    # Set the gRPC port number of the reflector
    request.reflector.address = reflector_port
    # Set the destination for the sender to reflector path
    request.send_refl_dest = send_refl_dest
    # Set the destination for the reflector to sender path
    request.refl_send_dest = refl_send_dest
    # Set the SID list for the sender to reflector path
    request.send_refl_sidlist.extend(send_refl_sidlist)
    # Set the SID list for the reflector to sender path
    request.refl_send_sidlist.extend(refl_send_sidlist)
    # Set the measurement protocol
    request.measurement_protocol = \
        srv6pm_manager_pb2.Value(measurement_protocol)
    # Set the measurement  type
    request.measurement_type = srv6pm_manager_pb2.Value(measurement_type)
    # Set the authentication mode
    request.authentication_mode = srv6pm_manager_pb2.Value(authentication_mode)
    # Set the authentication key
    request.authentication_key = authentication_key
    # Set the timestamp format
    request.timestamp_format = srv6pm_manager_pb2.Value(timestamp_format)
    # Set the delay measurement mode
    request.delay_measurement_mode = \
        srv6pm_manager_pb2.Value(delay_measurement_mode)
    # Set the padding
    request.padding_mbz = padding_mbz
    # Set the loss measurement mode
    request.loss_measurement_mode = \
        srv6pm_manager_pb2.Value(loss_measurement_mode)
    # Set the measure ID
    request.measure_id = measure_id
    # Set the local segment for the left to right path
    request.send_refl_localseg = send_refl_localseg
    # Set the local segment for the right to left path
    request.refl_send_localseg = refl_send_localseg
    # Set the force flag
    request.force = force
    #
    # Get the reference of the stub
    stub = srv6pm_manager_pb2_grpc.SRv6PMManagerStub(controller_channel)
    # Send the request to the gRPC server
    response = stub.StartExperiment(request)
    # Check the status code
    if response.status != nb_commons_pb2.STATUS_SUCCESS:
        return False       # TODO raise an exception?
    # Done, success
    return True


def get_experiment_results(controller_channel, sender, reflector,
                           sender_port, reflector_port,
                           send_refl_sidlist, refl_send_sidlist):
    """
    Get the results of a running experiment.
    """
    # pylint: disable=too-many-arguments
    #
    # Create request message
    request = srv6pm_manager_pb2.SRv6PMExperimentRequest()
    # Set the gRPC address of the sender
    request.sender.address = sender
    # Set the gRPC port number of the sender
    request.sender.port = sender_port
    # Set the gRPC address of the reflector
    request.reflector.address = reflector
    # Set the gRPC port number of the reflector
    request.reflector.address = reflector_port
    # Set the SID list for the sender to reflector path
    request.send_refl_sidlist.extend(send_refl_sidlist)
    # Set the SID list for the reflector to sender path
    request.refl_send_sidlist.extend(refl_send_sidlist)
    #
    # Get the reference of the stub
    stub = srv6pm_manager_pb2_grpc.SRv6PMManagerStub(controller_channel)
    # Send the request to the gRPC server
    response = stub.GetExperimentResults(request)
    # Check the status code
    if response.status != nb_commons_pb2.STATUS_SUCCESS:
        return False       # TODO raise an exception?
    # Done, success
    return True


def stop_experiment(controller_channel, sender, reflector,
                    sender_port, reflector_port, send_refl_dest,
                    refl_send_dest, send_refl_sidlist, refl_send_sidlist,
                    send_refl_localseg=None, refl_send_localseg=None):
    """
    Stop a running experiment.
    """
    # pylint: disable=too-many-arguments
    #
    # Create request message
    request = srv6pm_manager_pb2.SRv6PMExperimentRequest()
    # Set the gRPC address of the sender
    request.sender.address = sender
    # Set the gRPC port number of the sender
    request.sender.port = sender_port
    # Set the gRPC address of the reflector
    request.reflector.address = reflector
    # Set the gRPC port number of the reflector
    request.reflector.address = reflector_port
    # Set the destination for the sender to reflector path
    request.send_refl_dest = send_refl_dest
    # Set the destination for the reflector to sender path
    request.refl_send_dest = refl_send_dest
    # Set the SID list for the sender to reflector path
    request.send_refl_sidlist.extend(send_refl_sidlist)
    # Set the SID list for the reflector to sender path
    request.refl_send_sidlist.extend(refl_send_sidlist)
    # Set the local segment for the left to right path
    request.send_refl_localseg = send_refl_localseg
    # Set the local segment for the right to left path
    request.refl_send_localseg = refl_send_localseg
    #
    # Get the reference of the stub
    stub = srv6pm_manager_pb2_grpc.SRv6PMManagerStub(controller_channel)
    # Send the request to the gRPC server
    response = stub.StopExperiment(request)
    # Check the status code
    if response.status != nb_commons_pb2.STATUS_SUCCESS:
        return False       # TODO raise an exception?
    # Done, success
    return True
