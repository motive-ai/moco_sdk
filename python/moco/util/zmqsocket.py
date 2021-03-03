import logging
import socket
from datetime import timedelta, datetime
from time import sleep

import six
import zmq
from zmq.error import ZMQError

from .datatypes import AttributeDict
from .threads import TimedTaskProcessor

logger = logging.getLogger(__name__)

# set the time out to 10 seconds
socket.setdefaulttimeout(10)


class ZmqBase(object):
    BIND = 'bind'
    CONNECT = 'connect'

    def __init__(self):
        self._context = zmq.Context(1)

    def shutdown(self):
        raise NotImplementedError()

    def __del__(self):
        self.shutdown()


def zmq_connection_address(port, host='localhost', zmq_method=ZmqBase.CONNECT, protocol='tcp'):
    if zmq_method == ZmqBase.CONNECT:
        return "{0}://{1}:{2}".format(protocol, host, port)
    else:
        return "{0}://{1}:{2}".format(protocol, "*", port)


class ZmqListener(ZmqBase):
    def __init__(self, port, callback, ip="127.0.0.1", name=None, zmq_type=zmq.SUB,
                 zmq_method=ZmqBase.CONNECT, topic='', callback_extra_args=()):
        super(self.__class__, self).__init__()
        self._poll_interval = 100
        self._type = zmq_type
        self._callback = callback
        self._callback_extra_args = callback_extra_args
        self._name = "ZMQ-Listener"
        if name:
            self._name += '-{0}'.format(name)
        self._port = port
        self._keep_going = True
        self._processor = None
        self._socket = None
        self._zmq_method = zmq_method
        self._topic = topic
        self._ip = ip
        self._protocol = "tcp"
        if self._zmq_method == ZmqBase.BIND:
            self._ip = "*"
        self.full_address = "{}://{}:{}".format(self._protocol, self._ip, self._port)
        self._processor = TimedTaskProcessor(self._listen, self._name, 0,
                                             init_func=self._listen_init, term_func=self._listen_terminate)
        self._processor.start()
        logger.info("{} on {}".format(self._name, self.full_address))

    def create_socket(self):
        self._socket = self._context.socket(self._type)
        try:
            if self._zmq_method == ZmqBase.BIND:
                self._socket.bind(self.full_address)
            else:
                self._socket.connect(self.full_address)
        except ZMQError as e:
            self._socket = None
            raise e
        if self._type == zmq.SUB:
            if isinstance(self._topic, str):
                self._socket.setsockopt_string(zmq.SUBSCRIBE, six.text_type(self._topic))
            else:
                self._socket.setsockopt(zmq.SUBSCRIBE, bytes(self._topic))
        self._socket.setsockopt(zmq.RCVTIMEO, self._poll_interval)
        # don't wait around after we send context.term()
        self._socket.setsockopt(zmq.LINGER, 0)

    def shutdown(self):
        self._keep_going = False
        sleep(self._poll_interval / 1000 * 2)  # Give the listener time to finish.
        logger.info("Shutting down {} on {}".format(self._name, self.full_address))
        try:
            logger.debug("Shutting down the TimedTaskProcessor")
            if self._processor:
                self._processor.shutdown()
                self._processor = None
        except ZMQError:
            logger.exception("Error shutting down worker thread")
        try:
            logger.debug("Destroying the ZMQ context")
            if self._context:
                self._context.destroy(linger=0)
                self._context = None
        except ZMQError:
            logger.exception("Error Terminating ZMQ context")

    def _listen_init(self):
        try:
            self.create_socket()
        except ZMQError:
            logger.exception("Could not create ZmqListener")
            self._processor.shutdown()
            raise

    def _listen_terminate(self):
        self._keep_going = False
        if self._socket:
            self._socket.close()

    def _listen(self):
            try:
                message = self._socket.recv_multipart(self._poll_interval)
            except zmq.error.Again:
                return
            reply = self._callback(message, *self._callback_extra_args)
            if self._type == zmq.REP:
                if not reply:
                    reply = ["ok"]
                if not isinstance(reply, (list, tuple)):
                    reply = [reply]
                try:
                    for msg_part in reply[:-1]:
                        self._socket.send_string(msg_part, zmq.SNDMORE)
                    self._socket.send_string(reply[-1])
                except zmq.ZMQError as e:
                    if e.errno == zmq.ENOTSUP:
                        self._keep_going = False
                    logger.exception("Listener %s received ZMQ Exception", self._name)


