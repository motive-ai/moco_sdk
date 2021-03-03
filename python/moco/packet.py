import logging
import struct
from collections import defaultdict

import os
try:
    from cffi.backend_ctypes import long, unicode
except ImportError:
    pass

try:
    from ._ffi_moco_packet import ffi
except ImportError:
    from cffi import FFI
    ffi = FFI()
    ffi.set_source("moco._ffi_moco_packet", None, libraries=[])
    dpt_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            '../../embedded/firmware/communication/data_packet_types.h')
    with open(dpt_path, 'r') as dpt_file:
        ffi_data = dpt_file.readlines()
    ffi.cdef(''.join(ffi_data[7:-2]))

import six
from .util.datatypes import update, set_values, AttributeDict

logger = logging.getLogger("Motive." + __name__)
MAX_DATA_SIZE = 512

ffi = ffi
PACKET_LEN = ffi.sizeof("GenericPacket")
PACKET_HEADER_LEN = ffi.sizeof("PacketHeader")
PACKET_DATA_LEN = ffi.sizeof("GenericData")
DATA_FMT = ffi.typeof("DataFormats").relements
DATA_FMT_INT = ffi.typeof("DataFormats").elements
dp = AttributeDict(DATA_FMT)
dp.PACKET_VERSION = 2
PACKET_SIGNATURE = struct.unpack('I', b"MPD" + str(dp.PACKET_VERSION).encode())[0]


class Packet(object):
    def __init__(self):
        self.header = ffi.new("PacketHeader *")
        self.data = ffi.new("GenericData *")


class CDataPacket(object):
    def __init__(self, raw=None, data_format=0, packet=None):
        self.command = None
        self.sub_command = None
        self.format_strings = DATA_FMT_STRINGS
        self.expander = None
        self.data_format = 0
        self.filler = b'\0' * PACKET_DATA_LEN
        self.data = None
        if packet:
            self.packet = packet
        else:
            self.packet = Packet()
        if raw:
            self.set_data(raw)
        else:
            if not packet:  # make a packet
                self.packet.header.data_format = data_format
                self.packet.header.sig = struct.unpack('I', b"MPD" + str(dp.PACKET_VERSION).encode())[0]
                self.packet.header.microseconds = 0
            self.packet.header.data_format = data_format
            self.packet.header.data_size = DATA_FMT_DATA_SIZES[self.packet.header.data_format]
            try:
                self.data = self.get_data_pointer(self.packet.header.data_format)
            except KeyError:
                self.data = self.packet.data
        self.header = self.packet.header

    def set_data(self, raw_data):
        (self.packet.header.sig, self.packet.header.data_size,
         self.packet.header.data_format, self.packet.header.microseconds, self.packet.header.flags,
         self.packet.header.sequence_number) = struct.unpack('IHHIHH', raw_data[0:PACKET_HEADER_LEN])
        data_len = len(raw_data[PACKET_HEADER_LEN:])
        if data_len < PACKET_DATA_LEN:
            raw2 = raw_data[PACKET_HEADER_LEN:] + self.filler[0:(PACKET_DATA_LEN - data_len - 2)]
            # TODO: bytes or str
            ffi.memmove(self.packet.data, bytes(raw2), PACKET_DATA_LEN - 2)
        else:
            ffi.memmove(self.packet.data,
                        raw_data[PACKET_HEADER_LEN:PACKET_DATA_LEN + PACKET_HEADER_LEN - 2],
                        PACKET_DATA_LEN)
        if self.data_format != self.packet.header.data_format:
            try:
                self.data = self.get_data_pointer(self.packet.header.data_format)
                self.data_format = self.packet.header.data_format
            except KeyError:
                self.data = self.packet.data

    def raw(self):
        return bytes(ffi.buffer(self.packet.header)) + \
            bytes(ffi.buffer(self.packet.data, self.header.data_size))

    @staticmethod
    def get_data_size(data_format):
        if data_format < dp.DATA_FMT_BASIC:
            return 0
        # TODO: Need to list all modes and all commands
        elif dp.DATA_FMT_OPEN_MODE <= data_format <= dp.DATA_FMT_NO_MODE:
            return ffi.sizeof("GenericControllerParams")
        elif dp.DATA_FMT_OPEN_COMMAND <= data_format <= dp.DATA_FMT_NO_COMMAND:
            return ffi.sizeof("GenericControllerCommands")
        elif dp.DATA_FMT_BASIC <= data_format < dp.DATA_FMT_OPEN_MODE:  # it's data
            return ffi.sizeof("GenericData")
        elif dp.DATA_FMT_AMP_PARAM <= data_format <= dp.DATA_FMT_NO_PARAM:
            return ffi.sizeof("ParamPacketBody")
        elif dp.DATA_FMT_PERIODIC_REQUEST <= data_format <= dp.DATA_FMT_NO_REQUEST:
            return ffi.sizeof("StatusDataRequest")
        else:
            return 0

    @staticmethod
    def make_data_format_strings():
        format_strings = dict()
        for data_format in DATA_FMT_INT:
            if data_format < dp.DATA_FMT_OPEN_MODE:  # it's data
                format_string = ('status', DATA_FMT_INT[data_format][9:].lower())
            elif dp.DATA_FMT_OPEN_MODE <= data_format <= dp.DATA_FMT_NO_MODE:
                format_string = ('mode', DATA_FMT_INT[data_format][9:-5].lower())
            elif dp.DATA_FMT_OPEN_COMMAND <= data_format <= dp.DATA_FMT_NO_COMMAND:
                format_string = ('command', DATA_FMT_INT[data_format][9:-8].lower())
            elif dp.DATA_FMT_NO_PARAM >= data_format >= dp.DATA_FMT_AMP_PARAM:
                format_string = ('param', DATA_FMT_INT[data_format][9:-6].lower())
            elif dp.DATA_FMT_PERIODIC_REQUEST <= data_format <= dp.DATA_FMT_NO_REQUEST:
                format_string = ('request', DATA_FMT_INT[data_format][9:-8].lower())
            else:
                continue
            format_strings[data_format] = format_string
        return format_strings

    def get_data_pointer(self, data_format):
        if data_format < dp.DATA_FMT_BASIC:
            return self.packet.data
        try:
            format_string = self.format_strings.get(data_format, ('', ''))[1]
        except IndexError:
            return self.packet.data
        if data_format == dp.DATA_FMT_STRING:
            strlen = self.packet.data.status.string.strlen
            b = bytes(ffi.buffer(self.packet.data.status.string.string, strlen))
            data = struct.unpack('{}s'.format(strlen), b)[0].decode()
        elif data_format < dp.DATA_FMT_OPEN_MODE:  # it's data
            data = getattr(self.packet.data.status, format_string)
        elif dp.DATA_FMT_OPEN_MODE <= data_format < dp.DATA_FMT_NO_MODE:
            data = getattr(self.packet.data.mode, format_string)
        elif dp.DATA_FMT_BRAKE_COMMAND < data_format < dp.DATA_FMT_NO_COMMAND:
            data = getattr(self.packet.data.command, format_string)
        elif dp.DATA_FMT_AMP_PARAM <= data_format < dp.DATA_FMT_NO_PARAM:
            data = getattr(self.packet.data.param, format_string)
        elif dp.DATA_FMT_PERIODIC_REQUEST <= data_format < dp.DATA_FMT_NO_REQUEST:
            data = getattr(self.packet.data.request, format_string)
        else:
            data = self.packet.data

        return data

    def data_dict(self):
        if self.expander is None:
            self.expander = ObjectExpander()
        if self.header.data_format != 255:
            data = self.expander.expand(self.data)
        else:
            data = {'generic_data': self.header}
        return data


