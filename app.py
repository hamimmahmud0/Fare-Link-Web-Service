from flask import Flask, jsonify, request, abort, g
from util_defs import *
from endpoints_util import contact_utils
import sqlite3
import time
import threading
import os
from db import *
from ctx import *
from EventManager import *

app = Flask(__name__)
with app.app_context():
    init_db()


def run_minute_job():
    with app.app_context():
        print(f'APP: Running minute job: {time.time_ns()}')
        # remove expired contacts
        


def minute_worker():
    while True:
        run_minute_job()
        time.sleep(60)


def start_background_worker():
    worker = threading.Thread(target=minute_worker, daemon=True)
    worker.start()


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

@app.route('/contacts/announce',methods=['POST'])
def announce_contact():
    form_args = parse_form_args(req = request)

    if not contact_utils.is_announce_request_valid(request):
        abort(400)
    
    contact_announce.send('app',data = form_args)

    response = RESPONSE_OK
    response["user-id"] = form_args["user-id"]
    response = response | TIME()

    return jsonify(response)


@app.route('/contacts/search',methods=['GET'])
def search_contact():
    form_args = parse_form_args(req = request)
    if not contact_utils.is_search_request_valid(request):
        abort(400)
    result = contact_search.send('app',data=form_args)[0][1]
    return jsonify(RESPONSE_OK | TIME() | result)

    


@app.errorhandler(400)
def handle_json(e):
    return jsonify(RESPONSE_NOT_VALID)


if __name__ == '__main__':
    # '0.0.0.0' makes the service accessible on your local network
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true" or not app.debug:
        start_background_worker()

    app.run(host='0.0.0.0', port=5000)
