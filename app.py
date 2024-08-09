import json
from typing import Optional
import logging
import os
from flask import (
    Flask,
    jsonify,
    request,
)

from flask_cors import CORS
from flask_sock import Sock
from twilio.twiml.messaging_response import MessagingResponse
from websockets.exceptions import ConnectionClosed

from modules.call import CallModule

CALL_XML_RESPONSE = """\
<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Connect>
        <Stream url="wss://{url}/call"/>
    </Connect>
</Response>\
"""

app = Flask(__name__)
CORS(app)
socket = Sock(app)

call_module: Optional[CallModule] = None
TELEPHONY_URL = os.getenv("TELEPHONY_URL")

@app.route('/makecall', methods=['POST'])
def make_call():
    data = request.get_json()
    
    phone_number = data.get('phone_number')
    goal = data.get('goal')
    
    if not phone_number or not goal:
        return jsonify({"error": "phone_number and goal are required"}), 400
    call_module.initiate_call(TELEPHONY_URL, phone_number)
    
@app.route("/media", methods=["POST"])
def media():
    """Handles incoming media requests from telephony."""
    logging.info("CallApp received telephony HTTP Call. Responding with Stream TwiML.")
    return CALL_XML_RESPONSE.format(url=TELEPHONY_URL)

@socket.route("/call")
def echo(ws):
    """Handles WebSocket connections for media streaming."""
    logging.info("CallApp: telephony socket connection accepted")
    while True:
        try:
            message = ws.receive()
            stream_status = call_module.receive_media(message, ws)
            if not stream_status:
                break
        except ConnectionClosed as e:
            logging.info(f"CallApp: websocket connection closed with error: {e}")
        except Exception as e:
            logging.error(f"CallApp: websocket received unexpected error: {e}")


def set_call_app_module(callmodule: CallModule):
    global call_module
    call_module = callmodule
    logging.info("Global telephony_module set for call_app.")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)