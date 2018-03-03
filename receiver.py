import sacn
import time

# provide an IP-Address to bind to if you are using Windows and want to use multicast
receiver = sacn.sACNreceiver()
receiver.start()  # start the receiving thread

# define a callback function
@receiver.listen_on('universe', universe=1)  # listens on universe 1
def callback(packet):  # packet type: sacn.DataPacket
    print(packet.dmxData)  # print the received DMX data

# optional: if you want to use multicast use this function with the universe as parameter
receiver.join_multicast(1)

time.sleep(10)  # receive for 10 seconds
receiver.stop()
