# Creating a penalty system based on violation events
# Each violation event will have a certain point value and multiplier
# The penalty score for an exam session will be calculated based on the violation events that occurred during that instance of the exam session
# The state of the exam session will also be updated based on the penalty score (e.g., Clear, Warning, Flagged, Terminated)

from enum import Enum

#Violation Categories

class ViolationType(str, Enum):
    VISUAL = "visual"
    AUDIO = "audio"
    SYSTEM = "system"
    INPUT = "input"
    NETWORK = "network"

#Severity Levels

class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

#Full Penalty Matrix

PENALTY_MATRIX = {
    #Visual Violations
    "face_not_visible":{
        "points": 8,
        "category": ViolationType.VISUAL,
        "severity": Severity.MEDIUM,
        "detection": "MediaPipe face detection",
        "description": "Face not visible in frame",
        "student_alert": "Your Face is not visible, Please adjust the camera or lighting"
    },

    "face_absent":{
        "points": 20,
        "category": ViolationType.VISUAL,
        "severity": Severity.HIGH,
        "detection": "Continuous face tracking",
        "description": "Face absent from frame for >10 seconds",
        "student_alert": "You have been away from the camera. Please return to your seat."
    },

    "multiple_faces":{
        "points": 25,
        "category": ViolationType.VISUAL,
        "severity": Severity.HIGH,
        "detection": "Face Count in Frame",
        "description": "Multiple faces detected in frame",
        "student_alert": None
    },

    "gaze_away":{
        "points": 5,
        "category": ViolationType.VISUAL,
        "severity": Severity.LOW,
        "detection": "Gaze estimation model",
        "description": "Gaze away from screen",
        "student_alert": "Please keep your eyes on the screen"
    },

    "head_turned": {
        "points": 10,
        "category": ViolationType.VISUAL,
        "severity": Severity.MEDIUM,
        "detection": "Head pose estimation",
        "description": "Head turned > 45 degrees repeatedly",
        "student_alert": "Please look at the screen"
    },

    "looking_down": {
        "points": 8,
        "category": ViolationType.VISUAL,
        "severity": Severity.MEDIUM,
        "detection": "Head pose — pitch angle",
        "description": "Looking downward — possibly reading notes",
        "student_alert": "Please look at the screen"
    },

    "identity_mismatch": {
        "points": 50,
        "category": ViolationType.VISUAL,
        "severity": Severity.CRITICAL,
        "detection": "Face embedding comparison",
        "description": "Identity mismatch — face changed from registered photo",
        "student_alert": None
    },

    "camera_blocked": {
        "points": 20,
        "category": ViolationType.VISUAL,
        "severity": Severity.HIGH,
        "detection": "MediaStream track state",
        "description": "Camera disconnected or covered mid-exam",
        "student_alert": "The camera appears to be blocked or disconnected"
    },

    "liveness_fail_no_blink": {
        "points": 35,
        "category": ViolationType.VISUAL,
        "severity": Severity.HIGH,
        "detection": "Eye Aspect Ratio — MediaPipe Face Mesh landmarks",
        "description": "No blink detected for 90+ seconds — possible static image or video loop",
        "student_alert": None
    },

    "liveness_fail_robotic_blink": {
        "points": 50,
        "category": ViolationType.VISUAL,
        "severity": Severity.CRITICAL,
        "detection": "Blink interval regularity analysis",
        "description": "Blink pattern is unnaturally regular — possible synthetic video feed",
        "student_alert": None
    },

    # ── Audio Violations ──────────────────────────────────────────
    "voice_detected": {
        "points": 10,
        "category": ViolationType.AUDIO,
        "severity": Severity.MEDIUM,
        "detection": "Voice Activity Detection (VAD)",
        "description": "Voice or speech detected",
        "student_alert": None
    },
    "multiple_voices": {
        "points": 25,
        "category": ViolationType.AUDIO,
        "severity": Severity.HIGH,
        "detection": "Speaker diarization",
        "description": "Multiple voices detected — possible assistance",
        "student_alert": None
    },
    "microphone_muted": {
        "points": 10,
        "category": ViolationType.AUDIO,
        "severity": Severity.MEDIUM,
        "detection": "WebAudio API track state",
        "description": "Microphone muted or disconnected",
        "student_alert": "The microphone seems to be muted or disconnected."
    },

    # ── System Violations ─────────────────────────────────────────
    "tab_switch": {
        "points": 10,
        "category": ViolationType.SYSTEM,
        "severity": Severity.MEDIUM,
        "detection": "visibilitychange event",
        "description": "Tab switched or window unfocused",
        "student_alert": "Tab switching not allowed during the exam."
    },

    "keyboard_shortcut": {
        "points": 8,
        "category": ViolationType.SYSTEM,
        "severity": Severity.MEDIUM,
        "detection": "keydown event intercept",
        "description": "Keyboard shortcut attempt (Alt+Tab etc.)",
        "student_alert": None
    },

    "print_screen": {
        "points": 10,
        "category": ViolationType.SYSTEM,
        "severity": Severity.MEDIUM,
        "detection": "keydown PrintScreen",
        "description": "Print screen attempted",
        "student_alert": None
    },

    "screen_share": {
        "points": 40,
        "category": ViolationType.SYSTEM,
        "severity": Severity.CRITICAL,
        "detection": "getDisplayMedia API check",
        "description": "Screen sharing detected",
        "student_alert": None
    },

    "devtools_open": {
        "points": 15,
        "category": ViolationType.SYSTEM,
        "severity": Severity.HIGH,
        "detection": "Window size difference heuristic",
        "description": "Browser developer tools opened",
        "student_alert": None
    },

    # ── Input Violations ──────────────────────────────────────────
    "copy_attempt": {
        "points": 5,
        "category": ViolationType.INPUT,
        "severity": Severity.LOW,
        "detection": "copy event listener",
        "description": "Copy attempt (Ctrl+C)",
        "student_alert": "Copy is not permitted for the exam"
    },

    "paste_attempt": {
        "points": 5,
        "category": ViolationType.INPUT,
        "severity": Severity.LOW,
        "detection": "paste event listener",
        "description": "Paste attempt (Ctrl+V)",
        "student_alert": "Paste is not permitted for the exam"
    },

    "right_click": {
        "points": 3,
        "category": ViolationType.INPUT,
        "severity": Severity.LOW,
        "detection": "contextmenu event",
        "description": "Right-click context menu opened",
        "student_alert": "Right click is disabled for this exam"
    },

    "fast_submission": {
        "points": 5,
        "category": ViolationType.INPUT,
        "severity": Severity.LOW,
        "detection": "Time-on-question analysis",
        "description": "Suspiciously fast answer submission",
        "student_alert": None
    },

    "typing_anomaly": {
        "points": 15,
        "category": ViolationType.INPUT,
        "severity": Severity.MEDIUM,
        "detection": "Keystroke dynamics ML",
        "description": "Typing pattern anomaly — non-human rhythm",
        "student_alert": None
    },

    "long_idle": {
        "points": 5,
        "category": ViolationType.INPUT,
        "severity": Severity.LOW,
        "detection": "Activity timeout monitor",
        "description": "Long idle period — no input for > 5 minutes",
        "student_alert": None
    },

    # ── Network Violations ────────────────────────────────────────
    "vpn_detected": {
        "points": 25,
        "category": ViolationType.NETWORK,
        "severity": Severity.HIGH,
        "detection": "IP geo anomaly + WebRTC leak",
        "description": "VPN or proxy detected",
        "student_alert": None
    },
    
    "second_device": {
        "points": 50,
        "category": ViolationType.NETWORK,
        "severity": Severity.CRITICAL,
        "detection": "Concurrent session token check",
        "description": "Second device detected on same session",
        "student_alert": None
    },

    # ── Object Detection Violations ───────────────────────────────────
    "phone_detected": {
        "points":       30,
        "category":     ViolationType.VISUAL,
        "severity":     Severity.HIGH,
        "detection":    "YOLO object detection",
        "description":  "Mobile phone detected in frame",
        "student_alert": None
    },

    "earphone_detected": {
        "points":       25,
        "category":     ViolationType.VISUAL,
        "severity":     Severity.HIGH,
        "detection":    "YOLO object detection",
        "description":  "Earphones or headset detected in frame",
        "student_alert": None
    },

    "book_detected": {
        "points":       20,
        "category":     ViolationType.VISUAL,
        "severity":     Severity.HIGH,
        "detection":    "YOLO object detection",
        "description":  "Book or printed material detected in frame",
        "student_alert": "Book is not permitted in the exam."
    },

    "second_keyboard_detected": {
        "points":       25,
        "category":     ViolationType.VISUAL,
        "severity":     Severity.HIGH,
        "detection":    "YOLO object detection",
        "description":  "Second keyboard detected — possible second device",
        "student_alert": None
    },

    "second_monitor_detected": {
        "points":       35,
        "category":     ViolationType.VISUAL,
        "severity":     Severity.HIGH,
        "detection":    "YOLO object detection",
        "description":  "Second monitor or screen detected in background",
        "student_alert": None
    },

    "person_behind_detected": {
        "points":       40,
        "category":     ViolationType.VISUAL,
        "severity":     Severity.CRITICAL,
        "detection":    "YOLO person detection",
        "description":  "Another person detected standing behind the student",
        "student_alert": "Please stay in a isolated room for the exam"
    }
}

