import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageDraw, ImageTk
import numpy as np
import os

GRID_SIZE = 32
PIXEL_SIZE = 20
CANVAS_SIZE = GRID_SIZE * PIXEL_SIZE

# Optimized: Store binary arrays + preview image
dataset_images = {}  # { filename: (np.array, PIL.Image) }
image_refs = []

# GUI Setup
root = tk.Tk()
root.title("AI Drawing Matcher")
root.configure(bg="black")

canvas = tk.Canvas(root, width=CANVAS_SIZE, height=CANVAS_SIZE, bg="black", highlightthickness=0)
canvas.grid(row=0, column=0, rowspan=3, padx=10, pady=10)

image = Image.new("1", (GRID_SIZE, GRID_SIZE), color=0)
draw = ImageDraw.Draw(image)
rects = [[None for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]

for y in range(GRID_SIZE):
    for x in range(GRID_SIZE):
        rects[y][x] = canvas.create_rectangle(
            x * PIXEL_SIZE, y * PIXEL_SIZE,
            (x + 1) * PIXEL_SIZE, (y + 1) * PIXEL_SIZE,
            fill="black", outline="gray"
        )

left_down = False
right_down = False
editing = True

def draw_pixel(x, y, color):
    if not editing: return
    if 0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE:
        canvas.itemconfig(rects[y][x], fill=color)
        image.putpixel((x, y), 1 if color == "white" else 0)

def on_click(event):
    global left_down, right_down
    x, y = event.x // PIXEL_SIZE, event.y // PIXEL_SIZE
    if event.num == 1:
        left_down = True
        draw_pixel(x, y, "white")
    elif event.num == 3:
        right_down = True
        draw_pixel(x, y, "black")

def on_release(event):
    global left_down, right_down
    left_down = right_down = False

def on_motion(event):
    x, y = event.x // PIXEL_SIZE, event.y // PIXEL_SIZE
    if left_down:
        draw_pixel(x, y, "white")
    elif right_down:
        draw_pixel(x, y, "black")

canvas.bind("<Button-1>", on_click)
canvas.bind("<Button-3>", on_click)
canvas.bind("<B1-Motion>", on_motion)
canvas.bind("<B3-Motion>", on_motion)
canvas.bind("<ButtonRelease-1>", on_release)
canvas.bind("<ButtonRelease-3>", on_release)

# Load dataset and convert to binary numpy arrays
def load_dataset(folder="dataset"):
    for subdir in os.listdir(folder):
        subpath = os.path.join(folder, subdir)
        if os.path.isdir(subpath):
            for file in os.listdir(subpath):
                if file.lower().endswith(".png"):
                    path = os.path.join(subpath, file)
                    try:
                        img = Image.open(path).convert("L").resize((GRID_SIZE, GRID_SIZE))
                        bw = img.point(lambda x: 255 if x > 127 else 0, mode="1")
                        arr = np.array(bw).astype(np.uint8) // 255
                        dataset_images[file] = (arr, bw.convert("RGB"))
                    except Exception as e:
                        print(f"Failed to load {file}: {e}")

# Compare pixel-wise
def compare_images(user_img, dataset):
    user_arr = np.array(user_img).astype(np.uint8)
    matches = []
    for name, (arr, pil_img) in dataset.items():
        likelihood = np.sum(user_arr == arr) / (GRID_SIZE * GRID_SIZE) * 100
        matches.append((name, likelihood, pil_img))
    matches.sort(key=lambda x: -x[1])
    return matches[:2]

# Tierlist image area
tierlist_frame = tk.Frame(root, bg="black")
tierlist_frame.grid(row=0, column=1, padx=10, pady=10, sticky="n")

tierlist_labels = [tk.Label(tierlist_frame, bg="black") for _ in range(2)]
for lbl in tierlist_labels:
    lbl.pack(pady=10)

def update_tierlist(matches):
    global image_refs
    image_refs.clear()
    for i, (name, percent, img) in enumerate(matches):
        resized = img.resize((GRID_SIZE * 4, GRID_SIZE * 4), Image.NEAREST)
        tk_img = ImageTk.PhotoImage(resized)
        tierlist_labels[i].config(
            image=tk_img,
            text=f"{i+1}. {name} - {percent:.2f}%",
            compound="top",
            fg="white",
            font=("Courier", 10)
        )
        tierlist_labels[i].image = tk_img
        image_refs.append(tk_img)

# Button actions
def send_image():
    global editing
    if not editing: return
    editing = False
    matches = compare_images(image, dataset_images)
    update_tierlist(matches)

def clear_canvas():
    global editing, image, draw
    editing = True
    image = Image.new("1", (GRID_SIZE, GRID_SIZE), color=0)
    draw = ImageDraw.Draw(image)
    for y in range(GRID_SIZE):
        for x in range(GRID_SIZE):
            canvas.itemconfig(rects[y][x], fill="black")
    for lbl in tierlist_labels:
        lbl.config(image="", text="")
    image_refs.clear()

# Buttons
btn_frame = tk.Frame(root, bg="black")
btn_frame.grid(row=1, column=1, pady=5)

tk.Button(btn_frame, text="Send", command=send_image, bg="#222", fg="white", width=10).pack(pady=5)
tk.Button(btn_frame, text="Clear", command=clear_canvas, bg="#222", fg="white", width=10).pack(pady=5)

# Load dataset and launch
load_dataset("dataset")
root.mainloop()
