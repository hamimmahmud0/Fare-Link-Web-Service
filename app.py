from flask import Flask, jsonify, request, abort, g
from util_defs import *
from endpoints_util import contact_utils
import sqlite3
import time
from db import *
from ctx import *
from EventManager import *

app = Flask(__name__)
with app.app_context():
    init_db()


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
    result['data'] = result['data'][0]
    print(result)
    return jsonify(RESPONSE_OK | TIME() | result)

    


@app.errorhandler(400)
def handle_json(e):
    return jsonify(RESPONSE_NOT_VALID)

if __name__ == '__main__':
    # '0.0.0.0' makes the service accessible on your local network

    
    app.run(host='0.0.0.0', port=5000)
