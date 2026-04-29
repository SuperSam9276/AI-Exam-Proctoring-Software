import base64
import cv2
import numpy as np
import mediapipe as mp
from ultralytics import YOLO
import webrtcvad
import struct

mp_face_detect = mp.solutions.face_detection
mp_face_mesh = mp.solutions.face_mesh

face_detector = mp_face_detect.FaceDetection(
    model_selection=0, 
    min_detection_confidence=0.6
    )

face_mesh = mp_face_mesh.FaceMesh(
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.6,
    min_tracking_confidence=0.5,
    static_image_mode=False
    )


_face_missing_counts = {}

FACE_ABSENT_THRESHOLD = 6
# number of consecutive frames to consider face as absent


print("[detection] Face Detection and Mesh models loaded")

def decode_frame(frame_data: str) -> np.ndarray:
    try:
        frame_data = frame_data.split(",")[1] if "," in frame_data else frame_data
        image_bytes = base64.b64decode(frame_data)
        img_arr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(img_arr, cv2.IMREAD_COLOR)

        if img is not None and img.shape[0] > img.shape[1]:
            img = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
        return img
    except Exception as e:
        print(f"Error decoding frame: {e}")
        return None
    
def analyse_face(frame_data: str, session_id: str) -> list[str]:
    violations = []

    img = decode_frame(frame_data)

    if img is None:
        return ["camera_blocked"]
    
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = face_detector.process(img_rgb)
    print(f"[detection] Face detection results for session {session_id}: {len(results.detections) if results.detections else 0} faces detected")

    face_count = len(results.detections) if results.detections else 0
    if face_count > 1:
        violations.append("multiple_faces")
        print(f"[detection] Multiple faces detected for session {session_id}. Count: {face_count}") 

    if not results.detections:

        _face_missing_counts[session_id] = (_face_missing_counts.get(session_id, 0) + 1)
        
        count = _face_missing_counts[session_id]

        if count == 1:
            violations.append("face_not_visible")
            print(f"[detection] Face not visible for session {session_id}. Count: {count}")
            count = count + 1
        elif count >= FACE_ABSENT_THRESHOLD:
            violations.append("face_absent")
            print(f"[detection] Face absent for session {session_id}. Count: {count}")
            count = count + 1
        return violations
    
    #reseting count on successful detection
    _face_missing_counts[session_id] = 0

    primary_face = results.detections[0]
    confidence = primary_face.score[0]

    if confidence < 0.6:
        violations.append("face_not_visible")
        print(f"[detection] Low confidence ({confidence:.2f}) for session {session_id}")

    return violations

GAZE_THRESHOLD = 0.35
def analyse_eye_gaze(frame_data: str) -> list[str]:
    # Iris landmark indices (requires refine_landmarks=True)
    # Left eye:  iris centre=468, left corner=33, right corner=133
    # Right eye: iris centre=473, left corner=362, right corner=263

    violations = []

    img = decode_frame(frame_data)

    if img is None:
        return violations
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(img_rgb)

    if not results.multi_face_landmarks:
        return violations
    
    landmarks = results.multi_face_landmarks[0].landmark
    def get_gaze_direction(iris_center, eye_left, eye_right):
        iris_x = landmarks[iris_center].x
        left_x = landmarks[eye_left].x
        right_x = landmarks[eye_right].x
        eye_width = abs(right_x - left_x)
        
        if eye_width == 0:
            return 0.5
        
        ratio = (iris_x - left_x) / eye_width
        return ratio
    
    left_ratio = get_gaze_direction(468, 33, 133)
    right_ratio = get_gaze_direction(473, 362, 263)
    avg_ratio = (left_ratio + right_ratio) / 2

    if avg_ratio < GAZE_THRESHOLD or avg_ratio > (1 -GAZE_THRESHOLD):
        violations.append("gaze_away")
        print(f"[detection] Looking away detected. Left ratio: {left_ratio:.2f}, Right ratio: {right_ratio:.2f}, Average: {avg_ratio:.2f}")
    return violations


FACE_3D_MODEL = np.array([
    [0.0, 0.0, 0.0],        # Nose
    [0.0, -330.0, -65.0],   # Chin
    [-225.0, 170.0, -135.0], # Left eye left corner
    [225.0, 170.0, -135.0],  # Right eye right corner
    [-150.0, -150.0, -125.0], # Left Mouth corner
    [150.0, -150.0, -125.0]   # Right mouth corner
], dtype=np.float32)

FACE_2D_LANDMARKS = [1, 152, 33, 263, 61, 291] # Nose tip, Chin, Left eye left corner, Right eye right corner, Left Mouth corner, Right mouth corner

YAW_THRESHOLD = 30 # Yaw angle threshold in degrees for head turned away detection
PITCH_THRESHOLD = 20 # Pitch angle threshold in degrees for head looking down detection


