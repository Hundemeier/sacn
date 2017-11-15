import threading
import socket
import time
from .output import Output

DEFAULT_PORT = 5568
SEND_OUT_INTERVAL_ms = 1000


class OutputThread(threading.Thread):
    def __init__(self, outputs, bind_address, bind_port: int = DEFAULT_PORT, fps: int = 30):
        super().__init__(name='sACN output/sender thread')
        self._outputs = outputs
        self._bindAddress = bind_address
        self.enabled_flag: bool = True
        self.fps: int = fps
        self._bind_port = bind_port

    def run(self):
        udp_sock = socket.socket(socket.AF_INET,  # Internet
                                 socket.SOCK_DGRAM)  # UDP
        try:
            udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        except:  # Not all systems support multiple sockets on the same port and interface
            pass
        udp_sock.bind((self._bindAddress, DEFAULT_PORT))

        self.enabled_flag = True
        while self.enabled_flag:
            # go through the list of outputs and send everything out that has to be send out
            for output in self._outputs.values():
                # send out when the 1 second interval is over
                if abs(current_time_millis() - output._last_time_send) > SEND_OUT_INTERVAL_ms or output._changed:
                    # make socket multicast-aware: (set TTL)
                    udp_sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, output.ttl)
                    send_out(udp_sock, self._bind_port, output)
            time.sleep(1 / self.fps)  # this is just a rough temp solution
        udp_sock.close()


def send_out(udp_sock: socket.socket, port: int, output: Output):
    # 1st: Destination (check if multicast)
    UDP_IP = output.destination
    if output.multicast:
        UDP_IP = output._packet.calculate_multicast_addr()
        # make socket multicast-aware: (set TTL) for some reason that does not work here,
        # so its in the run method from above
        # socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, output.ttl)

    MESSAGE = bytearray(output._packet.getBytes())
    udp_sock.sendto(MESSAGE, (UDP_IP, port))
    output._last_time_send = current_time_millis()
    # increase the sequence counter
    output._packet.sequence_increase()
    # the changed flag is not necessary any more
    output._changed = False


def current_time_millis():
    return int(round(time.time() * 1000))
