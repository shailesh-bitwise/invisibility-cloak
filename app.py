from flask import Flask, render_template, Response, request
import cv2
import numpy as np

app = Flask(__name__)

cap = cv2.VideoCapture(0)
background = None

# Capture the background
for i in range(30):
    ret, background = cap.read()
background = np.flip(background, axis=1)  # Flip background horizontally

# Global variable to hold the selected color from the user
selected_color = [0, 0, 0]  # Default color (black)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/set_color', methods=['POST'])
def set_color():
    global selected_color
    hex_color = request.json['color']  # Color sent from client
    # Convert hex to RGB
    selected_color = tuple(int(hex_color[i:i+2], 16) for i in (1, 3, 5))
    return "Color updated", 200

def gen_frames():
    global selected_color, background
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        img = np.flip(frame, axis=1)

        # Convert BGR to HSV
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

        # Convert selected RGB color to HSV
        selected_color_np = np.uint8([[selected_color]])
        selected_color_hsv = cv2.cvtColor(selected_color_np, cv2.COLOR_RGB2HSV)[0][0]

        lower_color = np.array([selected_color_hsv[0] - 10, 100, 100])
        upper_color = np.array([selected_color_hsv[0] + 10, 255, 255])

        # Create a mask for the selected color
        mask = cv2.inRange(hsv, lower_color, upper_color)

        # Reduce noise
        mask = cv2.erode(mask, np.ones((5, 5), np.uint8), iterations=2)
        mask = cv2.dilate(mask, np.ones((7, 7), np.uint8), iterations=2)
        mask = cv2.medianBlur(mask, 7)

        # Replace the selected color areas in the image with the background
        img[np.where(mask == 255)] = background[np.where(mask == 255)]

        # Encode the frame into JPEG format
        ret, buffer = cv2.imencode('.jpg', img)
        frame = buffer.tobytes()

        # Yield the frame in the format required by the webpage
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='0.0.0.0')
