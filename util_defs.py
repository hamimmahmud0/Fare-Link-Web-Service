# Basic Responses
import time

RESPONSE_OK = {
    'status':'success'
}
RESPONSE_NOT_VALID = {
    'status':"failed",
    'message':'request not valid'
}

def parse_form_args(req):
    parsed = {}
    for key in req.form:
        parsed[key] = req.form.get(key)
    return parsed


def TIME():
    return {
        'timestamp':time.time_ns()
    }