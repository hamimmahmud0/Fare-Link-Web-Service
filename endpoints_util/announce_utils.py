from util_defs import *
from ctx import announced_peers

REQUIRED_FIELDS = {
    'user-id':str,
    'access-link':str,
    'public-key':str
}

OPTIONAL_FIELDS = {
    'visible':bool,
    'announce-duration':int
}

ALL_FIELDS = REQUIRED_FIELDS | OPTIONAL_FIELDS

DEFAULT_CONTACT = {}


def is_request_valid(req):
    print(req.form)
    for key in REQUIRED_FIELDS:
        if not key in req.form:
            return False        
    return True


