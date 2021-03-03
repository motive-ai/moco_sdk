#!/usr/bin/env python

import struct

from time import sleep

from moco.packet import CDataPacket
from moco.util.zmqsocket import ZmqListener
from moco.util.signal_handler import SignalHandler


class Receiver(object):
    ''' Simple class to receive packet data on specified port. Whenever new data is received,
    the callback function `got_data` is called.'''

    def __init__(self, port, host):
        self.sig_handler = SignalHandler(self.shutdown)
        # start a new thread to handle incoming data
        self.listener = ZmqListener(port, self.got_data, host)
        self.alive = True

    def got_data(self, data):
        serial = struct.unpack_from('i', data[0])[0]
        raw_bytes = data[1]

        # convert raw data into a packet
        packet = CDataPacket(raw=raw_bytes)
        # we now have a packet with data
        print(serial, packet.header.data_size, packet.data_dict())
        # do stuff with packet here...

    def shutdown(self, sig):
        self.listener.shutdown()
        self.alive = False


if __name__ == '__main__':
    receiver = Receiver(6510, 'localhost')
    # loop with main thread until receiver has ended
    while receiver.alive:
        sleep(1)
