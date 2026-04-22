/**
 * ProctorAI Monitoring Dashboard
 */

class ProctorDashboard extends Page {
    render() {
        this.container.innerHTML = `
            <div class="page-dashboard page-enter">
                <header class="dashboard-header" style="margin-bottom: 2rem;">
                    <p style="color: var(--text-secondary);">Monitoring Hub</p>
                    <h2 style="font-size: 1.5rem; font-weight: 800;">Active Sessions</h2>
                </header>

                <div class="monitoring-stats" style="display: flex; gap: 0.75rem; margin-bottom: 1.5rem;">
                    <div class="stat-pill" style="flex: 1; justify-content: center;">
                        <span style="color: var(--text-secondary);">Active:</span>
                        <span style="font-weight: 700;">12</span>
                    </div>
                    <div class="stat-pill" style="flex: 1; justify-content: center; border-color: var(--state-warning);">
                        <span style="color: var(--text-secondary);">At Risk:</span>
                        <span style="font-weight: 700; color: var(--state-warning);">2</span>
                    </div>
                </div>

                <div class="monitoring-grid" id="proctor-grid">
                    <!-- Cards will be injected here -->
                </div>

                <div style="margin-top: 2rem;">
                    <div class="section-title">
                        <span>Recent Alerts</span>
                        <span class="badge" style="background: var(--state-alert); font-size: 0.6rem; padding: 2px 6px; border-radius: 4px;">LIVE</span>
                    </div>
                    <div class="alert-list" id="alert-feed">
                        <div class="card glass" style="padding: 0.75rem; font-size: 0.875rem; border-left: 3px solid var(--state-warning);">
                            <strong>Mayank Garg</strong>: Switched tab detected
                            <div style="font-size: 0.7rem; color: var(--text-muted); margin-top: 2px;">2 mins ago</div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        this.loadSessions();
        if (window.lucide) lucide.createIcons();
    }

    loadSessions() {
        const grid = document.getElementById('proctor-grid');
        // Mocking some active sessions
        const mockSessions = [
            { student_name: 'Mayank Garg', state: 'WARNING', penalty_score: 45 },
            { student_name: 'Rahul Sharma', state: 'CLEAR', penalty_score: 5 },
            { student_name: 'Priya Singh', state: 'CAUTION', penalty_score: 22 },
            { student_name: 'Ankit Verma', state: 'CLEAR', penalty_score: 0 }
        ];

        grid.innerHTML = mockSessions.map(s => Card.session(s)).join('');
    }
}
