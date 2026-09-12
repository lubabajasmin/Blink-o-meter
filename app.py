import tkinter as tk
from tkinter import messagebox
import cv2
import mediapipe as mp
import math
import time

# ============================================================
# SETTINGS
# ============================================================

EAR_THRESHOLD = 0.21
CONSECUTIVE_FRAMES = 2

# Pastel colours
BG = "#FFF8FC"
PINK = "#FFD6E7"
PINK_DARK = "#EFA8C5"
LAVENDER = "#E8DEFF"
BLUE = "#DDF4FF"
MINT = "#DDF5E5"
YELLOW = "#FFF0C9"
TEXT = "#51445F"
WHITE = "#FFFFFF"
GREEN = "#83CFA4"

# ============================================================
# MEDIAPIPE
# ============================================================

BaseOptions = mp.tasks.BaseOptions
FaceLandmarker = mp.tasks.vision.FaceLandmarker
FaceLandmarkerOptions = mp.tasks.vision.FaceLandmarkerOptions
RunningMode = mp.tasks.vision.RunningMode

LEFT_EYE = [362, 385, 387, 263, 373, 380]
RIGHT_EYE = [33, 160, 158, 133, 153, 144]


def distance(p1, p2):
    return math.sqrt(
        (p1.x - p2.x) ** 2 +
        (p1.y - p2.y) ** 2
    )


def eye_aspect_ratio(landmarks, eye):
    p1 = landmarks[eye[0]]
    p2 = landmarks[eye[1]]
    p3 = landmarks[eye[2]]
    p4 = landmarks[eye[3]]
    p5 = landmarks[eye[4]]
    p6 = landmarks[eye[5]]

    vertical1 = distance(p2, p6)
    vertical2 = distance(p3, p5)
    horizontal = distance(p1, p4)

    return (vertical1 + vertical2) / (2.0 * horizontal)


# ============================================================
# MAIN WINDOW
# ============================================================

root = tk.Tk()
root.title("Blink-O-Meter")
root.geometry("1200x760")
root.configure(bg=BG)
root.resizable(False, False)

camera = None
landmarker = None

blink_count = 0
closed_frames = 0
start_time = None
running = False


# ============================================================
# GRADIENT BACKGROUND
# ============================================================

canvas = tk.Canvas(
    root,
    width=1200,
    height=760,
    highlightthickness=0,
    bg=BG
)
canvas.place(x=0, y=0)


def pastel_gradient():
    steps = 760

    for i in range(steps):
        ratio = i / steps

        r = int(255 * (1 - ratio) + 248 * ratio)
        g = int(248 * (1 - ratio) + 240 * ratio)
        b = int(252 * (1 - ratio) + 255 * ratio)

        color = f"#{r:02x}{g:02x}{b:02x}"

        canvas.create_line(
            0, i,
            1200, i,
            fill=color
        )


pastel_gradient()


# ============================================================
# HEADER
# ============================================================

header = tk.Frame(
    root,
    bg=BG
)
header.place(x=45, y=25, width=1110, height=85)

tk.Label(
    header,
    text="👁 BLINK-O-METER",
    font=("Segoe UI", 28, "bold"),
    fg=TEXT,
    bg=BG
).pack(anchor="w")

tk.Label(
    header,
    text="A completely unnecessary scientific investigation ✨",
    font=("Segoe UI", 12),
    fg="#8D7C9C",
    bg=BG
).pack(anchor="w", pady=(4, 0))


# ============================================================
# CAMERA CARD
# ============================================================

camera_card = tk.Frame(
    root,
    bg=WHITE,
    highlightbackground=PINK,
    highlightthickness=3
)
camera_card.place(x=45, y=125, width=720, height=500)

tk.Label(
    camera_card,
    text="LIVE CAMERA",
    font=("Segoe UI", 13, "bold"),
    fg=TEXT,
    bg=WHITE
).place(x=25, y=18)

status_label = tk.Label(
    camera_card,
    text="● CAMERA OFF",
    font=("Segoe UI", 10, "bold"),
    fg="#B48AA0",
    bg=PINK
)
status_label.place(x=570, y=17, width=120, height=30)

