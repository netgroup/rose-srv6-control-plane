#!/usr/bin/python

import os
import pytest
from ipaddress import IPv6Address

from controller import srv6_utils

NODES_YAML = os.path.join(os.path.dirname(__file__), 'nodes.yml')
NODES_INVALID_1_YAML = os.path.join(
    os.path.dirname(__file__),
    'nodes_invalid_1.yml')


def normalize_ip_addrs(ip_addrs):
    return [str(IPv6Address(addr)) for addr in ip_addrs]


def normalize_ip_addr(ip_addr):
    return str(IPv6Address(ip_addr))


def compare_ip_addrs(addr1, addr2):
    return normalize_ip_addrs(addr1) == normalize_ip_addrs(addr2)


def test_nodes_to_addrs():
    nodes = ['R1', 'R2', 'R3']
    addrs_list = ['fcbb:bb00:0001::',
                  'fcbb:bb00:0002::',
                  'fcbb:bb00:0003::']
    nodes_info = srv6_utils.read_nodes(NODES_YAML)[0]
    assert normalize_ip_addrs([node['uN'] for node in nodes_info.values()
                               if node['name'] in nodes]) \
        == normalize_ip_addrs(addrs_list), 'Test failed'


def test_segments_to_micro_segment_1():
    # First test (#SIDs < 6)
    locator = 'fcbb:bb00::'
    sid_list = [
        'fcbb:bb00:0001::',
        'FCBB:BB00:0002::',
        'FCBB:BB00:0003::',
    ]
    usid = 'fcbb:bb00:0001:0002:0003::'
    assert normalize_ip_addr(srv6_utils.segments_to_micro_segment(
        locator, sid_list)) == normalize_ip_addr(usid)


def test_segments_to_micro_segment_2():
    # Second test (#SIDs = 6)
    locator = 'fcbb:bb00::'
    sid_list = [
        'fcbb:bb00:0001::',
        'FCBB:BB00:0002::',
        'FCBB:BB00:0003::',
        'FCBB:BB00:0004::',
        'FCBB:BB00:0005::',
        'FCBB:BB00:0006::',
    ]
    usid = 'fcbb:bb00:0001:0002:0003:0004:0005:0006'
    assert normalize_ip_addr(srv6_utils.segments_to_micro_segment(
        locator, sid_list)) == normalize_ip_addr(usid)


def test_segments_to_micro_segment_3():
    # Third test (#SIDs > 6)
    locator = 'fcbb:bb00::'
    sid_list = [
        'fcbb:bb00:0001::',
        'FCBB:BB00:0002::',
        'FCBB:BB00:0003::',
        'FCBB:BB00:0004::',
        'FCBB:BB00:0005::',
        'FCBB:BB00:0006::',
        'FCBB:BB00:0007::',
        'FCBB:BB00:0008::',
    ]
    with pytest.raises(srv6_utils.TooManySegmentsError):
        srv6_utils.segments_to_micro_segment(
            normalize_ip_addr(locator), normalize_ip_addrs(sid_list))


def test_get_sid_locator():
    locator = 'fcbb:bb00::'
    sid_list = [
        'fcbb:bb00:0001::',
        'FCBB:BB00:0002::',
        'FCBB:BB00:0003::',
        'FCBB:BB00:0004::',
        'FCBB:BB00:0005::',
        'FCBB:BB00:0006::',
        'FCBB:BB00:0007::',
        'FCBB:BB00:0008::',
    ]
    assert normalize_ip_addr(srv6_utils.get_sid_locator(sid_list)) == \
        normalize_ip_addr(locator)


def test_sidlist_to_usidlist_1():
    # First test (#SIDs < 6)
    sid_list = [
        'fcbb:bb00:0001::',
        'FCBB:BB00:0002::',
        'FCBB:BB00:0003::',
    ]
    usid_list = ['fcbb:bb00:0001:0002:0003::']
    assert normalize_ip_addrs(srv6_utils.sidlist_to_usidlist(sid_list)) == \
        normalize_ip_addrs(usid_list)


def test_sidlist_to_usidlist_2():
    # Second test (#SIDs = 6)
    sid_list = [
        'fcbb:bb00:0001::',
        'FCBB:BB00:0002::',
        'FCBB:BB00:0003::',
        'FCBB:BB00:0004::',
        'FCBB:BB00:0005::',
        'FCBB:BB00:0006::',
    ]
    usid_list = ['fcbb:bb00:0001:0002:0003:0004:0005::', 'fcbb:bb00:0006::']
    assert normalize_ip_addrs(srv6_utils.sidlist_to_usidlist(sid_list)) == \
        normalize_ip_addrs(usid_list)


def test_sidlist_to_usidlist_3():
    # Third test (#SIDs > 6)
    sid_list = [
        'fcbb:bb00:0001::',
        'FCBB:BB00:0002::',
        'FCBB:BB00:0003::',
        'FCBB:BB00:0004::',
        'FCBB:BB00:0005::',
        'FCBB:BB00:0006::',
        'FCBB:BB00:0007::',
        'FCBB:BB00:0008::',
    ]
    usid_list = [
        'fcbb:bb00:0001:0002:0003:0004:0005::',
        'fcbb:bb00:0006:0007:0008::',
    ]
    assert normalize_ip_addrs(srv6_utils.sidlist_to_usidlist(sid_list)) == \
        normalize_ip_addrs(usid_list)


def test_nodes_to_micro_segments():
    nodes = ['R1', 'R2', 'R3', 'R4', 'R5', 'R6', 'R8']
    usid_list = [
        'fcbb:bb00:0001:0002:0003:0004:0005::',
        'fcbb:bb00:0006:0008::',
    ]
    assert normalize_ip_addrs(srv6_utils.nodes_to_micro_segments(
        nodes, NODES_YAML)) == normalize_ip_addrs(usid_list)


def test_nodes_to_micro_segments_invalid_1():
    nodes = ['R1', 'R2', 'R3', 'R4', 'R5', 'R6', 'R8']
    with pytest.raises(srv6_utils.InvalidConfigurationError):
        srv6_utils.nodes_to_micro_segments(
            nodes, NODES_INVALID_1_YAML)


def test_nodes_to_micro_segments_invalid_2():
    nodes = ['R1', 'R2', 'R3', 'R4', 'R5', 'R6', 'R8', 'R9']
    with pytest.raises(srv6_utils.NodeNotFoundError):
        srv6_utils.nodes_to_micro_segments(
            nodes, NODES_YAML)
