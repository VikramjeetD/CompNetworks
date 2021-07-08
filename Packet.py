from struct import pack, unpack
from enum import IntEnum
from Constants import HEADER_SIZE


class Packet(IntEnum):
    SYN = 0
    DATA = 1
    ACK = 2
    FIN = 3


def create_packet(pkt_type=Packet.DATA, seq_no=0, data=b''):
    return pack('IIB', seq_no, len(data) + HEADER_SIZE, pkt_type) + data


def decode_header(header):
    class Header():
        def __init__(self, seq_no, length, pkt_type):
            self.seq_no = seq_no
            self.content_length = length
            self.pkt_type = pkt_type

        def getattributes(self, attributes):
            attrs = []
            for attribute in attributes:
                attrs.append(getattr(self, attribute))
            return tuple(attrs)

    return Header(*unpack('IIB', header))