camera_label = tk.Label(
    camera_card,
    bg="#F4EDF7",
    text="Camera preview\nwill appear here",
    font=("Segoe UI", 16),
    fg="#A898AF"
)
camera_label.place(x=20, y=65, width=680, height=405)


# ============================================================
# RIGHT SIDE
# ============================================================

def stat_card(parent, x, y, title, value, bg_color):

    card = tk.Frame(
        parent,
        bg=bg_color
    )
    card.place(x=x, y=y, width=335, height=105)

    tk.Label(
        card,
        text=title,
        font=("Segoe UI", 11, "bold"),
        fg=TEXT,
        bg=bg_color
    ).place(x=20, y=15)

    label = tk.Label(
        card,
        text=value,
        font=("Segoe UI", 25, "bold"),
        fg=TEXT,
        bg=bg_color
    )
    label.place(x=20, y=42)

    return label


blink_value = stat_card(
    root, 800, 125,
    "👁  BLINKS",
    "0",
    PINK
)

time_value = stat_card(
    root, 800, 245,
    "⏱  SESSION TIME",
    "00:00",
    LAVENDER
)

rate_value = stat_card(
    root, 800, 365,
    "📊  BLINK RATE",
    "0.0 / min",
    BLUE
)


# ============================================================
# USELESSNESS CARD
# ============================================================

useless_card = tk.Frame(
    root,
    bg=MINT
)
useless_card.place(x=800, y=485, width=335, height=140)

tk.Label(
    useless_card,
    text="🎀 USELESSNESS LEVEL",
    font=("Segoe UI", 11, "bold"),
    fg=TEXT,
    bg=MINT
).place(x=20, y=15)

useless_bar_bg = tk.Frame(
    useless_card,
    bg=WHITE
)
useless_bar_bg.place(x=20, y=55, width=295, height=18)

useless_bar = tk.Frame(
    useless_bar_bg,
    bg=GREEN
)
useless_bar.place(x=0, y=0, width=240, height=18)

useless_text = tk.Label(
    useless_card,
    text="82% — Impressive.",
    font=("Segoe UI", 11, "bold"),
    fg=TEXT,
    bg=MINT
)
useless_text.place(x=20, y=88)


# ============================================================
# FUNNY MESSAGE
# ============================================================

message_card = tk.Frame(
    root,
    bg=YELLOW
)
message_card.place(x=800, y=640, width=335, height=60)

message_label = tk.Label(
    message_card,
    text="Waiting for your first blink...",
    font=("Segoe UI", 10, "bold"),
    fg=TEXT,
    bg=YELLOW,
    wraplength=290
)
message_label.place(x=15, y=10, width=305, height=40)


# ============================================================
# BUTTONS
# ============================================================

def start_camera():

    global camera
    global landmarker
    global blink_count
    global closed_frames
    global start_time
    global running

    if running:
        return

    camera = cv2.VideoCapture(0)

    if not camera.isOpened():
        messagebox.showerror(
            "Camera Error",
            "Could not access the webcam."
        )
        return

    options = FaceLandmarkerOptions(
        base_options=BaseOptions(
            model_asset_path="face_landmarker.task"
        ),
        running_mode=RunningMode.IMAGE,
        num_faces=1,
        min_face_detection_confidence=0.5,
        min_face_presence_confidence=0.5,
        min_tracking_confidence=0.5
    )

    landmarker = FaceLandmarker.create_from_options(options)

    blink_count = 0
    closed_frames = 0
    start_time = time.time()
    running = True

    status_label.config(
        text="● LIVE",
        bg=MINT,
        fg="#4C9B70"
    )

    message_label.config(
        text="Camera is watching... 👀"
    )

    update_camera()


def stop_camera():

    global camera
    global landmarker
    global running

    running = False

    if camera:
        camera.release()
        camera = None

    if landmarker:
        landmarker.close()
        landmarker = None

    status_label.config(
        text="● CAMERA OFF",
        bg=PINK,
        fg="#B48AA0"
    )

    message_label.config(
        text="Session stopped. Productivity gained: 0% 😌"
    )


