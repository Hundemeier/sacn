# This file is under MIT license. The license file can be obtained in the root
# directory of this module.

import pytest
from sacn.messages.root_layer import \
    byte_tuple_to_int, \
    int_to_bytes, \
    make_flagsandlength, \
    RootLayer


def test_int_to_bytes():
    assert int_to_bytes(0xFFFF) == [0xFF, 0xFF]
    assert int_to_bytes(0x1234) == [0x12, 0x34]
    # test that the value cannot exceed two bytes
    with pytest.raises(TypeError):
        int_to_bytes(0x123456)
    assert int_to_bytes(0x0001) == [0x00, 0x01]


def test_make_flagsandlength():
    assert make_flagsandlength(0x123) == [0x71, 0x23]
    with pytest.raises(ValueError):
        assert make_flagsandlength(0x1234) == [0x72, 0x34]
    assert make_flagsandlength(0x001) == [0x70, 0x01]


def test_root_layer_bytes():
    cid = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16)
    vector = (1, 2, 3, 4)
    # test that the vector length must be 4
    with pytest.raises(ValueError):
        RootLayer(0, cid, ())
    # test that the cid length must be 16
    with pytest.raises(ValueError):
        RootLayer(0, (), vector)
    packet = RootLayer(0x123456, cid, vector)
    shouldBe = [
        # initial static vector
        0, 0x10, 0, 0, 0x41, 0x53, 0x43, 0x2d, 0x45,
        0x31, 0x2e, 0x31, 0x37, 0x00, 0x00, 0x00,
        # length value
        0x74, 0x46
    ]
    # vector
    shouldBe.extend(vector)
    # cid
    shouldBe.extend(cid)
    assert packet.getBytes() == shouldBe


def test_int_byte_transitions():
    # test the full 0-65534 range, though only using 0-63999 currently
    for input_i in range(65536):
        converted_i = byte_tuple_to_int(tuple(int_to_bytes(input_i)))
        assert input_i == converted_i
