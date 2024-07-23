import tkinter as tk
from tkinter import messagebox
import requests
from PIL import Image, ImageTk
import io
import cv2

# Server URL
SERVER_URL = "http://127.0.0.1:5000"

# Initialize the main window
root = tk.Tk()
root.title("Client Application")

# Canvas setup
canvas = tk.Canvas(root, width=500, height=500)
canvas.pack()

# Store the positions of the red object and blue objects
red_object_coords = []
blue_objects = []

# Function to fetch and update the canvas
def update_canvas():
    response = requests.get(f"{SERVER_URL}/canvas")
    if response.status_code == 200:
        image_data = response.content
        image = Image.open(io.BytesIO(image_data))
        photo = ImageTk.PhotoImage(image)
        canvas.create_image(0, 0, anchor=tk.NW, image=photo)
        canvas.image = photo
    else:
        messagebox.showerror("Error", "Failed to fetch canvas")

# Function to fetch object positions
def fetch_object_positions():
    global red_object_coords, blue_objects
    response = requests.get(f"{SERVER_URL}/objects")
    if response.status_code == 200:
        data = response.json()
        red_object_coords = data["red_object_coords"]
        blue_objects = data["blue_objects"]
    else:
        messagebox.showerror("Error", "Failed to fetch object positions")

# Function to move the red object
def move_object(direction):
    url = f"{SERVER_URL}/move"
    data = {"direction": direction}
    response = requests.post(url, json=data)
    if response.status_code == 200:
        fetch_object_positions()
        update_canvas()
    else:
        messagebox.showerror("Error", "Failed to move object")

# Function to take a picture
def take_picture(obj_position):
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        messagebox.showerror("Error", "Failed to open camera")
        return
    
    ret, frame = cap.read()
    if ret:
        cap.release()
        cv2.destroyAllWindows()
        file_path = "capture.jpg"
        cv2.imwrite(file_path, frame)
        with open(file_path, "rb") as img_file:
            response = requests.post(f"{SERVER_URL}/upload?object_pos={obj_position}", files={"image": img_file})
            if response.status_code == 200:
                messagebox.showinfo("Success", "Image uploaded successfully")
                fetch_object_positions()  # Update the positions after removing the blue object
                update_canvas()  # Update the canvas to show the new state
            else:
                messagebox.showerror("Error", "Failed to upload image")
    else:
        messagebox.showerror("Error", "Failed to capture image")

# Key press event handler
def on_key_press(event):
    if event.keysym in ["Up", "Down", "Left", "Right"]:
        move_object(event.keysym.lower())
    
    if event.keysym == "Return":
        overlapping_obj = is_overlapping()
        if overlapping_obj:
            take_picture(overlapping_obj)

# Function to check for overlap
def is_overlapping():
    global red_object_coords, blue_objects
    fetch_object_positions()  # Ensure we have the latest positions
    for blue_object in blue_objects:
        if red_object_coords[0] < blue_object[2] and red_object_coords[2] > blue_object[0] and red_object_coords[1] < blue_object[3] and red_object_coords[3] > blue_object[1]:
            return blue_object
    return None

# Bind key press event
root.bind("<KeyPress>", on_key_press)

# Function to reset the canvas
def reset_canvas():
    response = requests.post(f"{SERVER_URL}/reset", json={"num_objects": 3})
    if response.status_code == 200:
        fetch_object_positions()
        update_canvas()
    else:
        messagebox.showerror("Error", "Failed to reset canvas")

reset_button = tk.Button(root, text="Reset", command=reset_canvas)
reset_button.pack()

# Initialize the canvas with blue objects
def initialize_canvas():
    response = requests.post(f"{SERVER_URL}/initialize", json={"num_objects": 3})
    if response.status_code == 200:
        fetch_object_positions()
        update_canvas()
    else:
        messagebox.showerror("Error", "Failed to initialize canvas")

# Initial canvas update and object fetch
initialize_canvas()

root.mainloop()
