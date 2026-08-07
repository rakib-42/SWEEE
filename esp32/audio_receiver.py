import socket
import wave
import struct
import numpy as np

ESP32_IP = "192.168.137.3"
UDP_PORT = 5005

SAMPLE_RATE = 16000
RECORD_SECONDS = 5

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("0.0.0.0", UDP_PORT))

sock.sendto(b"HELLO", (ESP32_IP, UDP_PORT))

print("Recording...")

pcm = []

packets = int((SAMPLE_RATE * RECORD_SECONDS) / 512)

for _ in range(packets):

    data, addr = sock.recvfrom(1024)

    if len(data) == 0:
        continue

    count = len(data) // 2

    samples = struct.unpack("<{}h".format(count), data)

    pcm.extend(samples)

print("Normalizing...")

audio = np.array(pcm, dtype=np.float32)

audio -= np.mean(audio)

peak = np.max(np.abs(audio))

if peak > 0:
    audio *= 30000.0 / peak

audio = np.clip(audio, -32768, 32767).astype(np.int16)

with wave.open("speech.wav", "wb") as wav:

    wav.setnchannels(1)
    wav.setsampwidth(2)
    wav.setframerate(SAMPLE_RATE)

    wav.writeframes(audio.tobytes())

print("Saved as speech.wav")