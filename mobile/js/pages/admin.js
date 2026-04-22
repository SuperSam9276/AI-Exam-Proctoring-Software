/**
 * ProctorAI Admin Panel
 */

class AdminPanel extends Page {
    render() {
        this.container.innerHTML = `
            <div class="page-dashboard page-enter">
                <header class="dashboard-header" style="margin-bottom: 2rem;">
                    <p style="color: var(--text-secondary);">Administration</p>
                    <h2 style="font-size: 1.5rem; font-weight: 800;">Management Panel</h2>
                </header>

                <div class="monitoring-grid">
                    ${Card.stat('Total Exams', '24', 'file-text')}
                    ${Card.stat('Total Users', '156', 'users', 'var(--accent-purple)')}
                </div>

                <div style="margin-top: 2rem;">
                    <button class="btn btn-primary" style="margin-bottom: 1.5rem;" onclick="Modal.open({title:'Create Exam', body: 'Exam creation form would go here.'})">
                        <i data-lucide="plus-circle"></i>
                        Create New Exam
                    </button>
                    
                    <div class="section-title">Manage Exams</div>
                    <div id="admin-exams-list">
                        <!-- Exam management list -->
                    </div>
                </div>
            </div>
        `;

        this.loadExams();
        if (window.lucide) lucide.createIcons();
    }

    async loadExams() {
        const list = document.getElementById('admin-exams-list');
        const exams = await api.getExams();
        list.innerHTML = exams.map(exam => `
            <div class="card glass" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem;">
                <div>
                    <div style="font-weight: 600;">${exam.title}</div>
                    <div style="font-size: 0.75rem; color: var(--text-muted);">${new Date(exam.date).toLocaleDateString()}</div>
                </div>
                <div style="display: flex; gap: 0.5rem;">
                    <button class="btn-icon" style="color: var(--accent-cyan);"><i data-lucide="edit-2" size="16"></i></button>
                    <button class="btn-icon" style="color: var(--state-alert);"><i data-lucide="trash-2" size="16"></i></button>
                </div>
            </div>
        `).join('');
        if (window.lucide) lucide.createIcons();
    }
}
