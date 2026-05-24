/**
 * ProctorAI Main App Controller
 * Handles routing and page orchestration
 */

class App {
    constructor() {
        this.contentArea = document.getElementById('app-content');
        this.splash = document.getElementById('splash-screen');
        this.appShell = document.getElementById('app');
        this.routes = {
            'login': LoginPage,
            'student': StudentDashboard,
            'exam-session': ExamSessionPage,
            'proctor': ProctorDashboard,
            'admin': AdminPanel
        };

        window.addEventListener('hashchange', () => this.handleRouting());
        this.init();
    }

    async init() {
        // Wait for splash animation
        setTimeout(() => {
            this.splash.style.opacity = '0';
            setTimeout(() => {
                this.splash.style.display = 'none';
                this.appShell.style.display = 'flex';
                this.handleRouting();
            }, 500);
        }, 2000);

        // Initialize state listeners
        state.subscribe(data => {
            if (data.view !== this.currentView) {
                this.navigate(data.view);
            }
        });
    }

    handleRouting() {
        const hash = window.location.hash.replace('#/', '') || (state.user ? state.user.role : 'login');
        this.renderView(hash);
    }

    navigate(view) {
        window.location.hash = `#/${view}`;
    }

    renderView(viewName) {
        if (this.currentView === viewName) return;
        
        const PageClass = this.routes[viewName] || this.routes['login'];
        this.currentPage = new PageClass(this.contentArea);
        this.currentPage.render();
        this.currentView = viewName;

        // Update nav bar
        if (viewName !== 'login' && viewName !== 'exam-session') {
            document.getElementById('app-nav').style.display = 'flex';
            NavBar.render();
        } else {
            document.getElementById('app-nav').style.display = 'none';
        }

        // Trigger Lucide icons
        if (window.lucide) {
            lucide.createIcons();
        }
    }
}

// Base Page Class
class Page {
    constructor(container) {
        this.container = container;
    }
    render() {
        this.container.innerHTML = `<div class="page-enter">Rendering ${this.constructor.name}...</div>`;
    }
}

// Start the app
document.addEventListener('DOMContentLoaded', () => {
    window.proctorApp = new App();
});