start_button = tk.Button(
    root,
    text="▶  START BLINKING",
    command=start_camera,
    font=("Segoe UI", 11, "bold"),
    bg=MINT,
    fg=TEXT,
    activebackground="#C9EBD5",
    activeforeground=TEXT,
    relief="flat",
    bd=0,
    cursor="hand2"
)
start_button.place(x=45, y=650, width=220, height=48)


stop_button = tk.Button(
    root,
    text="■  STOP",
    command=stop_camera,
    font=("Segoe UI", 11, "bold"),
    bg=PINK,
    fg=TEXT,
    activebackground="#FFC4DA",
    activeforeground=TEXT,
    relief="flat",
    bd=0,
    cursor="hand2"
)
stop_button.place(x=280, y=650, width=150, height=48)


# ============================================================
# CAMERA UPDATE
# ============================================================

def update_camera():

    global closed_frames
    global blink_count

    if not running:
        return

    success, frame = camera.read()

    if not success:
        root.after(30, update_camera)
        return

    # Mirror webcam like a normal selfie camera
    frame = cv2.flip(frame, 1)

    # Convert BGR → RGB for correct real-world colours
    rgb_frame = cv2.cvtColor(
        frame,
        cv2.COLOR_BGR2RGB
    )

    # MediaPipe image
    mp_image = mp.Image(
        image_format=mp.ImageFormat.SRGB,
        data=rgb_frame
    )

    result = landmarker.detect(mp_image)

    # Blink detection
    if result.face_landmarks:

        landmarks = result.face_landmarks[0]

        left_ear = eye_aspect_ratio(
            landmarks,
            LEFT_EYE
        )

        right_ear = eye_aspect_ratio(
            landmarks,
            RIGHT_EYE
        )

        ear = (left_ear + right_ear) / 2

        if ear < EAR_THRESHOLD:

            closed_frames += 1

        else:

            if closed_frames >= CONSECUTIVE_FRAMES:
                blink_count += 1

            closed_frames = 0

        # Draw eye points
        for index in LEFT_EYE + RIGHT_EYE:

            x = int(
                landmarks[index].x *
                frame.shape[1]
            )

            y = int(
                landmarks[index].y *
                frame.shape[0]
            )

            cv2.circle(
                frame,
                (x, y),
                3,
                (255, 170, 210),
                -1
            )

    # ========================================================
    # DISPLAY REAL CAMERA COLOURS
    # ========================================================

    display_frame = cv2.cvtColor(
        frame,
        cv2.COLOR_BGR2RGB
    )

    display_frame = cv2.resize(
        display_frame,
        (680, 405)
    )

    # PPM preserves RGB correctly in Tkinter
    success, encoded = cv2.imencode(
        ".ppm",
        display_frame
    )

    if success:

        image = tk.PhotoImage(
            data=encoded.tobytes()
        )

        camera_label.config(
            image=image,
            text=""
        )

        camera_label.image = image

    # ========================================================
    # UPDATE STATISTICS
    # ========================================================

    blink_value.config(
        text=str(blink_count)
    )

    if start_time:

        elapsed = int(
            time.time() - start_time
        )

        minutes = elapsed // 60
        seconds = elapsed % 60

        time_value.config(
            text=f"{minutes:02d}:{seconds:02d}"
        )

        if elapsed > 0:

            rate = (
                blink_count /
                (elapsed / 60)
            )

            rate_value.config(
                text=f"{rate:.1f} / min"
            )

    # Funny messages
    if blink_count == 0:
        message_label.config(
            text="Waiting for your first blink... 👀"
        )

    elif blink_count < 5:
        message_label.config(
            text="Congratulations. Your eyes work."
        )

    elif blink_count < 15:
        message_label.config(
            text="Excellent. Absolutely no reason for this app."
        )

    elif blink_count < 30:
        message_label.config(
            text="You're getting suspiciously good at blinking."
        )

    else:
        message_label.config(
            text="BLINK MASTER unlocked 🏆"
        )

    root.after(
        15,
        update_camera
    )


# ============================================================
# CLOSE WINDOW SAFELY
# ============================================================

def close_app():

    global running

    running = False

    if camera:
        camera.release()

    if landmarker:
        landmarker.close()

    root.destroy()


root.protocol(
    "WM_DELETE_WINDOW",
    close_app
)

root.mainloop()