class ObjectExpander(object):
    def __init__(self):
        self.known_objs = dict()

    def expand(self, obj):
        d = dict()
        obj_type = type(obj)
        if obj_type == ffi.CData:
            obj_type = ffi.typeof(obj)
        if obj_type is dict:
            fields = obj.keys()
        elif obj_type in self.known_objs:
            fields = self.known_objs[obj_type]
        else:
            fields = self.find_fields(obj)
            self.known_objs[obj_type] = fields
        for field, assignable in fields:
            a = getattr(obj, field)
            if not assignable:
                try:
                    ret_data = self.expand(a)
                    if ret_data:
                        d[field] = ret_data
                except AttributeError:
                    pass
            else:
                d[field] = a
        return d

    @staticmethod
    def find_fields(obj):
        all_fields = dir(obj)
        fields = list()
        for f in all_fields:
            if f[0] == '_' or f in ['this', 'thisown', 'string']:
                continue
            a = getattr(obj, f)
            if type(a) in [float, int, str, unicode, long]:
                assignable = True
            else:
                assignable = False
            fields.append((f, assignable))
        return fields


def make_packet(command, sub_command, params, packet=None, flags=0):
    cmd = command.lower()
    sub_cmd = sub_command.upper()
    cmd_type = 'DATA_FMT_{}_{}'.format(sub_cmd, cmd.upper())

    p = CDataPacket(data_format=DATA_FMT[cmd_type], packet=packet)
    p.header.flags = flags
    default_params = build_param_dict()[cmd][sub_command.lower()]
    validated_params = default_params
    if params:
        for k, v in six.iteritems(params):
            d = {k: v}
            try:
                validated_params = update(validated_params, d)
            except KeyError:
                pass

    set_values(p.data, validated_params)
    return p


def get_param_dict(packet):
    fmt = DATA_FMT_INT[packet.header.data_format]
    cmd = fmt[fmt.rfind('_') + 1:].lower()
    sub_cmd = fmt[9:fmt.rfind('_')].lower()
    return {cmd: {sub_cmd: packet.data_dict()}}


def build_param_dict():
    p = CDataPacket()
    packet_data = ObjectExpander().expand(p.data)
    commands = defaultdict(list)

    params = {}
    for k, v in six.iteritems(DATA_FMT):
        if v >= dp.DATA_FMT_OPEN_MODE:
            cmd = k[k.rfind('_') + 1:]
            commands[cmd].append(k[9:k.rfind('_')])
    for k, v in six.iteritems(commands):
        cmd = k.lower()
        params[cmd] = {}
        data_fields = packet_data[cmd]
        for sub_cmd in v:
            sub_cmd = sub_cmd.lower()
            try:
                params[cmd][sub_cmd] = data_fields[sub_cmd]
            except KeyError:  # needed because some commands (like open mode) have no data
                params[cmd][sub_cmd] = {}
    return params


def build_data_dict():
    p = CDataPacket()
    packet_data = ObjectExpander().expand(p.data.status)
    data_types = list()
    for k, v in six.iteritems(DATA_FMT):
        if v > 39:  # only data types 0-39 are data
            continue
        data_types.append(k[9:])
    params = {}
    for k in data_types:
        dt = k.lower()
        try:
            params[dt] = packet_data[dt]
        except KeyError:
            pass
    return params


DATA_FMT_STRINGS = CDataPacket.make_data_format_strings()
DATA_FMT_DATA_SIZES = {data_fmt: CDataPacket.get_data_size(data_fmt) for data_fmt in DATA_FMT_INT}
