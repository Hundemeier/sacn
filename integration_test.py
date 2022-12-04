# This is an example in how to use the sacn library to send and receive DMX data via sACN.
# It assumes a multicast ready environment and the packets probably can be captured on the loopback traffic interface.
# A sender and receiver is created, so that the receiver receives the values transmitted from the sender.
# Each first eight bytes that the receiver gets are printed to the console.
# Note that not each packet that is set by the sender loop is actually send out.
# (e.g. (5, 6, 7, 8, ...) is followed by (8, 9, 10, 11, ...))
# This is due to the fact, that the sending loop sets the DMX data approx. every 10ms,
# but the sending thread subsamples with approx. 33ms.
# The universe that is used to transmit the data is switched from 1 to 2 in between.

import time
import sacn
import logging
import pytest
from collections import OrderedDict


@pytest.mark.timeout(10)
@pytest.mark.integration_test
def test_integration():
    logging.basicConfig(level=logging.DEBUG)  # enable logging of sacn module
    universes_changes = []  # used by the integration test
    universe_packet_counter = {1: 0, 2: 0}

    receiver = sacn.sACNreceiver()
    receiver.start()  # start the receiving thread

    sender = sacn.sACNsender()
    sender.start()  # start the sending thread

    @receiver.listen_on('availability')  # check for availability of universes
    def callback_available(universe, changed):
        print(f'universe {universe}: {changed}')
        universes_changes.append((universe, changed))

    @receiver.listen_on('universe', universe=1)  # listens on universes 1 and 2
    @receiver.listen_on('universe', universe=2)
    def callback(packet):  # packet type: sacn.DataPacket
        print(f'{packet.universe}: {packet.dmxData[:8]}')  # print the received DMX data, but only the first 8 values
        universe_packet_counter[packet.universe] += 1

    receiver.join_multicast(1)
    receiver.join_multicast(2)

    sender.activate_output(1)  # start sending out data in the 1st universe
    sender[1].multicast = True  # set multicast to True

    def send_out_for_2s(universe: int):
        # with 200 value changes and each taking 10ms, this for-loop runs for 2s
        for i in range(0, 200):
            # set test DMX data that increases its first four values each iteration
            sender[universe].dmx_data = tuple(x % 256 for x in range(i, i + 4))
            time.sleep(0.01)  # sleep for 10ms

    send_out_for_2s(1)
    sender.move_universe(1, 2)
    send_out_for_2s(2)

    sender.deactivate_output(2)

    receiver.leave_multicast(1)
    receiver.leave_multicast(2)

    # stop both threads
    receiver.stop()
    sender.stop()

    # assertions of the integration test:
    # use an ordered dict to retain the order in which the events ocurred,
    # but not the amount of events (e.g. the timeout event can be called multiple times, depending on thread timings)
    assert OrderedDict(universes_changes) == OrderedDict([(1, "available"), (1, "timeout"), (2, "available"), (2, "timeout")])
    # depending on the thread timing, the amount of packets received might be higher than 60 packets
    # there are 30 packets per second and the test runs for at least two seconds
    assert universe_packet_counter[1] in range(60, 80)
    assert universe_packet_counter[2] in range(60, 80)


if __name__ == '__main__':
    test_integration()
