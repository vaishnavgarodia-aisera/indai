from pydantic import BaseModel, Field
from typing import Optional


class CallInfo(BaseModel):
    call_sid: str = Field(..., description="Unique identifier for the call session.")
    stream_sid: str = Field(..., description="Unique identifier for the stream session.")
    phone_number: str = Field(..., description="Phone number associated with the call.")

class TelephonyAudioMessage(BaseModel):
    call_info: CallInfo = Field(..., description="Information about the call associated with the audio message.")
    audio_data: str = Field(..., description="Base64 encoded audio data.")

class TelephonyCallEndMessage(BaseModel):
    call_info: CallInfo = Field(..., description="Information about the call that ended.")