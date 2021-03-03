from tornado import websocket

from ..packet import CDataPacket


class SocketHandler(websocket.WebSocketHandler):
    def __init__(self, application, request, **kwargs):
        self.opened = False
        self.ref = None
        super(self.__class__, self).__init__(application, request, **kwargs)

    def check_origin(self, origin):
        return True

    def open(self):
        self.opened = True
        self.application.register(self)

    def on_close(self):
        self.application.deregister(self)

    def on_message(self, message):
        print("Got message {}".format(message))
        # TODO: Fix this

        p = CDataPacket()
        self.application.sender.send_string(p.raw())

    def data_received(self, chunk):
        pass
