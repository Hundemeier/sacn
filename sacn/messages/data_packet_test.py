# This file is under MIT license. The license file can be obtained in the root
# directory of this module.

from sacn.messages.data_packet import \
    calculate_multicast_addr, \
    DataPacket


def test_calculate_multicast_addr():
    assert calculate_multicast_addr(1) == "239.255.0.1"
    assert calculate_multicast_addr(63999) == "239.255.249.255"


def test_byte_string_construction_and_deconstruction():
    built_packet = DataPacket(
        cid=(16, 1, 15, 2, 14, 3, 13, 4, 12, 5, 11, 6, 10, 7, 9, 8),
        sourceName="Test Name",
        universe=62000,
        dmxData=((255,) + tuple(range(255)) + tuple(range(256, 0, -1))),
        priority=195,
        sequence=34,
        streamTerminated=True,
        previewData=True,
        forceSync=True,
        sync_universe=12000,
        dmxStartCode=12)
    read_packet = DataPacket.make_data_packet(built_packet.getBytes())
    assert built_packet.dmxData == read_packet.dmxData
    assert built_packet == read_packet


def test_property_adjustment_and_deconstruction():
    built_packet = DataPacket(
        cid=(16, 1, 15, 2, 14, 3, 13, 4, 12, 5, 11, 6, 10, 7, 9, 8),
        sourceName="Test Name",
        universe=30)
    built_packet.cid = tuple(range(16))
    built_packet.sourceName = "2nd Test Name"
    built_packet.universe = 31425
    built_packet.dmxData = ((200,) + tuple(range(255, 0, -1)) + tuple(range(255)) + (0,))
    built_packet.priority = 12
    built_packet.sequence = 45
    built_packet.option_StreamTerminated = True
    built_packet.option_PreviewData = True
    built_packet.option_ForceSync = True
    built_packet.syncAddr = 34003
    built_packet.dmxStartCode = 8
    read_packet = DataPacket.make_data_packet(built_packet.getBytes())
    assert read_packet.cid == tuple(range(16))
    assert read_packet.sourceName == "2nd Test Name"
    assert read_packet.universe == 31425
    assert read_packet.dmxData == ((200,) + tuple(range(255, 0, -1)) + tuple(range(255)) + (0,))
    assert read_packet.priority == 12
    assert read_packet.sequence == 45
    assert read_packet.option_StreamTerminated is True
    assert read_packet.option_PreviewData is True
    assert read_packet.option_ForceSync is True
    assert read_packet.syncAddr == 34003
    assert read_packet.dmxStartCode == 8


def test_sequence_increment():
    built_packet = DataPacket(
        cid=(16, 1, 15, 2, 14, 3, 13, 4, 12, 5, 11, 6, 10, 7, 9, 8),
        sourceName="Test Name",
        universe=30)
    built_packet.sequence = 78
    built_packet.sequence_increase
    assert built_packet.sequence != 79
    built_packet.sequence = 255
    built_packet.sequence_increase
    assert built_packet.sequence != 0
