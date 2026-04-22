/**
 * ProctorAI Navigation Component
 */

class NavBar {
    static render() {
        const nav = document.getElementById('app-nav');
        const role = state.user ? state.user.role : 'student';
        const currentView = window.location.hash.replace('#/', '');

        let navHtml = '';

        if (role === 'student') {
            navHtml = `
                <a href="#/student" class="nav-item ${currentView === 'student' ? 'active' : ''}">
                    <i data-lucide="home"></i>
                    <span>Home</span>
                </a>
                <a href="#/history" class="nav-item ${currentView === 'history' ? 'active' : ''}">
                    <i data-lucide="clipboard-list"></i>
                    <span>Sessions</span>
                </a>
            `;
        } else if (role === 'proctor') {
            navHtml = `
                <a href="#/proctor" class="nav-item ${currentView === 'proctor' ? 'active' : ''}">
                    <i data-lucide="monitor"></i>
                    <span>Monitor</span>
                </a>
                <a href="#/alerts" class="nav-item ${currentView === 'alerts' ? 'active' : ''}">
                    <i data-lucide="bell"></i>
                    <span>Alerts</span>
                </a>
            `;
        } else if (role === 'admin') {
            navHtml = `
                <a href="#/admin" class="nav-item ${currentView === 'admin' ? 'active' : ''}">
                    <i data-lucide="settings"></i>
                    <span>Admin</span>
                </a>
                <a href="#/analytics" class="nav-item ${currentView === 'analytics' ? 'active' : ''}">
                    <i data-lucide="bar-chart-2"></i>
                    <span>Stats</span>
                </a>
            `;
        }

        // Add Profile for everyone
        navHtml += `
            <a href="#/profile" class="nav-item ${currentView === 'profile' ? 'active' : ''}">
                <i data-lucide="user"></i>
                <span>Profile</span>
            </a>
        `;

        nav.innerHTML = navHtml;
        if (window.lucide) lucide.createIcons();
    }
}

class Header {
    static render(title, showBack = false) {
        const header = document.getElementById('app-header');
        header.innerHTML = `
            <div class="header-content glass">
                ${showBack ? '<button class="btn-back"><i data-lucide="chevron-left"></i></button>' : ''}
                <h1 class="header-title">${title}</h1>
                <div class="header-actions">
                    <button class="btn-icon"><i data-lucide="more-vertical"></i></button>
                </div>
            </div>
        `;
        if (window.lucide) lucide.createIcons();
    }
}
