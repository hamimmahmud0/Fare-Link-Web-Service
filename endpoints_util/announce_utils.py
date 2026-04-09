from util_defs import *
from ctx import announced_peers

REQUIRED_FIELDS = [
    'user-id',
    'access-link',
    'public-key'
]

OPTIONAL_FIELDS = [
    'visible',
    'announce-duration'
]


DEFAULT_CONTACT = {}


def is_request_valid(req):
    print(req.form)
    for key in REQUIRED_FIELDS:
        if not key in req.form:
            return False        
    return True


def add_peer
