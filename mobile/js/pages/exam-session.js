/**
 * ProctorAI Exam Session Page
 */

class ExamSessionPage extends Page {
    constructor(container) {
        super(container);
        this.camera = new CameraFeed('exam-video');
        this.penaltyScore = 0;
        this.timerInterval = null;
        this.stateInterval = null;
    }

    async render() {
        const exam = appState.data.activeExam || { title: 'Exam Session', duration_minutes: 60 };
        
        this.container.innerHTML = `
            <div class="page-exam page-enter">
                <div class="camera-container">
                    <video id="exam-video" class="camera-feed" autoplay playsinline muted></video>
                    
                    <div class="exam-overlay">
                        <div class="exam-stats">
                            <div class="stat-pill">
                                <i data-lucide="clock" size="16"></i>
                                <span id="exam-timer">${exam.duration_minutes}:00</span>
                            </div>
                            <div class="stat-pill" id="state-badge">
                                <div class="pulse-dot" style="background: var(--state-clear)"></div>
                                <span id="state-text">CLEAR</span>
                            </div>
                        </div>

                        <div class="exam-footer" style="pointer-events: auto; text-align: center; padding-bottom: 2rem;">
                            <div class="risk-gauge-container" style="margin-bottom: 2rem;">
                                <div class="risk-label" style="font-size: 0.75rem; color: var(--text-secondary); margin-bottom: 0.5rem;">RISK SCORE</div>
                                <div id="risk-value" style="font-size: 2.5rem; font-weight: 800; color: var(--text-primary);">0%</div>
                            </div>
                            
                            <button class="btn btn-danger" id="btn-end-exam" style="width: auto; padding: 1rem 3rem; border-radius: var(--radius-full);">
                                End Exam
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        await this.camera.start();
        this.startTimer(exam.duration_minutes);
        this.startStateSync();

        document.getElementById('btn-end-exam').onclick = () => this.confirmEnd();
        if (window.lucide) lucide.createIcons();
    }

    startTimer(mins) {
        let seconds = mins * 60;
        const timerEl = document.getElementById('exam-timer');
        
        this.timerInterval = setInterval(() => {
            seconds--;
            if (seconds <= 0) {
                this.endSession();
                return;
            }
            const m = Math.floor(seconds / 60);
            const s = seconds % 60;
            timerEl.innerText = `${m}:${s.toString().padStart(2, '0')}`;
        }, 1000);
    }

    startStateSync() {
        // In a real app, this would poll the backend /session/:id/state
        this.stateInterval = setInterval(async () => {
            if (appState.isMockMode) {
                // Simulate some risk events
                if (Math.random() > 0.9) {
                    this.penaltyScore += Math.floor(Math.random() * 15);
                    this.updateUI();
                }
            } else {
                // Real API call
                try {
                    const data = await api.getSessionState(appState.data.sessionId);
                    this.penaltyScore = data.penalty_score;
                    this.updateUI(data.state);
                } catch (err) { console.error(err); }
            }
        }, 3000);
    }

    updateUI(stateText) {
        const scoreEl = document.getElementById('risk-value');
        const badge = document.getElementById('state-badge');
        const textEl = document.getElementById('state-text');
        
        scoreEl.innerText = `${this.penaltyScore}%`;
        
        const state = stateText || this.getStateLabel(this.penaltyScore);
        textEl.innerText = state;
        
        const color = `var(--state-${state.toLowerCase()})`;
        badge.querySelector('.pulse-dot').style.background = color;
        scoreEl.style.color = color;

        if (state === 'TERMINATED') {
            this.endSession(true);
        }
    }

    getStateLabel(score) {
        if (score <= 0) return "CLEAR";
        if (score <= 30) return "CAUTION";
        if (score <= 60) return "WARNING";
        if (score <= 85) return "ALERT";
        if (score <= 99) return "CRITICAL";
        return "TERMINATED";
    }

    confirmEnd() {
        Modal.open({
            title: 'End Exam?',
            body: 'Are you sure you want to submit and end your session? This action cannot be undone.',
            primaryBtn: 'Yes, Submit',
            secondaryBtn: 'Continue Exam',
            onPrimary: () => this.endSession()
        });
    }

    endSession(terminated = false) {
        this.camera.stop();
        clearInterval(this.timerInterval);
        clearInterval(this.stateInterval);
        
        Toast.success(terminated ? 'Exam terminated due to violations' : 'Exam submitted successfully');
        appState.setState({ view: 'student', activeExam: null });
    }
}
