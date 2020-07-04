#!/usr/bin/python

import pytest

from controller import srv6_utils


def test_nodes_to_addrs():
    nodes = ['R1', 'R2', 'R3']
    addrs_list = ['fcbb:bb00:0001::',
                  'fcbb:bb00:0002::',
                  'fcbb:bb00:0003::']
    assert srv6_utils.nodes_to_addrs(
        nodes, 'nodes.yml') == addrs_list, 'Test failed'


def test_segments_to_micro_segment_1():
    # First test (#SIDs < 6)
    locator = 'fcbb:bb00'
    sid_list = [
        'fcbb:bb00:0001::',
        'FCBB:BB00:0002::',
        'FCBB:BB00:0003::',
    ]
    usid = 'fcbb:bb00:0001:0002:0003::'
    assert srv6_utils.segments_to_micro_segment(
        locator, sid_list) == usid


def test_segments_to_micro_segment_2():
    # Second test (#SIDs = 6)
    locator = 'fcbb:bb00'
    sid_list = [
        'fcbb:bb00:0001::',
        'FCBB:BB00:0002::',
        'FCBB:BB00:0003::',
        'FCBB:BB00:0004::',
        'FCBB:BB00:0005::',
        'FCBB:BB00:0006::',
    ]
    usid = 'fcbb:bb00:0001:0002:0003:0004:0005:0006'
    assert srv6_utils.segments_to_micro_segment(
        locator, sid_list) == usid


def test_segments_to_micro_segment_3():
    # Third test (#SIDs > 6)
    locator = 'fcbb:bb00'
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
            locator, sid_list)


def test_get_sid_locator():
    locator = 'fcbb:bb00'
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
    assert srv6_utils.get_sid_locator(sid_list) == locator


def test_sidlist_to_usidlist_1():
    # First test (#SIDs < 6)
    sid_list = [
        'fcbb:bb00:0001::',
        'FCBB:BB00:0002::',
        'FCBB:BB00:0003::',
    ]
    usid_list = ['fcbb:bb00:0001:0002:0003::']
    assert srv6_utils.sidlist_to_usidlist(sid_list) == usid_list


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
    usid_list = ['fcbb:bb00:0001:0002:0003:0004:0005:0006']
    assert srv6_utils.sidlist_to_usidlist(sid_list) == usid_list


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
        'fcbb:bb00:0001:0002:0003:0004:0005:0006',
        'fcbb:bb00:0007:0008::',
    ]
    assert srv6_utils.sidlist_to_usidlist(sid_list) == usid_list


def test_nodes_to_micro_segments():
    nodes = ['R1', 'R2', 'R3', 'R4', 'R5', 'R6', 'R8']
    usid_list = [
        'fcbb:bb00:0001:0002:0003:0004:0005:0006',
        'fcbb:bb00:0008::',
    ]
    assert usid_list == srv6_utils.nodes_to_micro_segments(
        nodes, 'nodes.yml') == usid_list
