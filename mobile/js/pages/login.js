/**
 * ProctorAI Login Page
 */

class LoginPage extends Page {
    render() {
        this.container.innerHTML = `
            <div class="page-login page-enter">
                <div class="login-header">
                    <div class="splash__icon" style="width: 60px; height: 60px; margin-bottom: 1rem;">
                        <svg viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <rect x="4" y="12" width="56" height="40" rx="4" stroke="url(#grad2)" stroke-width="3" fill="none"/>
                            <circle cx="32" cy="32" r="10" stroke="url(#grad2)" stroke-width="2.5" fill="none"/>
                            <circle cx="32" cy="32" r="4" fill="url(#grad2)"/>
                            <defs>
                                <linearGradient id="grad2" x1="0" y1="0" x2="64" y2="64">
                                    <stop offset="0%" stop-color="#22d3ee"/>
                                    <stop offset="100%" stop-color="#a78bfa"/>
                                </linearGradient>
                            </defs>
                        </svg>
                    </div>
                    <h1 class="splash__title">Proctor<span>AI</span></h1>
                    <p class="splash__subtitle">Sign in to start your session</p>
                </div>

                <form id="login-form">
                    <div class="form-group">
                        <label class="label">Email Address</label>
                        <input type="email" class="input" id="login-email" placeholder="student@college.edu" required>
                    </div>
                    <div class="form-group">
                        <label class="label">Password</label>
                        <input type="password" class="input" id="login-password" placeholder="••••••••" required>
                    </div>
                    <button type="submit" class="btn btn-primary" id="btn-login">Sign In</button>
                </form>

                <div style="text-align: center; margin-top: 2rem;">
                    <p style="color: var(--text-secondary); font-size: 0.875rem;">
                        Don't have an account? <a href="#" style="color: var(--accent-cyan); font-weight: 600;">Register</a>
                    </p>
                    <div style="margin-top: 1rem; padding-top: 1rem; border-top: 1px solid var(--border-color);">
                        <button class="btn btn-ghost" onclick="appState.setState({ isMockMode: !appState.isMockMode })">
                            <i data-lucide="database"></i>
                            Mock Mode: ${appState.isMockMode ? 'ON' : 'OFF'}
                        </button>
                    </div>
                </div>
            </div>
        `;

        document.getElementById('login-form').onsubmit = (e) => this.handleLogin(e);
        if (window.lucide) lucide.createIcons();
    }

    async handleLogin(e) {
        e.preventDefault();
        const email = document.getElementById('login-email').value;
        const password = document.getElementById('login-password').value;
        const btn = document.getElementById('btn-login');

        btn.disabled = true;
        btn.innerHTML = 'Signing in...';

        try {
            const data = await api.login(email, password);
            Toast.success(`Welcome back, ${data.name}!`);
            
            appState.setState({ 
                user: { name: data.name, role: data.role }, 
                token: data.access_token,
                view: data.role // Navigate based on role
            });
        } catch (err) {
            Toast.error(err.message);
            btn.disabled = false;
            btn.innerHTML = 'Sign In';
        }
    }
}
