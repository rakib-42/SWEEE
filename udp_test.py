"""Standalone UDP diagnostic — checks whether the ESP32 is actually
reaching this machine at all, without loading Whisper/VAD/Piper.

Run this on its own:
    python udp_test.py

Then either:
  - power-cycle the ESP32, or
  - trigger it however it starts streaming (button press, etc.)

If you see "packet received" lines, networking is fine and the problem
is elsewhere. If you see nothing after ~15 seconds, it's a networking
problem (see the checklist printed below).
"""

import socket
import time

from speech.config import ESP32_IP, UDP_PORT

print(f"Listening for UDP packets on 0.0.0.0:{UDP_PORT}")
print(f"Expecting the ESP32 at {ESP32_IP}")
print("Sending HELLO handshake...")

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("0.0.0.0", UDP_PORT))
sock.settimeout(15.0)

try:
    sock.sendto(b"HELLO", (ESP32_IP, UDP_PORT))
except OSError as exc:
    print(f"Could not even send to {ESP32_IP}:{UDP_PORT} — {exc}")

count = 0
start = time.time()

try:
    while time.time() - start < 15.0:
        try:
            data, addr = sock.recvfrom(4096)
            count += 1
            print(f"packet received #{count}: {len(data)} bytes from {addr}")
        except socket.timeout:
            break
except KeyboardInterrupt:
    pass

print()
if count > 0:
    print(f"Received {count} packets. Networking is fine.")
else:
    print("No packets received in 15 seconds. Checklist:")
    print("  1. Is the ESP32 actually powered on and connected to WiFi?")
    print("  2. Try: ping", ESP32_IP, "  (does it respond at all?)")
    print("  3. Run 'ipconfig' on this laptop — has ITS IP changed?")
    print("     The ESP32 firmware must be sending to THIS laptop's")
    print("     current IP, not just any IP. If your laptop's IP changed")
    print("     since the ESP32 was last configured/flashed, it's sending")
    print("     audio to an address nobody is listening on anymore.")
    print("  4. Windows Firewall may be silently blocking incoming UDP")
    print("     on port", UDP_PORT, "for python.exe — try temporarily")
    print("     disabling it (or add an inbound allow rule) as a test.")
    print("  5. Confirm the ESP32 and this laptop are on the SAME")
    print("     WiFi network/subnet (192.168.137.x on both).")