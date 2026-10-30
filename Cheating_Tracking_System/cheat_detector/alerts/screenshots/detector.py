
import cv2
import numpy as np
import mediapipe as mp
import supervision as sv
from ultralytics import YOLO
from collections import defaultdict


model = YOLO("yolov8n.pt")
tracker = sv.ByteTrack()

face_mesh = mp.solutions.face_mesh.FaceMesh(
    static_image_mode=False,
    max_num_faces=20,
    refine_landmarks=False,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

FACE_POINTS = [1, 152, 33, 263, 61, 291]

MODEL_POINTS = np.array([
    (0.0, 0.0, 0.0),
    (0.0, -330.0, -65.0),
    (-225.0, 170.0, -135.0),
    (225.0, 170.0, -135.0),
    (-150.0, -150.0, -125.0),
    (150.0, -150.0, -125.0)
], dtype=np.float64)

student_states = defaultdict(lambda: {
    "calibration": [],
    "baseline": None,
    "turn_frames": 0,
    "cooldown": 0
})


def estimate_head_yaw(face_landmarks, width, height):

    image_points = np.array([
        (
            face_landmarks.landmark[index].x * width,
            face_landmarks.landmark[index].y * height
        )
        for index in FACE_POINTS
    ], dtype=np.float64)

    focal_length = width

    camera_matrix = np.array([
        [focal_length, 0, width / 2],
        [0, focal_length, height / 2],
        [0, 0, 1]
    ], dtype=np.float64)

    distortion = np.zeros((4, 1))

    success, rotation_vector, translation_vector = cv2.solvePnP(
        MODEL_POINTS,
        image_points,
        camera_matrix,
        distortion,
        flags=cv2.SOLVEPNP_ITERATIVE
    )

    if not success:
        return None

    rotation_matrix, _ = cv2.Rodrigues(rotation_vector)

    angles = cv2.RQDecomp3x3(rotation_matrix)[0]

    yaw = float(angles[1])

    return yaw


def process_frame(frame):

    height, width = frame.shape[:2]

    
    results = model(
        frame,
        classes=[0],
        conf=0.35,
        verbose=False
    )[0]

    detections = sv.Detections.from_ultralytics(results)

    
    detections = tracker.update_with_detections(detections)

    if detections.tracker_id is None or len(detections) == 0:
        return detections, []

    
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    face_results = face_mesh.process(rgb_frame)

    if not face_results.multi_face_landmarks:
        return detections, []

    
    person_yaws = {}

    for face in face_results.multi_face_landmarks:

        nose = face.landmark[1]

        face_x = int(nose.x * width)
        face_y = int(nose.y * height)

        for i, box in enumerate(detections.xyxy):

            x1, y1, x2, y2 = map(int, box)
            if x1 <= face_x <= x2 and y1 <= face_y <= y2:

                tracker_id = int(detections.tracker_id[i])

                yaw = estimate_head_yaw(face, width, height)

                if yaw is not None:
                    person_yaws[tracker_id] = yaw

                break

    suspicious_ids = []
    alert_details = {}

    for i, tracker_id in enumerate(detections.tracker_id):

        tracker_id = int(tracker_id)

        state = student_states[tracker_id]

        if state["cooldown"] > 0:
            state["cooldown"] -= 1

        if tracker_id not in person_yaws:
            continue

        yaw = person_yaws[tracker_id]

        
        if state["baseline"] is None:

            state["calibration"].append(yaw)

            if len(state["calibration"]) >= 30:

                state["baseline"] = float(
                    np.median(state["calibration"])
                )

                state["calibration"] = []

            continue

        difference = yaw - state["baseline"]

        
        if abs(difference) > 25:
            state["turn_frames"] += 1
        else:
            state["turn_frames"] = 0

       
        if (
            state["turn_frames"] >= 25
            and state["cooldown"] == 0
        ):

            direction = "left" if difference < 0 else "right"

            suspicious_ids.append(tracker_id)

            alert_details[tracker_id] = {
                "behavior": f"Repeated head turn ({direction})",
                "confidence": min(
                    0.99,
                    0.50 + abs(difference) / 100
                )
            }

            state["cooldown"] = 180
            state["turn_frames"] = 0

    detections.data["alert_details"] = [
        alert_details.get(int(tid), None)
        for tid in detections.tracker_id
    ]

    return detections, suspicious_ids
