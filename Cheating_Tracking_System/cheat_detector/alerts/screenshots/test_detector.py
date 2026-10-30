from ultralytics import YOLO
import cv2

model = YOLO("yolov8n.pt") 

cap = cv2.VideoCapture("D:\OneDrive\Desktop\Cheating_Tracking_System\WhatsApp Video 2026-10-24 at 5.59.33 PM (1).mp4") 

ret, frame = cap.read()
if ret:
    results = model(frame)
    results[0].show() 
    print("Classes detected:", results[0].names)
else:
    print("Could not read video")

cap.release()