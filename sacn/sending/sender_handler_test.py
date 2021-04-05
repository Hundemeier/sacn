# This file is under MIT license. The license file can be obtained in the root directory of this module.

from typing import Dict
from sacn.messages.data_packet import DataPacket
from sacn.messages.universe_discovery import UniverseDiscoveryPacket
from sacn.sending.output import Output
from sacn.sending.sender_handler import SenderHandler
from sacn.sending.sender_socket_test import SenderSocketTest


def test_universe_discovery_packets():
    cid = tuple(range(0, 16))
    source_name = 'test'
    outputs: Dict[int, Output] = {
        1: Output(
            packet=DataPacket(
                cid=cid,
                sourceName=source_name,
                universe=1,
            )
        )
    }
    socket = SenderSocketTest()
    handler = SenderHandler(
        cid=cid,
        source_name=source_name,
        outputs=outputs,
        bind_address='0.0.0.0',
        bind_port=5568,
        fps=30,
        socket=socket,
    )
    handler.manual_flush = True
    # wire up listener for tests
    socket._listener = handler
    current_time = 100.0

    assert handler.universe_discovery is True
    assert socket.send_broadcast_called is None

    # test that the universe discovery can be disabled
    handler.universe_discovery = False
    socket.call_on_periodic_callback(current_time)
    assert socket.send_broadcast_called is None
    handler.universe_discovery = True

    # if no outputs are specified, there is an empty universe packet send
    socket.call_on_periodic_callback(current_time)
    assert socket.send_broadcast_called == UniverseDiscoveryPacket(cid, source_name, (1,))


def test_send_out_interval():
    cid = tuple(range(0, 16))
    source_name = 'test'
    outputs: Dict[int, Output] = {
        1: Output(
            packet=DataPacket(
                cid=cid,
                sourceName=source_name,
                universe=1,
                sequence=0,
            )
        )
    }
    socket = SenderSocketTest()
    handler = SenderHandler(
        cid=cid,
        source_name=source_name,
        outputs=outputs,
        bind_address='0.0.0.0',
        bind_port=5568,
        fps=30,
        socket=socket,
    )
    # wire up listener for tests
    socket._listener = handler
    current_time = 100.0

    assert handler.manual_flush is False
    assert socket.send_unicast_called is None

    # first send packet due to interval
    socket.call_on_periodic_callback(current_time)
    assert socket.send_unicast_called[0].__dict__ == DataPacket(cid, source_name, 1, sequence=0).__dict__
    assert socket.send_unicast_called[1] == '127.0.0.1'

    # interval must be 1 seconds
    socket.call_on_periodic_callback(current_time+0.99)
    assert socket.send_unicast_called[0].__dict__ == DataPacket(cid, source_name, 1, sequence=0).__dict__
    socket.call_on_periodic_callback(current_time+1.01)
    assert socket.send_unicast_called[0].__dict__ == DataPacket(cid, source_name, 1, sequence=1).__dict__


def test_multicast():
    # TODO
    pass


def test_unicast():
    # TODO
    pass


def test_send_out_all_universes():
    # TODO
    pass