class ZmqSender(ZmqBase):
    def __init__(self, port, ip="127.0.0.1", zmq_type=zmq.PUB, zmq_method=ZmqBase.CONNECT,
                 timeout=-1):
        super(self.__class__, self).__init__()
        self._type = zmq_type
        if self._type not in [zmq.PUB, zmq.REQ]:
            raise Exception("Unknown ZMQ send type: %s", self._type)

        self.socket = self._context.socket(self._type)
        self.socket.setsockopt(zmq.LINGER, 0)  # don't wait around after we send context.term()
        self.timeout = timeout
        self.socket.setsockopt(zmq.RCVTIMEO, self.timeout)
        self.socket.setsockopt(zmq.SNDTIMEO, self.timeout)
        self._protocol = 'tcp'
        self.full_address = zmq_connection_address(port, ip, zmq_method, self._protocol)
        if zmq_method == ZmqBase.CONNECT:
            self.socket.connect(self.full_address)
        else:
            self.socket.bind(self.full_address)
        logger.info("{} on {}".format("ZmqSender", self.full_address))

    def send_multipart(self, data):
        if self._type == zmq.PUB:
            self.socket.send_multipart(data)
        else:
            raise Exception('multipart send not implemented for this socket type')

    def send(self, msg):
        # zmq send requires a byte-like object. On py2.7 this means a string, and on py3 this
        #   is a bytes object. The code below handles both. Note that bytes(msg) is a no-op in py2
        if not isinstance(msg, bytes):
            if isinstance(msg, str):
                msg = msg.encode()
            msg = bytes(msg)
        self.socket.send(msg)
        if self._type == zmq.REQ:
            data = [self.socket.recv()]
            while self.socket.getsockopt(zmq.RCVMORE):
                data.append(self.socket.recv())
            return data

    def shutdown(self):
        try:
            self.socket.close()
        except ZMQError:
            logger.warning("Error closing zmq socket on {}".format(self.full_address))


class HeartbeatException(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class HeartbeatSender(object):
    def __init__(self, port, identifier):
        self.context = zmq.Context()
        self.command_sender = self.context.socket(zmq.PUB)
        self.command_sender.connect("tcp://127.0.0.1:{}".format(port))
        self.command_sender.setsockopt(zmq.LINGER, 0)
        self.identity = identifier
        pass

    def __del__(self):
        self.shutdown()

    def shutdown(self):
        if self.command_sender is not None:
            self.command_sender.close(linger=0)
        if self.context is not None:
            self.context.destroy(linger=0)
        self.command_sender = None
        self.context = None

    def send_heartbeat(self):
        self.command_sender.send("HEARTBEAT {}".format(self.identity))

    def send_custom_command(self, command):
        if command.find(' ') != -1:
            raise HeartbeatException('command cannot contain spaces')
        self.command_sender.send("{} {}".format(command, self.identity))


class HeartbeatReceiver(object):
    """Listens over a zmq socket for commands from a registered sender"""

    def __init__(self, port, default_timeout=timedelta(seconds=30)):
        self.registered_senders = {}
        self.timeout = default_timeout
        self.port = port
        self.context = zmq.Context()
        self.command_listener = self.context.socket(zmq.SUB)
        self.command_listener.bind("tcp://*:{}".format(self.port))
        self.command_listener.setsockopt(zmq.SUBSCRIBE, "")
        self.command_listener.setsockopt(zmq.LINGER, 0)
        self.command_listener.setsockopt(zmq.RCVTIMEO, 300)
        self.custom_command_callbacks = []
        self._poller = zmq.Poller()
        self._poller.register(self.command_listener, zmq.POLLIN | zmq.POLLOUT)
        self._keep_running = True

    def __del__(self):
        self.shutdown()

    def shutdown(self):
        if self.command_listener:
            self.command_listener.close(linger=0)
        if self.context:
            self.context.destroy(linger=0)
        self.command_listener = None
        self.context = None

    def listen(self):
        try:
            messages = len(self._poller.poll(10)) > 0
            if not messages:
                return
            cmd = self.command_listener.recv()
            cmd_action, ident = cmd.split()
            if cmd_action == 'HEARTBEAT':
                self.update_heartbeat(ident)
            else:
                self.call_custom_callback(cmd_action, ident)
        except zmq.ZMQError:
            return

    def register_id(self, ident, timeout=None):
        ident = str(ident)
        if timeout is None:
            timeout = self.timeout
        self.registered_senders[ident] = AttributeDict({'last_heartbeat': datetime.utcnow(),
                                                        'heartbeat_count': 0,
                                                        'timeout': timeout})

    def update_heartbeat(self, ident, time=None):
        if time is None:
            time = datetime.utcnow()
        ident = str(ident)
        self.registered_senders[ident].last_heartbeat = time
        self.registered_senders[ident].heartbeat_count += 1

    def expired_senders(self):
        curr_time = datetime.utcnow()
        expired = []
        for ident, sender in self.registered_senders.items():
            if curr_time - sender.last_heartbeat > sender.timeout:
                expired.append(ident)
        return expired

    def register_command_callback(self, command, callback_fn):
        if command.find(' ') != -1:
            raise HeartbeatException('command cannot contain spaces')
        self.custom_command_callbacks.append(AttributeDict({'command': command,
                                                            'callback': callback_fn}))

    def call_custom_callback(self, command, ident):
        ident = str(ident)
        for cmd in self.custom_command_callbacks:
            if cmd.command == command:
                cmd.callback(ident)

    def get_heartbeat_count(self, ident):
        return self.registered_senders[ident].heartbeat_count

    def get_heartbeat_time(self, ident):
        return self.registered_senders[ident].last_heartbeat
