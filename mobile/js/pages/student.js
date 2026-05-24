/**
 * ProctorAI Student Dashboard
 */

class StudentDashboard extends Page {
    async render() {
        this.container.innerHTML = `
            <div class="page-dashboard page-enter">
                <header class="dashboard-header" style="margin-bottom: 2rem;">
                    <p style="color: var(--text-secondary);">Hello,</p>
                    <h2 style="font-size: 1.5rem; font-weight: 800;">${appState.user?.name || 'Student'}</h2>
                </header>

                <section>
                    <div class="section-title">
                        <span>Upcoming Exams</span>
                        <i data-lucide="calendar" size="18"></i>
                    </div>
                    <div id="exams-list" class="exams-grid">
                        <div class="loading-state">Loading exams...</div>
                    </div>
                </section>

                <section style="margin-top: 2rem;">
                    <div class="section-title">
                        <span>Recent Performance</span>
                    </div>
                    <div class="monitoring-grid">
                        ${Card.stat('Avg Risk', '12%', 'activity', 'var(--state-clear)')}
                        ${Card.stat('Sessions', '8', 'check-circle', 'var(--accent-cyan)')}
                    </div>
                </section>
            </div>
        `;

        this.loadExams();
        if (window.lucide) lucide.createIcons();
    }

    async loadExams() {
        const list = document.getElementById('exams-list');
        try {
            const exams = await api.getExams();
            if (exams.length === 0) {
                list.innerHTML = '<p style="color: var(--text-muted); text-align: center; padding: 2rem;">No upcoming exams found.</p>';
                return;
            }
            list.innerHTML = exams.map(exam => Card.exam(exam)).join('');
            if (window.lucide) lucide.createIcons();
        } catch (err) {
            list.innerHTML = `<p style="color: var(--state-alert); text-align: center;">Error loading exams: ${err.message}</p>`;
        }
    }
}