# Simple Points Lookup
PENALTY_POINTS = {
    event: data["points"] 
    for event, data in PENALTY_MATRIX.items()
}

#state descriptions

def get_state(score: int) -> str:
    if score <= 0:
        return "CLEAR"
    elif score <= 30:
        return "CAUTION"
    elif score <= 60:
        return "WARNING"
    elif score <= 85:
        return "ALERT"
    elif score <= 99:
        return "CRITICAL"
    else:
        return "TERMINATED"
    

# State Descriptions

STATE_ACTIONS = {
    "CLEAR": {
        "face_check_interval_secs": 10,
        "student_message":          None,
        "invigilator_alert":        False,
        "exam_paused":              False,
        "screenshot_interval_secs": None,
        "description":              "Normal exam flow. Background logging only."
    },
    "CAUTION": {
        "face_check_interval_secs": 5,
        "student_message":          "Please stay focused on your exam.",
        "invigilator_alert":        False,    # yellow indicator on dashboard
        "exam_paused":              False,
        "screenshot_interval_secs": None,
        "description":              "Silent toast warning. Check frequency increased."
    },
    "WARNING": {
        "face_check_interval_secs": 5,
        "student_message":          "Warning: Multiple violations detected. Your exam is being reviewed.",
        "invigilator_alert":        True,     # push notification
        "exam_paused":              False,
        "screenshot_interval_secs": 30,
        "description":              "Full-screen modal. Invigilator notified. Auto-screenshot every 30s."
    },
    "ALERT": {
        "face_check_interval_secs": 5,
        "student_message":          "Proctoring Review in Progress. Please wait.",
        "invigilator_alert":        True,     # must click Resume
        "exam_paused":              True,     # timer continues but input locked
        "screenshot_interval_secs": 10,
        "description":              "Exam paused. Invigilator must click Resume. All events get 1.5x multiplier."
    },
    "CRITICAL": {
        "face_check_interval_secs": 5,
        "student_message":          "Your exam has been paused for manual review by an Admin.",
        "invigilator_alert":        True,     # escalated to Admin
        "exam_paused":              True,     # locked until manual release
        "screenshot_interval_secs": 5,
        "description":              "Locked. Admin must manually review and release."
    },
    "TERMINATED": {
        "face_check_interval_secs": None,
        "student_message":          "Your exam has been permanently terminated due to integrity violations.",
        "invigilator_alert":        True,
        "exam_paused":              True,
        "screenshot_interval_secs": None,
        "description":              "Permanent shutdown. Token blacklisted. Evidence bundle auto-sent."
    }
}


