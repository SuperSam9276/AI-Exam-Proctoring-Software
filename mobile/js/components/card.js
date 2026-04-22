/**
 * ProctorAI Card Components
 */

class Card {
    static exam(exam) {
        const date = new Date(exam.date).toLocaleDateString();
        const time = new Date(exam.start_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        
        return `
            <div class="card exam-card glass" onclick="appState.setState({ activeExam: ${JSON.stringify(exam)}, view: 'exam-session' })">
                <div class="exam-card__time">${date} • ${time}</div>
                <h3 class="exam-card__title">${exam.title}</h3>
                <p class="exam-card__desc">${exam.description || 'No description provided'}</p>
                <div class="exam-card__meta">
                    <span><i data-lucide="clock" size="14"></i> ${exam.duration_minutes} mins</span>
                </div>
            </div>
        `;
    }

    static session(session) {
        const stateColor = `var(--state-${session.state.toLowerCase()})`;
        return `
            <div class="card student-card glass">
                <div class="student-mini-cam"></div>
                <div class="student-info">
                    <h4 class="student-name">${session.student_name || 'Student'}</h4>
                    <div class="state-badge" style="color: ${stateColor}">${session.state}</div>
                </div>
                <div class="risk-bar">
                    <div class="risk-bar__fill" style="width: ${session.penalty_score}%; background: ${stateColor}"></div>
                </div>
            </div>
        `;
    }

    static stat(label, value, icon, color = 'var(--accent-cyan)') {
        return `
            <div class="card stat-card glass">
                <div class="stat-icon" style="background: ${color}22; color: ${color}">
                    <i data-lucide="${icon}"></i>
                </div>
                <div class="stat-content">
                    <div class="stat-label">${label}</div>
                    <div class="stat-value">${value}</div>
                </div>
            </div>
        `;
    }
}
