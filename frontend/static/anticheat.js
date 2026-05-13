//  WADJET (AI Proctor - Anti Cheat Detection(Browser Side))
//  Detects: tab_switch, keyboard_shortcut, print_screen,
//           copy_attempt, paste_attempt, right_click
//
//  Event types sent to backend must match PENALTY_MATRIX in penalty.py
//  Object detection (phone_detected, earphone_detected, book_detected,
//  second_keyboard_detected, second_monitor_detected, person_behind_detected)
//  and liveness detection (liveness_fail_no_blink, liveness_fail_robotic_blink)
//  are handled server-side via YOLO and MediaPipe — NOT here. 

const AntiCheat = (()=> {
    // Helper function to send events to the backend
    let _sessionId = null; // This should be set to the current exam session ID
    let _token = null; // This should be set to the user's auth token
    let _active = false; // Flag to track if monitoring is active

    // Sending Violations to Backend
    // event_type must be a key in PENALTY_MATRIX (penalty.py)
    // Browser-detectable events this file can send:
    //   System:  tab_switch, keyboard_shortcut, print_screen
    //   Input:   copy_attempt, paste_attempt, right_click
    
    function updateScoreDisplay(score, state) {
    const el = document.getElementById("score-display");
    if (!el) return;
    el.textContent  = state;
    el.className    = "status-value " + state.toLowerCase();
    }
    
    function showViolationAlert(message) {
    const existing = document.getElementById("ac-violation-alert");
    if (existing) existing.remove();

    const alert   = document.createElement("div");
    alert.id      = "ac-violation-alert";
    alert.textContent = message;

    Object.assign(alert.style, {
        position:   "fixed",
        top:        "0",
        left:       "0",
        right:      "0",
        background: "#1e40af",
        color:      "#fff",
        padding:    "10px 20px",
        fontSize:   "14px",
        textAlign:  "center",
        zIndex:     "9998"
    });

    document.body.appendChild(alert);
    setTimeout(() => alert.remove(), 5000);
    }
    
    
    
    
    
    async function sendEvent(event_type) {
        if (!_active) return;
        try {
            const response = await fetch(`/session/${_sessionId}/violation_event`, {
                method:  "POST",
                headers: {
                    "Content-Type":  "application/json",
                    "Authorization": `Bearer ${_token}`
                },
                body: JSON.stringify({ event_type })
            });

            if (!response.ok) {
                console.warn("[AntiCheat] Failed:", event_type, response.status);
                return;
            }

            const data = await response.json();
            if (!data || data.status === "cooldown") return;

            // Update score display on exam page
            updateScoreDisplay(data.new_score, data.new_state);

            // Show student alert if present
            if (data.student_alert) {
                showViolationAlert(data.student_alert);
            }

            // Show state message
            if (data.student_message) {
                showToast(data.student_message, data.new_state);
            }

            // Pause exam if ALERT or CRITICAL
            if (data.exam_paused) {
                lockExamInput(data.student_message);
            }

            // Terminate exam permanently
            if (data.new_state === "TERMINATED") {
                _active = false;
                showLockdownScreen(data.student_message);
            }

        } catch (err) {
            console.error("[AntiCheat] Error:", event_type, err);
        }
    }


    async function sendFrame(frameData, isFullFrame) {
    try {
        const response = await fetch(`/session/${_sessionId}/frame`, {
            method:  'POST',
            headers: {
                'Content-Type':  'application/json',
                'Authorization': `Bearer ${_token}`
            },
            body: JSON.stringify({ 
                frame_data: frameData
            })
        });

        if (!response.ok) {
            const errorText = await response.json();
            console.error("Error Detail:", JSON.stringify(errorText));
            throw new Error(`Failed to send frame, response status: ${response.status}`);
        }

        return await response.json()
    } catch (err) {
        console.error("Error sending frame:", err);
    }   
}

    async function sendLiveness(frameData) {
    try {
        const response = await fetch(`/session/${_sessionId}/liveness`, {
            method: 'POST',
            headers: {
                'Content-Type':  'application/json',
                'Authorization': `Bearer ${_token}`
            },
            body: JSON.stringify({ frame_data: frameData })
        });

        if (!response.ok) {
            const errorText = await response.json();
            console.error("Liveness Error:", JSON.stringify(errorText));
            throw new Error(`Liveness check failed, status: ${response.status}`);
        }

        return await response.json();

    } catch (err) {
        console.error("Error sending liveness frame:", err);
    }
}

    async function sendAudio(audioData) {
    try {
        const response = await fetch(`/session/${_sessionId}/audio`, {
            method:  'POST',
            headers: {
                'Content-Type':  'application/json',
                'Authorization': `Bearer ${_token}`
            },
            body: JSON.stringify({ audio_data: audioData })
        });

        if (!response.ok) {
            const errorText = await response.json();
            console.error("Error Detail:", JSON.stringify(errorText));
            throw new Error(`Failed to send audio, response status: ${response.status}`);
        }
    } catch (err) {
        console.error("Error sending audio:", err);
    }
}

    // Event Listeners
    // Tab Switch Detection/ Window blur
    function onVisibilityChange() {
        if (document.hidden) {
            sendEvent("tab_switch");
        }
    }

    function onWindowBlur() {
        sendEvent("tab_switch");
    }

    // Keyboard Shortcut Detection
    function onKeyDown(e) {
        // Detect common shortcuts (Ctrl+C, Ctrl+V, Ctrl+P, Print Screen)
        const ctrl = e.ctrlKey || e.metaKey; // Support Command key on Mac
        const shift = e.shiftKey;

        if (e.key === "PrintScreen") {
            e.preventDefault(); // Prevent the default print screen action
            sendEvent("print_screen");
        } else if (ctrl && e.key === "c") {
            e.preventDefault(); // Prevent the default copy action
            sendEvent("copy_attempt");
        } else if (ctrl && e.key === "v") {
            e.preventDefault(); // Prevent the default paste action
            sendEvent("paste_attempt");
        } else if (ctrl && e.key === "p") {
            e.preventDefault();
            sendEvent("keyboard_shortcut");
        } else if (ctrl && shift && e.key === "i") {
            e.preventDefault();
            sendEvent("devtools_open");
        } else if (ctrl && shift && e.key === "j") {
            e.preventDefault();
            sendEvent("devtools_open");
        } else if (e.key === "F12") {
            e.preventDefault();
            sendEvent("devtools_open");
        } else if (ctrl && e.key === "u"){
            e.preventDefault(); // Prevent the default view source action
            sendEvent("keyboard_shortcut");
        } else if (ctrl && e.key === "Tab") {
            e.preventDefault(); // Prevent the default tab switch action
            sendEvent("tab_switch");
        } else if (ctrl && e.key === "s") {
            e.preventDefault(); // Prevent the default save action
            sendEvent("keyboard_shortcut");
        } else if (ctrl && e.key === "a") {
            e.preventDefault(); // Prevent the default select all action
            sendEvent("keyboard_shortcut");
        }
    }

    // copy attempt and paste attempt can also be detected via the 'copy' and 'paste' events, which can catch attempts that might not involve keyboard shortcuts (e.g., right-click context menu).
    function onCopy(e) {
        e.preventDefault();
        sendEvent("copy_attempt");
    }

    function onPaste(e) {
        e.preventDefault();
        sendEvent("paste_attempt");
    }

    function onCut(e) {
        e.preventDefault();
        sendEvent("cut_attempt");
    }

    // Right Click Detection
    function onContextMenu(e) {
        e.preventDefault(); // Prevent the default context menu from appearing
        sendEvent("right_click");
    }

    // UI Helpers
    function showToast(message, state) {
        const existing = document.getElementById("anticheat-toast");
        if (existing) {
            existing.remove();
        }

        const toast = document.createElement("div");
        toast.id = "anticheat-toast";
        toast.textContent = message;

        const colorMap = {
            "CLEAR": "#ffffff",
            "CAUTION": "#FF9800",
            "WARNING": "#f44336",
            "ALERT": "#9C27B0",
            "CRITICAL": "#7f1d1d",
            "TERMINATED": "#000000"
        };

        Object.assign(toast.style, {
            position: "fixed",
            bottom: "20px",
            right: "20px",
            backgroundColor: colorMap[state] || "#374151",
            color: "#fff",
            padding: "12px 20px",
            borderRadius: "4px",
            fontSize: "16px",
            zIndex: 9999,
            maxwidth: "300px",
            boxShadow: "0 4px 12px rgba(0,0,0,0.3)",
        });

        document.body.appendChild(toast);

        // auto dismiss for caution and warning states after 5 seconds
        if (state === "CAUTION" || state === "WARNING") {
            setTimeout(() => toast.remove(), 5000);
        }
    }

    function lockExamInput(message) {
        // This function can be expanded to disable specific exam input fields or show a modal
        const overlay= document.createElement("div");
        overlay.id = "anticheat-pause-overlay";

        Object.assign(overlay.style, {
            position: "fixed",
            inset: 0,
            backgroundColor: "rgba(0, 0, 0, 0.85)",
            color: "#fff",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            flexDirection: "column",
            zIndex: 10000,
            fontSize: "18px",
            textAlign: "center",
            padding: "20px"
        });

        overlay.innerHTML = `<div style="font-size: 32px; margin-bottom: 20px;">██</div>
        <div style = "max-width: 480px; line-height: 1.5;">${message || "Exam paused for security reasons."}</div>
        <div style="margin-top: 20px; font-size: 13px; opacity: 0.6;">Please wait while we review your activity.</div>`;
    
        document.body.appendChild(overlay);
    }

   function showLockdownScreen(message) {
    const pause = document.getElementById("anticheat-pause-overlay");
    if (pause) pause.remove();

    const lockdown = document.createElement("div");
    lockdown.id    = "anticheat-lockdown";

    Object.assign(lockdown.style, {
        position:       "fixed",
        inset:          "0",
        backgroundColor:"#1a0000",
        color:          "#fff",
        display:        "flex",
        alignItems:     "center",
        justifyContent: "center",
        flexDirection:  "column",
        zIndex:         "99999",
        fontSize:       "18px",
        textAlign:      "center",
        padding:        "40px"
    });

    lockdown.innerHTML = `
        <div style="font-size:48px;margin-bottom:20px">🔒</div>
        <h2 style="color:#ef4444;margin-bottom:16px">Exam Terminated</h2>
        <div style="max-width:520px;line-height:1.7;color:#fca5a5">
            ${message || "Your exam has been terminated due to integrity violations."}
        </div>
        <div style="margin-top:32px;font-size:13px;opacity:0.5">
            An incident report has been sent to your institution.
        </div>
    `;

    document.body.appendChild(lockdown);

    // Block ALL further interaction
    document.addEventListener("keydown",     e => e.preventDefault(), true);
    document.addEventListener("click",       e => e.stopPropagation(), true);
    document.addEventListener("contextmenu", e => e.preventDefault(), true);
    document.addEventListener("copy",        e => e.preventDefault(), true);
    document.addEventListener("paste",       e => e.preventDefault(), true);

    // Stop webcam
    if (window.webcamStream) {
        window.webcamStream.getTracks().forEach(t => t.stop());
    }

    // Stop timer
    if (typeof timerInterval !== 'undefined' && timerInterval) {
        clearInterval(timerInterval);
        timerInterval = null;
    }
    }

    function updateScore(score, state) {
        updateScoreDisplay(score, state);
        if (state === "TERMINATED" && _active) {
            _active = false;
            showLockdownScreen("Your exam has been terminated due to integrity violations.");
        }
        if ((state === "ALERT" || state === "CRITICAL") && _active) {
            lockExamInput("Your exam has been paused for review.");
        }
    }

    function triggerLockdown(message) {
        _active = false;
        showLockdownScreen(message);
    }   



    //Public API

    return {
        init: function(sessionId, token) {
            _sessionId = sessionId;
            _token = token;
            _active = true;

            // Attach event listeners
            document.addEventListener("visibilitychange", onVisibilityChange);
            window.addEventListener("blur", onWindowBlur);
            document.addEventListener("keydown", onKeyDown, true); // Use capture phase to catch events before they reach the page's own handlers
            document.addEventListener("contextmenu", onContextMenu);
            document.addEventListener("copy", onCopy, true);
            document.addEventListener("paste", onPaste, true); // Use capture phase for copy/paste to catch all attempts
            document.addEventListener("cut", onCut, true);

            console.log("[Anticheat] Monitoring initialized for session:", _sessionId);
        },
        destroy: function() {
            _active = false;

            // Detach event listeners
            document.removeEventListener("visibilitychange", onVisibilityChange);
            window.removeEventListener("blur", onWindowBlur);
            document.removeEventListener("keydown", onKeyDown, true);
            document.removeEventListener("contextmenu", onContextMenu);
            document.removeEventListener("copy", onCopy, true);
            document.removeEventListener("paste", onPaste, true);
            document.removeEventListener("cut", onCut, true);

            console.log("[Anticheat] Monitoring stopped for session:", _sessionId);
        },
        sendEvent: sendEvent, // Expose sendEvent for manual triggering if needed
        sendFrame: sendFrame, // Expose sendFrame for sending webcam frames to the backend
        sendAudio: sendAudio, // Expose sendAudio for sending audio data to the backend
        updateScore: updateScore,
        triggerLockdown: triggerLockdown
    };
})();

window.AntiCheat = AntiCheat; // Expose the AntiCheat module to the global scope