def analyse_head_pose(frame_data: str) -> list[str]:
    violations = []

    img = decode_frame(frame_data)

    if img is None:
        return violations
    
    h, w = img.shape[:2]
    size = min(h, w)
    img = cv2.resize(img, (size, size))
    h,w = size, size

    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(img_rgb)

    if not results.multi_face_landmarks:
        return violations
    
    landmarks = results.multi_face_landmarks[0].landmark

    img_2d = np.array([
        [landmarks[i].x * w, landmarks[i].y * h] 
        for i in FACE_2D_LANDMARKS
    ], dtype=np.float32)

    focal_length = w

    cam_matrix = np.array([
        [focal_length, 0, w / 2],
        [0, focal_length, h / 2],
        [0, 0, 1]
    ], dtype=np.float32)

    dist_coeffs = np.zeros((4, 1))

    success, rot_vec, trans_vec = cv2.solvePnP(FACE_3D_MODEL, img_2d, cam_matrix, dist_coeffs)

    if not success:
        return violations
    
    
    rot_mat, _ = cv2.Rodrigues(rot_vec)

    angles, _, _, _, _, _ = cv2.RQDecomp3x3(rot_mat)

    pitch = angles[0]   
    yaw = angles[1]


    if abs(yaw) > YAW_THRESHOLD:
        violations.append("head_turned")
        print(f"[detection] Head turned away detected. Yaw: {yaw:.1f}°")

    if pitch < -PITCH_THRESHOLD:
        violations.append("looking_down")
        print(f"[detection] Head looking down detected. Pitch: {pitch:.1f}°")
    return violations

yolo_model = YOLO("yolov8s.pt")
print("[detection] YOLOv8 small model loaded \n")

YOLO_CONFIDENCE = 0.5

YOLO_VIOLATION_CLASSES = {
    "cell phone": "phone_detected",
    "keyboard": "second_keyboard_detected",
    "book": "book_detected",
    "tv" : "second_monitor_detected",
    "monitor": "second_monitor_detected",
    "laptop": "second_monitor_detected"
}

EARPHONE_CLASS_NAMES = {"headphones", "earphones", "earbuds", "airpods", "headset"}

ALLOWED_CLASSES = set(YOLO_VIOLATION_CLASSES.keys()) | EARPHONE_CLASS_NAMES | {"person"}

def analyse_objects(frame_data: str) -> list[str]:
    violations = set()
    person_count = 0

    img = decode_frame(frame_data)
    if img is None:
        return []
    
    results = yolo_model(img, conf=YOLO_CONFIDENCE, verbose= False)
    
    annotated = results[0].plot()
    cv2.imwrite("C:\\Swayam\\Codes\\Proctoring Software\\debug_frame.jpg", annotated)
    

    for result in results:
        for box in result.boxes:
            cls_name = yolo_model.names[int(box.cls)]

            if cls_name not in ALLOWED_CLASSES:
                continue

            if cls_name in YOLO_VIOLATION_CLASSES:
                violations.add(YOLO_VIOLATION_CLASSES[cls_name])
                print(f"[detection] Object detected: {cls_name}, Violation: {YOLO_VIOLATION_CLASSES[cls_name]}")

            if cls_name in EARPHONE_CLASS_NAMES:
                violations.add("earphone_detected")
                print(f"[detection] Earphones detected: {cls_name}")

            if cls_name == "person":
                person_count += 1
        
        if person_count >= 2:
            violations.add("person_behind_detected")
            print(f"[detection] Multiple people detected. Count: {person_count}")
    
    return list(violations)


vad = webrtcvad.Vad(2)  # Set aggressiveness mode (0-3)

SAMPLE_RATE = 16000
FRAME_MS = 30  # ms
SPEECH_THRESHOLD = 0.6  # Proportion of speech frames to consider as talking

def analyse_audio(audio_data: bytes) -> list[str]:

    violations = []

    frame_size = int(SAMPLE_RATE * FRAME_MS / 1000) * 2  # 16-bit audio
    speech_frames = 0
    total_frames = 0


    for i in range(0, len(audio_data) - frame_size, frame_size):
        frame = audio_data[i:i + frame_size]
        if len(frame) < frame_size:
            break

        try:
            is_speech = vad.is_speech(frame, SAMPLE_RATE)
            if is_speech:
                speech_frames += 1
            total_frames += 1

        except Exception as e:
            print(f"Error processing audio frame: {e}")
            continue

    if total_frames > 0:
        ratio = speech_frames / total_frames
        if ratio > SPEECH_THRESHOLD:
            violations.append("voice_detected")
            print(f"[detection] Voice detected. Speech frames: {speech_frames}, Total frames: {total_frames}, Ratio: {ratio:.2f}")
                
    return violations
    