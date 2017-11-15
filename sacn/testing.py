# if __package__ is None:
#     __package__ = "sacn.testing"
#     print('Changed package!')
#
# from sacn import sender
# from messages.data_packet import DataPacket
# import time
# import struct
# import random
#
# import _socket
# print(f"IPPROTO_UDP: {_socket.IPPROTO_UDP}")
# print(f"IPPROTO_IP: {_socket.IPPROTO_IP}")
# print(f"IP Multicast: {_socket.IP_MULTICAST_TTL}")
#
# sender = sender.sACNsender("192.168.1.4")
# sender.activate_output(1)
# sender[1].destination = "192.168.1.1"
# sender[1].multicast = True
# sender[1].ttl = 8#struct.pack('b', 8)
# sender[1].dmx_data = (2,3,8,9)
# sender.activate_output(2)
# sender[2].multicast = True
# sender[2].ttl = 12
# sender[2].dmx_data = (10,11,12,13)
# sender.deactivate_output(3)
#
# sender.start()
#
# time.sleep(2)
# for i in range(5000):
#     sender[1].dmx_data = tuple(int(random.random() * 255) for _ in range(0, 16))
#     sender[2].dmx_data = tuple(int(random.random() * 255) for _ in range(0, 16))
#     print("new dmx data!")
#     time.sleep(0.01)
# time.sleep(100)
# sender.stop()
#
import time

from sacn.receiver import sACNreceiver

def callback(packet):
    print(packet.dmxData)

rec = sACNreceiver()
rec.callbacks.append(callback)
rec.start()
rec.join_multicast(1)

time.sleep(10)
rec.stop()
