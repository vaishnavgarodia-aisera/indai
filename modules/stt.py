import os
import json
import asyncio
from deepgram import Deepgram
from websockets import serve

# Configuration
HTTP_SERVER_PORT = 8080
stream_sid = ''  # Variable to store stream session ID
deepgram_api_key = os.getenv('DEEPGRAM_API_KEY')
deepgram_client = Deepgram(deepgram_api_key)
keep_alive = None

# Deepgram WebSocket Event Handlers
async def handle_transcript_event(event, media_stream):
    transcript = event['channel']['alternatives'][0]['transcript']
    if transcript:
        if event.get('is_final', False):
            media_stream['final_transcripts'].append(transcript)
            if event.get('speech_final', False):
                utterance = ' '.join(media_stream['final_transcripts'])
                media_stream['final_transcripts'].clear()
                print(f"Deepgram STT: [Speech Final] {utterance}")
                # Process final transcript (send to OpenAI, etc.)
            else:
                print(f"Deepgram STT: [Is Final] {transcript}")
        else:
            print(f"Deepgram STT: [Interim Result] {transcript}")
            # Handle interim transcript (e.g., barge-in logic)

async def handle_deepgram_connection(media_stream):
    media_stream['final_transcripts'] = []

    async def keep_alive_task():
        while True:
            await asyncio.sleep(10)
            await media_stream['deepgram_socket'].send(json.dumps({"type": "keep-alive"}))

    global keep_alive
    if keep_alive is None or keep_alive.cancelled():
        keep_alive = asyncio.create_task(keep_alive_task())

    async with deepgram_client.transcription.live(
        model="nova-2-phonecall",
        language="en",
        encoding="mulaw",
        sample_rate=8000,
        smart_format=True,
        no_delay=True,
        interim_results=True,
        endpointing=300,
        utterance_end_ms=1000
    ) as deepgram_socket:
        media_stream['deepgram_socket'] = deepgram_socket

        async for event in deepgram_socket.events():
            if event['type'] == 'transcript':
                await handle_transcript_event(event, media_stream)
            elif event['type'] == 'utterance_end':
                if media_stream['final_transcripts']:
                    utterance = ' '.join(media_stream['final_transcripts'])
                    media_stream['final_transcripts'].clear()
                    print(f"Deepgram STT: [Speech Final] {utterance}")
                    # Process final transcript (send to OpenAI, etc.)
            elif event['type'] == 'close':
                print("Deepgram STT: Disconnected")
                if keep_alive:
                    keep_alive.cancel()
                break
            elif event['type'] == 'error':
                print(f"Deepgram STT: Error received: {event}")
            elif event['type'] == 'warning':
                print(f"Deepgram STT: Warning received: {event}")
            elif event['type'] == 'metadata':
                print(f"Deepgram STT: Metadata received: {event}")
