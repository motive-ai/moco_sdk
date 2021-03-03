#!/usr/bin/env python

import struct
from time import sleep

from moco.packet import CDataPacket, dp
from moco.util.zmqsocket import ZmqSender

if __name__ == '__main__':
    sender = ZmqSender(6511)
    # Give a little time to connect
    sleep(.5)

    # create a packet of that will put MoCo in Phase Lock mode
    # The `DATA_FMT_*` strings are from data_packet_types.h
    packet = CDataPacket(data_format=dp['DATA_FMT_PHASE_LOCK_MODE'])
    # set packet parameters
    packet.data.current_param.max_current = 1
    packet.data.phase_lock_current = 1
    print(packet.data_dict())

    print("Entering Phase Lock Mode")
    # Using `0xFEFE` will send the message to all boards.
    # Replace with serial number to send to a single board
    serial_int = struct.pack('i', int(0xFEFE))
    sender.send_multipart([serial_int, packet.raw()])

    # wait 3 seconds in phase lock mode
    sleep(3)

    # Put MoCo in Open mode
    print("Entering Open Mode")
    packet = CDataPacket(data_format=dp['DATA_FMT_OPEN_MODE'])
    sender.send_multipart([serial_int, packet.raw()])
    # sleep before exiting to give time for packets to be sent
    sleep(1)
