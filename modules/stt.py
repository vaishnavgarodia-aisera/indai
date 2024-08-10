from flask import Flask, render_template
from deepgram import Deepgram
from aiohttp import web
from aiohttp_wsgi import WSGIHandler
import asyncio
import os

# Initialize Deepgram client
dg_client = Deepgram(os.getenv('DEEPGRAM_API_KEY'))

# Function to process audio and get transcription
async def process_audio():
    async def get_transcript(data):
        if 'channel' in data:
            transcript = data['channel']['alternatives'][0]['transcript']
            if transcript:
                print("Transcript recieved")
    deepgram_socket = await connect_to_deepgram(get_transcript)
    return deepgram_socket

# Function to connect to Deepgram's live transcription API
async def connect_to_deepgram(transcript_received_handler):
    try:
        socket = await dg_client.transcription.live(
            model="nova-2-phonecall",
            language="en",
            encoding="mulaw",
            sample_rate=8000,
            smart_format=True,
            no_delay=True,
            interim_results=True,
            endpointing=300,
            utterance_end_ms=1000
        )
        socket.registerHandler(socket.event.CLOSE, lambda c: print(f'Connection closed with code {c}.'))
        socket.registerHandler(socket.event.TRANSCRIPT_RECEIVED, transcript_received_handler)

        return socket
    except Exception as e:
        raise Exception(f'Could not open socket: {e}')