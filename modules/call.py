import json
import queue
import logging
import os
from twilio.rest import Client

from domain import CallInfo, TelephonyAudioMessage, TelephonyCallEndMessage

TELEPHONY_PHONE_NUMBER = os.getenv("TELEPHONY_PHONE_NUMBER")
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TELEPHONY_URL=os.getenv("TELEPHONY_URL")

class  CallModule():
    """Telephony module class using Twilio to handle calls and SMS messages."""

    def __init__(self):
        self.client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        self.call_messages = queue.Queue()
        self.call_id_to_phone_number = {}  # call_sid => phone_number
        self.connected_sockets = {}  # stream_sid => socket
        
    def initiate_call(self, receiver_number: str):
        print("Call initiated")
        try:
            call = self.client.calls.create(
                url=f"https://{TELEPHONY_URL}/media",
                to=receiver_number,
                from_=TELEPHONY_PHONE_NUMBER,
            )
        except Exception as e:
            logging.info("Initiating call exception: {}".format(e))
            return None
        logging.info("Call Module initiated a call to {receiver_number} with twilio.")
        self.call_id_to_phone_number[call.sid] = receiver_number
        return call

    def receive_media(self, message, ws, deepgram_socket):
        try:
            data = json.loads(message)
        except json.JSONDecodeError:
            logging.info("Call Module failed to parse JSON from WebSocket message.")
            return False
        if not data:
            logging.info("Call Module received empty data through socket.")
            return False

        message_event = data.get("event", None)
        if message_event == "connected":
            logging.info("Call Module received connected message.")
            return True

        stream_sid = data.get("streamSid", None)
        call_info = CallInfo(call_sid=None, stream_sid=stream_sid)
        if message_event == "start":
            self.connected_sockets[stream_sid] = ws
            logging.debug(f"Call Module call connected for callSid: {call_sid} and streamSid: {stream_sid}.")
        elif message_event == "media":
            audio_data = data["media"]["payload"]
            deepgram_socket.send(audio_data)
        elif message_event in ["stop"]:
            call_sid = data["stop"]["callSid"]
            call_info.call_sid = call_sid
            self.call_messages.put(TelephonyCallEndMessage(call_info=call_info))
            logging.debug(f"Call Module received stop message for streamSid: {stream_sid}.")
            return False
        else:
            logging.info(f"Call Module received unknown message: {message}.")
        return True

    def end_call(self, call_sid: str):
        self.client.calls(call_sid).update(status="completed")

    def cleanup_socket(self, stream_sid: str, call_id: str):
        self.connected_sockets.pop(stream_sid)
        self.call_id_to_phone_number.pop(call_id)