
import argparse
import cv2
import pyvirtualcam
from pyvirtualcam import PixelFormat


# Set up webcam capture.
vc = cv2.VideoCapture(0)

if not vc.isOpened():
    raise RuntimeError('Could not open video source')

pref_width = 1280
pref_height = 720
pref_fps_in = 30
vc.set(cv2.CAP_PROP_FRAME_WIDTH, pref_width)
vc.set(cv2.CAP_PROP_FRAME_HEIGHT, pref_height)
vc.set(cv2.CAP_PROP_FPS, pref_fps_in)

# Query final capture device values (may be different from preferred settings).
width = int(vc.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(vc.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps_in = vc.get(cv2.CAP_PROP_FPS)
print(f'Webcam capture started ({width}x{height} @ {fps_in}fps)')

fps_out = 20

with pyvirtualcam.Camera(width, height, fps_out, fmt=PixelFormat.BGR, print_fps=True) as cam:
    print(f'Virtual cam started: {cam.device} ({cam.width}x{cam.height} @ {cam.fps}fps)')

    # Shake two channels horizontally each frame.
    channels = [[0, 1], [0, 2], [1, 2]]

    while True:
        # Read frame from webcam.
        ret, frame = vc.read()
        if not ret:
            raise RuntimeError('Error fetching frame')

        # Tiny bit of horizontal jitter
        dx = 5 - cam.frames_sent % 5
        c1, c2 = channels[cam.frames_sent % 3]
        frame[:,:-dx,c1] = frame[:,dx:,c1]
        frame[:,dx:,c2] = frame[:,:-dx,c2]

        # Send to virtual cam.
        cam.send(frame)

        # Wait until it's time for the next frame.
        cam.sleep_until_next_frame()