
import argparse
import cv2
import pyvirtualcam
from pyvirtualcam import PixelFormat
from selenium import webdriver
from PIL import Image
from io import BytesIO
import numpy
import json 
from http.server import HTTPServer, BaseHTTPRequestHandler
import _thread as thread
import time 

class HttpServ(BaseHTTPRequestHandler):
    def do_GET(self):
       path = self.path
       if path == '/':
           path = '/index.html'
       path = '/www'+path           
       try:
           file_to_open = open(path[1:]).read()
           self.send_response(200)
       except:
           file_to_open = "File not found"
           self.send_response(404)
       self.end_headers()
       self.wfile.write(bytes(file_to_open, 'utf-8'))

def run_http_server():
    httpd = HTTPServer(('localhost',8080),HttpServ)
    httpd.serve_forever()

# Start up a local http server in a bg thread
thread.start_new_thread(run_http_server, ())

# Give HTTP server some time to start up
time.sleep(5)


OVERLAY_WIDTH = 1920
OVERLAY_HEIGHT = 1080


options = webdriver.ChromeOptions()
options.add_argument('headless')
options.add_argument('window-size=%dx%d' % (OVERLAY_WIDTH, OVERLAY_HEIGHT))

browser = webdriver.Chrome(options)
browser.get('http://127.0.0.1:8080')

# Send custom cmd to set background color to 0 alpha
url = browser.command_executor._url + "/session/%s/chromium/send_command_and_get_result" % browser.session_id
body = json.dumps({'cmd':"Emulation.setDefaultBackgroundColorOverride", 'params': {'color': {'r': 0, 'g': 0, 'b': 0, 'a': 0}}})
response = browser.command_executor._request('POST', url, body)
# if response['status']: raise Exception(response.get('value'))


# Extract screenshot pixels
browser_element = browser.find_element(value='hello')



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

        # Extract screenshot of browser
        browser_element_png = browser_element.screenshot_as_png
        browser_element_stream = BytesIO(browser_element_png)
        browser_image = Image.open(browser_element_stream).convert("RGBA")
        browser_element_stream.close()

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