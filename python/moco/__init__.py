import json
import logging

import zmq
from moco.util.zmqsocket import ZmqSender

logger = logging.getLogger(__name__)


def get_config_from_master(master_host='localhost', master_port=6500, serial=None):
    sender = ZmqSender(master_port, master_host, zmq_type=zmq.REQ, timeout=100)
    try:
        d = dict(command='config')
        resp = sender.send(json.dumps(d))
        config_json = resp[0].decode()
        config = json.loads(config_json)
        if serial:
            d['id'] = serial
        d['command'] = 'status'
        resp = sender.send(json.dumps(d))
        boards_json = resp[0].decode()
        boards = json.loads(boards_json)
        if serial:
            boards = boards[serial]
    except zmq.error.Again:
        logger.error("No Moco Manager running on {}".format(sender.full_address))
        config = dict()
        boards = dict()
    except KeyError:
        logger.error("No board {} found on Manager".format(serial))
        config = dict()
        boards = dict()
    return config, boards
