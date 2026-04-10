from util_defs import *


REQUIRED_FIELDS = {
    'user-id':str,
    'access-link':str
}

OPTIONAL_FIELDS = {
    'visible':bool,
    'expire':int # in minutes
}

ALL_FIELDS = REQUIRED_FIELDS | OPTIONAL_FIELDS


REQUIRED_SEARCH_FIELDS = {
    'user-id':str
}
DEFAULT_CONTACT = {
    'user-id':'',
    'access-link':'',
    'visible':True,
    'expire':5 # in minutes
}


def is_request_valid(req, template):
    for key in template:
        if not key in req.form:
            return False        
    return True


def is_announce_request_valid(req):
    if not is_request_valid(req, template=REQUIRED_FIELDS):
        return False

    for key in req.form:
        if key not in ALL_FIELDS:
            return False

    return True

def is_search_request_valid(req):
    return is_request_valid(req,template=REQUIRED_SEARCH_FIELDS)
