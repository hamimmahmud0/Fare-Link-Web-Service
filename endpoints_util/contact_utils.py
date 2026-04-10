from util_defs import *


REQUIRED_FIELDS = {
    'user-id':str,
    'access-link':str
}

OPTIONAL_FIELDS = {
    'visible':bool,
    'announce-duration':int
}

ALL_FIELDS = REQUIRED_FIELDS | OPTIONAL_FIELDS


REQUIRED_SEARCH_FIELDS = {
    'user-id':str
}

DEFAULT_CONTACT = {
    'user-id':'',
    'access-link':'',
    'visible':True,
    'announce-duration':5*60
}


def is_request_valid(req, template):
    for key in template:
        if not key in req.form:
            return False        
    return True


def is_announce_request_valid(req):
    return is_request_valid(req, template=REQUIRED_FIELDS)

def is_search_request_valid(req):
    return is_request_valid(req,template=REQUIRED_SEARCH_FIELDS)
