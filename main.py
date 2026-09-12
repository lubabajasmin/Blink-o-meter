import cv2
import mediapipe as mp
import math
import time

# -----------------------------
# SETTINGS
# -----------------------------
EAR_THRESHOLD = 0.21
CONSECUTIVE_FRAMES = 2

# -----------------------------
# MEDIAPIPE SETUP
# -----------------------------
BaseOptions = mp.tasks.BaseOptions
FaceLandmarker = mp.tasks.vision.FaceLandmarker
FaceLandmarkerOptions = mp.tasks.vision.FaceLandmarkerOptions
RunningMode = mp.tasks.vision.RunningMode

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

# -----------------------------
# EYE LANDMARKS
# -----------------------------
LEFT_EYE = [362, 385, 387, 263, 373, 380]
RIGHT_EYE = [33, 160, 158, 133, 153, 144]


def eye_aspect_ratio(landmarks, eye_points, width, height):

    points = []

    for point in eye_points:
        x = int(landmarks[point].x * width)
        y = int(landmarks[point].y * height)
        points.append((x, y))

    vertical_1 = math.dist(points[1], points[5])
    vertical_2 = math.dist(points[2], points[4])
    horizontal = math.dist(points[0], points[3])

    ear = (vertical_1 + vertical_2) / (2 * horizontal)

    return ear


# -----------------------------
# CAMERA
# -----------------------------
camera = cv2.VideoCapture(0)

blink_count = 0
blink_frames = 0
start_time = time.time()

# -----------------------------
# START MEDIAPIPE
# -----------------------------
with FaceLandmarker.create_from_options(options) as face_landmarker:

    while True:

        success, frame = camera.read()

        if not success:
            print("Camera could not be opened.")
            break

        # Mirror camera
        frame = cv2.flip(frame, 1)

        height, width, _ = frame.shape

        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2RGB
        )

        # Create MediaPipe image
        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=rgb_frame
        )

        # Detect face
        result = face_landmarker.detect(mp_image)

        # -----------------------------
        # FACE FOUND
        # -----------------------------
        if result.face_landmarks:

            face_landmarks = result.face_landmarks[0]

            left_ear = eye_aspect_ratio(
                face_landmarks,
                LEFT_EYE,
                width,
                height
            )

            right_ear = eye_aspect_ratio(
                face_landmarks,
                RIGHT_EYE,
                width,
                height
            )

            ear = (left_ear + right_ear) / 2

            # -----------------------------
            # BLINK DETECTION
            # -----------------------------
            if ear < EAR_THRESHOLD:

                blink_frames += 1

            else:

                if blink_frames >= CONSECUTIVE_FRAMES:
                    blink_count += 1

                blink_frames = 0

            # Show eye ratio
            cv2.putText(
                frame,
                f"Eye Ratio: {ear:.2f}",
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2
            )

        # -----------------------------
        # BLINK RATE
        # -----------------------------
        elapsed_time = time.time() - start_time
        minutes = elapsed_time / 60

        if minutes > 0:
            blink_rate = blink_count / minutes
        else:
            blink_rate = 0

        # -----------------------------
        # DISPLAY BOX
        # -----------------------------
        cv2.rectangle(
            frame,
            (10, 60),
            (370, 200),
            (40, 40, 40),
            -1
        )

        cv2.putText(
            frame,
            f"BLINKS: {blink_count}",
            (30, 105),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 255),
            3
        )

        cv2.putText(
            frame,
            f"RATE: {blink_rate:.1f}/min",
            (30, 145),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2
        )

        cv2.putText(
            frame,
            "Press Q to quit",
            (30, 180),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (200, 200, 200),
            1
        )

        # -----------------------------
        # FUNNY MESSAGE
        # -----------------------------
        if blink_count >= 50:
            message = "BLINK MASTER!"

        elif blink_count >= 25:
            message = "Are you even looking?"

        elif blink_count >= 10:
            message = "Blink detected!"

        else:
            message = "Watching your blinks..."

        cv2.putText(
            frame,
            message,
            (20, height - 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 255, 255),
            2
        )

        # -----------------------------
        # SHOW CAMERA
        # -----------------------------
        cv2.imshow(
            "Useless Eye Blink Counter",
            frame
        )

        key = cv2.waitKey(1) & 0xFF

        if key == ord("q"):
            break


# -----------------------------
# CLOSE
# -----------------------------
camera.release()
cv2.destroyAllWindows()

print("Total blinks:", blink_count)
print("Thank you for wasting time counting your blinks!")