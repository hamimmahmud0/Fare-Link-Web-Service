from flask import Flask, jsonify, request, abort, g
from util_defs import *
from endpoints_util import announce_utils
import sqlite3
import time
from db import *
from ctx import *

app = Flask(__name__)


@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()



# The "Route" defines the URL path
@app.route('/')
def home():
    return "Hello, World! Your Python service is running."

# An example of a JSON API endpoint
@app.route('/ping')
def ping():
    return jsonify({
        "status": "success",
        "message": "OK"
    })

@app.route('/announce',methods=['POST'])
def announce():
    form_args = parse_form_args(req = request)

    if not announce_utils.is_request_valid(request):
        abort(400)
    

    response = RESPONSE_OK
    response["user-id"] = form_args["user-id"]
    response["time"] = time.time()

    return jsonify(form_args)

@app.errorhandler(400)
def handle_json(e):
    return jsonify(RESPONSE_NOT_VALID)

if __name__ == '__main__':
    # '0.0.0.0' makes the service accessible on your local network

    init_db()

    app.run(host='0.0.0.0', port=5000)