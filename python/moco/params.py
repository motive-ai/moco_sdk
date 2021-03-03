import json
import logging

from .packet import build_param_dict, get_param_dict
from .util.datatypes import flatten, update

logger = logging.getLogger("Motive." + __name__)


def get_default_param_json():
    params = build_param_dict()
    s = json.dumps(params, sort_keys=True, indent=2)
    print(s)


def read_param_file(param_file):
    data = json.load(param_file)
    if 'config_packets' in data.keys():
        return data['config_packets']
    else:
        try:
            data.pop('config')
        except KeyError:
            pass
        return data


def write_param_file(param_file, packet, existing_params_file=None):
    if existing_params_file:
        data = read_param_file(existing_params_file)
    else:
        data = {}
    data.update(get_param_dict(packet))
    json.dump({'config_packets': data}, param_file, sort_keys=True, indent=2)


def load_config(config_file):
    params = build_param_dict()
    if config_file:
        logger.debug("Loading config file '{}'".format(config_file.name))
        defaults = read_param_file(config_file)
        params = update(params, defaults, True)
    return params


def validate_params(param_file):
    defaults = flatten(read_param_file(param_file))
    params = flatten(build_param_dict())
    unknown_fields = []
    unset_fields = []
    for field in sorted(defaults.keys()):
        if field not in params:
            unknown_fields.append(field)
            logger.warning("Unknown parameter '{}'".format(field))
    for field in sorted(params.keys()):
        if field not in defaults:
            unset_fields.append(field)
            logger.warning("Unset parameter '{}'".format(field))
    return unknown_fields, unset_fields
