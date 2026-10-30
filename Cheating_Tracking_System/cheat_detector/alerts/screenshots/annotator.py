
import cv2
import datetime
from pathlib import Path
import numpy as np


def annotate_and_screenshot(frame, detections, cheating_ids, db_handler):

    annotated = frame.copy()

    if detections.tracker_id is None:
        return annotated

    details_list = detections.data.get(
        "alert_details",
        [None] * len(detections.tracker_id)
    )

    screenshot_dir = Path(__file__).resolve().parent
    screenshot_dir.mkdir(parents=True, exist_ok=True)

    for i, tracker_id in enumerate(detections.tracker_id):

        if tracker_id is None or not np.isfinite(tracker_id):
            continue

        tracker_id = int(tracker_id)

        x1, y1, x2, y2 = map(int, detections.xyxy[i])

        is_suspicious = tracker_id in cheating_ids

        color = (0, 0, 255) if is_suspicious else (0, 180, 0)

        label = (
            f"ID {tracker_id} - SUSPICIOUS HEAD TURN"
            if is_suspicious
            else f"ID {tracker_id}"
        )

        cv2.rectangle(
            annotated,
            (x1, y1),
            (x2, y2),
            color,
            2
        )

        cv2.putText(
            annotated,
            label,
            (x1, max(y1 - 10, 20)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            color,
            2
        )

        if is_suspicious:

            details = details_list[i] if i < len(details_list) else None

            if details is None:
                behavior = "Repeated head turn"
                confidence = 0.0
            else:
                behavior = details["behavior"]
                confidence = details["confidence"]

            timestamp = datetime.datetime.now().strftime(
                "%Y%m%d_%H%M%S_%f"
            )

            screenshot_path = screenshot_dir / (
                f"alert_{tracker_id}_{timestamp}.jpg"
            )

            cv2.imwrite(str(screenshot_path), annotated)

            db_handler.save_alert(
                student_id=str(tracker_id),
                behavior=behavior,
                confidence=float(confidence),
                screenshot_path=str(screenshot_path)
            )

    return annotated
