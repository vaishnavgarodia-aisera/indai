from pydantic import BaseModel, Field
from typing import Optional


class CallInfo(BaseModel):
    call_sid: str = Field(..., description="Unique identifier for the call session.")
    stream_sid: str = Field(..., description="Unique identifier for the stream session.")
    phone_number: str = Field(..., description="Phone number associated with the call.")

class StreamSessionData(BaseModel):
    packets_since_media_out: int = Field(0, description="Number of packets sent since last media output.")

class TelephonyAudioMessage(BaseModel):
    call_info: CallInfo = Field(..., description="Information about the call associated with the audio message.")
    audio_data: str = Field(..., description="Base64 encoded audio data.")

class TelephonyCallEndMessage(BaseModel):
    call_info: CallInfo = Field(..., description="Information about the call that ended.")

class TelephonyCallStartMessage(BaseModel):
    call_info: CallInfo = Field(..., description="Information about the call that started.")
    start_time: str = Field(..., description="Timestamp when the call started.")

class TelephonyMarkMessage(BaseModel):
    call_info: CallInfo = Field(..., description="Information about the call associated with the mark message.")
    mark_name: str = Field(..., description="Name of the mark received during the call.")
