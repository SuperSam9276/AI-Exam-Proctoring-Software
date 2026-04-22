/**
 * ProctorAI API Client
 */

class ApiClient {
    constructor() {
        this.baseUrl = localStorage.getItem('API_BASE_URL') || 'http://localhost:8000';
    }

    async request(endpoint, options = {}) {
        // If mock mode is on, we skip actual network requests
        if (state.isMockMode) {
            return mockDataEngine.handleRequest(endpoint, options);
        }

        const url = `${this.baseUrl}${endpoint}`;
        const headers = {
            'Content-Type': 'application/json',
            ...options.headers
        };

        if (state.token) {
            headers['Authorization'] = `Bearer ${state.token}`;
        }

        try {
            const response = await fetch(url, { ...options, headers });
            
            if (response.status === 401) {
                state.logout();
                throw new Error('Unauthorized');
            }

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'API Request failed');
            }

            return await response.json();
        } catch (err) {
            console.error(`API Error [${endpoint}]:`, err);
            throw err;
        }
    }

    // Auth
    login(email, password) {
        return this.request('/auth/login', {
            method: 'POST',
            body: JSON.stringify({ email, password })
        });
    }

    register(data) {
        return this.request('/auth/register', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    getMe() {
        return this.request('/auth/me');
    }

    // Exams
    getExams() {
        return this.request('/exams/listings');
    }

    createExam(data) {
        return this.request('/exams/creation', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    // Sessions
    startSession(examId) {
        return this.request('/sessions/start', {
            method: 'POST',
            body: JSON.stringify({ exam_id: examId })
        });
    }

    getSessionState(sessionId) {
        return this.request(`/sessions/${sessionId}/state`);
    }
}

const api = new ApiClient();
