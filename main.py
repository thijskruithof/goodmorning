
import argparse
import cv2
import pyvirtualcam
from pyvirtualcam import PixelFormat
from selenium import webdriver
from PIL import Image
from io import BytesIO
import numpy
import json 

OVERLAY_WIDTH = 1920
OVERLAY_HEIGHT = 1080


options = webdriver.ChromeOptions()
options.add_argument('headless')
options.add_argument('window-size=%dx%d' % (OVERLAY_WIDTH, OVERLAY_HEIGHT))

browser = webdriver.Chrome(options)
browser.get('file:///D:/Private/Projects/goodmorning/hello.html')

# Send custom cmd to set background color to 0 alpha
url = browser.command_executor._url + "/session/%s/chromium/send_command_and_get_result" % browser.session_id
body = json.dumps({'cmd':"Emulation.setDefaultBackgroundColorOverride", 'params': {'color': {'r': 0, 'g': 0, 'b': 0, 'a': 0}}})
response = browser.command_executor._request('POST', url, body)
# if response['status']: raise Exception(response.get('value'))


# Extract screenshot pixels
element = browser.find_element(value='hello')
element_png = element.screenshot_as_png

stream = BytesIO(element_png)
browser_image = Image.open(stream).convert("RGBA")
stream.close()
# image.save('out.png')

# exit()


# Set up webcam capture.
vc = cv2.VideoCapture(0)

if not vc.isOpened():
    raise RuntimeError('Could not open video source')

pref_width = 1920
pref_height = 1080
pref_fps_in = 30
vc.set(cv2.CAP_PROP_FRAME_WIDTH, pref_width)
vc.set(cv2.CAP_PROP_FRAME_HEIGHT, pref_height)
vc.set(cv2.CAP_PROP_FPS, pref_fps_in)

# Query final capture device values (may be different from preferred settings).
width = int(vc.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(vc.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps_in = vc.get(cv2.CAP_PROP_FPS)
print(f'Webcam capture started ({width}x{height} @ {fps_in}fps)')

fps_out = 30

with pyvirtualcam.Camera(width, height, fps_out, fmt=PixelFormat.BGR, print_fps=True) as cam:
    print(f'Virtual cam started: {cam.device} ({cam.width}x{cam.height} @ {cam.fps}fps)')

    # Shake two channels horizontally each frame.
    channels = [[0, 1], [0, 2], [1, 2]]

    while True:
        # Read frame from webcam.
        ret, frame = vc.read()
        if not ret:
            raise RuntimeError('Error fetching frame')
        
        # Create image for webcam frame
        cam_image = Image.fromarray(frame, mode="RGB")
        cam_image = cam_image.convert("RGBA")

        # Draw browser on top
        cam_image.alpha_composite(browser_image, (10,10))
        cam_image = cam_image.convert("RGB")

        # # Tiny bit of horizontal jitter
        # dx = 5 - cam.frames_sent % 5
        # c1, c2 = channels[cam.frames_sent % 3]
        # frame[:,:-dx,c1] = frame[:,dx:,c1]
        # frame[:,dx:,c2] = frame[:,:-dx,c2]

        # Construct 1D array for our frame
        frame_1d = numpy.frombuffer(cam_image.tobytes(), dtype=numpy.uint8)
        # Remap into 3D array
        frame = numpy.reshape(frame_1d, newshape=(height, width, 3))

        # Send to virtual cam.
        cam.send(frame)

        # Wait until it's time for the next frame.
        cam.sleep_until_next_frame()