# Score Engine 
DECAY_RATE = 1 # 1 decay point per half minute
DECAY_INTERVAL_SECS = 30
FLOOR_SCORE = 0

COOLDOWN_SECS = 3 #same event cannot fire more than once every 3 seconds to prevent rapid point accumulation from a single source
STREAK_WINDOWS_SECS = 60 # if multiple violations occur within this window, a streak multiplier is applied to increase the penalty points for subsequent violations in the streak
STREAK_MULTIPLIER_TIERS=[
    (1,1.0),
    (3,1.5),
    (6,2.0)
]

STATE_MULTIPLIERS= {
    "CLEAR":      1.0,
    "CAUTION":    1.0,
    "WARNING":    1.0,
    "ALERT":      1.5,
    "CRITICAL":   2.0,
    "TERMINATED": 1.0
}

STATE_FLOOR_SCORE = {
    "CLEAR": 0,
    "CAUTION": 1,
    "WARNING": 31,
    "ALERT": 61,
    "CRITICAL": 86,
    "TERMINATED": 100
}

def get_streak_multipliers(streak_count: int)-> float:
    multiplier= 1.0
    for threshold, value in STREAK_MULTIPLIER_TIERS:
        if streak_count >= threshold:
            multiplier= value
    return multiplier

def get_combined_multiplier(streak_count:int, state:str) -> float:
    streak_m = get_streak_multipliers(streak_count)
    state_m = STATE_MULTIPLIERS[state]
    """
    So, working on additive multipliers making the penalties a bit harsh, instead of the student trying to get away with cheating,
    Multiplier for state + multiplier for violation streak - 1.0 as both state and streak start with 1, so it doubles and rounding off to 2 decimal places.
    """
    return round(streak_m + state_m - 1.0, 2)

DEESCALATION_MIN_INTERVAL = 300 # if no violations occur within this window, the penalty score is reduced by a certain amount to allow for recovery

# Get Full Violation Info

def get_violation_info(event_type: str) -> dict:
    if event_type not in PENALTY_MATRIX:
        return None
    return PENALTY_MATRIX[event_type]

#Get All Violations By categories

def get_violations_by_category(category: ViolationType) -> dict:
    return{
        k: v for k, v in PENALTY_MATRIX.items() 
        if v["category"] == category
    }

# Get all Critical Violations

def get_critical_violations() -> dict:
    return {
        k: v for k, v in PENALTY_MATRIX.items() 
        if v["severity"] == Severity.CRITICAL
    }