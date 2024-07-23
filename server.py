from flask import Flask, request, jsonify, send_file
import os
import ast
import cv2
import numpy as np
from PIL import Image, ImageDraw
import random

app = Flask(__name__)

# Red object coordinates
red_object_coords = [340, 180, 360, 200]
canvas_size = (500, 500)
blue_objects = []
uploaded_images = []  # List to store paths of uploaded images

def num_gen_random():
    while True:
        yield random.randint(0, 500)

num_gen_random = num_gen_random()

# Create an empty canvas with the red object and blue objects
def create_canvas():
    image = Image.new("RGB", canvas_size, "white")
    draw = ImageDraw.Draw(image)
    draw.rectangle(red_object_coords, fill="red")
    for pos in blue_objects:
        draw.rectangle(pos, fill="blue")
    if not blue_objects:  # Only render images when no blue objects are left
        for img_path in uploaded_images:
            img = Image.open(img_path)
            img.thumbnail((50, 50))
            image.paste(img, (random.randint(0, 450), random.randint(0, 450)))
    return image

# Move red object function
def move_red_object(direction):
    global red_object_coords
    step = 20
    if direction == "up":
        red_object_coords[1] = max(0, red_object_coords[1] - step)
        red_object_coords[3] = max(step, red_object_coords[3] - step)
    elif direction == "down":
        red_object_coords[1] = min(canvas_size[1] - step, red_object_coords[1] + step)
        red_object_coords[3] = min(canvas_size[1], red_object_coords[3] + step)
    elif direction == "left":
        red_object_coords[0] = max(0, red_object_coords[0] - step)
        red_object_coords[2] = max(step, red_object_coords[2] - step)
    elif direction == "right":
        red_object_coords[0] = min(canvas_size[0] - step, red_object_coords[0] + step)
        red_object_coords[2] = min(canvas_size[0], red_object_coords[2] + step)

# Function to create random blue objects
def create_random_blue_objects(num_objects):
    global blue_objects
    blue_objects = []
    while len(blue_objects) < num_objects:
        x = random.randint(0, canvas_size[0] - 20)
        y = random.randint(0, canvas_size[1] - 20)
        new_object = [x, y, x + 20, y + 20]
        
        # Ensure new object does not overlap with red object
        if not is_overlapping(new_object, red_object_coords):
            blue_objects.append(new_object)

def is_overlapping(rect1, rect2):
    if rect1[0] < rect2[2] and rect1[2] > rect2[0] and rect1[1] < rect2[3] and rect1[3] > rect2[1]:
        return True
    return False

# Endpoint to initialize canvas with blue objects
@app.route("/initialize", methods=["POST"])
def initialize():
    num_objects = request.json.get("num_objects", 5)
    create_random_blue_objects(num_objects)
    return jsonify({"message": "Canvas initialized with blue objects"})

# Endpoint to move the red object
@app.route("/move", methods=["POST"])
def move():
    direction = request.json.get("direction")
    move_red_object(direction)
    return jsonify({"message": "Red object moved"})

# Endpoint to get the current canvas
@app.route("/canvas", methods=["GET"])
def get_canvas():
    image = create_canvas()
    file_path = "canvas.png"
    image.save(file_path)
    return send_file(file_path, mimetype='image/png')

# Endpoint to get object positions
@app.route("/objects", methods=["GET"])
def get_objects():
    return jsonify({"red_object_coords": red_object_coords, "blue_objects": blue_objects})


def is_aruco_code(path):
    image = cv2.imread(path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_6X6_250)
    parameters = cv2.aruco.DetectorParameters_create()
    corners, ids, rejectedImgPoints = cv2.aruco.detectMarkers(gray, aruco_dict, parameters=parameters)
    return ids is not None

# Endpoint to upload and validate images
@app.route("/upload", methods=["POST"])
def upload_image():
    global blue_objects, uploaded_images
    try:
        file = request.files["image"]
        num = next(num_gen_random)
        file_name = f"{num}_{file.filename}"
        file_path = os.path.join("uploads", file_name)
        file.save(file_path)

        uploaded_images.append(file_path)
        object_position_str = request.args.get("object_pos")
        object_position = ast.literal_eval(object_position_str)
        index_pos = blue_objects.index(object_position)
        blue_objects.pop(index_pos)

        #if is_aruco_code(file_path):
         #   uploaded_images.append(file_path)
          

           # return jsonify({"message": "Image uploaded successfully"}), 200
        #else:
         #   return jsonify({"message": "Invalid image"}), 400
        return jsonify({"message": "Image uploaded successfully"}), 200
    except Exception as e:
        print(e)
        return jsonify({"message": "  No aruco found"}), 400

# Endpoint to reset the canvas
@app.route("/reset", methods=["POST"])
def reset_canvas():
    try:    
      global uploaded_images
      num_objects = request.json.get("num_objects")
      uploaded_images = []  # Clear uploaded images
      create_random_blue_objects(num_objects)
      return jsonify({"message": "Canvas reset"}), 200
  
    except Exception as e:
        print(e)
        return jsonify({"message": "Failed to reset canvas"}), 400

if __name__ == "__main__":
    if not os.path.exists("uploads"):
        os.makedirs("uploads")
    app.run(debug=True)
