import socket
import wave
import struct
import numpy as np

ESP32_IP = "192.168.137.217"
UDP_PORT = 5005

SAMPLE_RATE = 8000
PACKETS = 160

CENTER = 2048
GAIN = 40

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("0.0.0.0", UDP_PORT))

sock.sendto(b"HELLO", (ESP32_IP, UDP_PORT))

print("Recording...")

pcm_samples = []

for _ in range(PACKETS):

    data, addr = sock.recvfrom(512)

    if len(data) != 512:
        continue

    samples = struct.unpack("<256H", data)

    for s in samples:

        pcm = (s - CENTER) * GAIN

        if pcm > 32767:
            pcm = 32767
        elif pcm < -32768:
            pcm = -32768

        pcm_samples.append(pcm)

audio = np.array(pcm_samples, dtype=np.float32)

# Remove DC offset
audio -= np.mean(audio)

# Normalize volume
peak = np.max(np.abs(audio))
if peak > 0:
    audio *= (30000 / peak)

audio = np.clip(audio, -32768, 32767).astype(np.int16)

with wave.open("speech.wav", "wb") as wav:
    wav.setnchannels(1)
    wav.setsampwidth(2)
    wav.setframerate(SAMPLE_RATE)
    wav.writeframes(audio.tobytes())

print("Saved as speech.wav")