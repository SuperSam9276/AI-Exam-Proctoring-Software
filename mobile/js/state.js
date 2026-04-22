/**
 * ProctorAI Global State Manager
 * A simple observable store for reactive UI updates
 */

class State {
    constructor() {
        this.listeners = new Set();
        this.data = {
            user: JSON.parse(localStorage.getItem('proctor_user')) || null,
            token: localStorage.getItem('proctor_token') || null,
            isMockMode: localStorage.getItem('MOCK_MODE') !== 'false', // Default to true for demo
            activeExam: null,
            exams: [],
            sessions: [], // Live sessions for proctors
            view: 'login', // current active page
            alerts: []
        };
    }

    /**
     * Update state and notify listeners
     * @param {Object} newData 
     */
    setState(newData) {
        this.data = { ...this.data, ...newData };
        
        // Persist critical data
        if (newData.user) localStorage.setItem('proctor_user', JSON.stringify(newData.user));
        if (newData.token) localStorage.setItem('proctor_token', newData.token);
        if (newData.isMockMode !== undefined) localStorage.setItem('MOCK_MODE', newData.isMockMode);
        
        this.notify();
    }

    /**
     * Subscribe to state changes
     * @param {Function} listener 
     * @returns {Function} unsubscribe function
     */
    subscribe(listener) {
        this.listeners.add(listener);
        // Initial call
        listener(this.data);
        return () => this.listeners.delete(listener);
    }

    notify() {
        this.listeners.forEach(listener => listener(this.data));
    }

    /**
     * Getters
     */
    get user() { return this.data.user; }
    get token() { return this.data.token; }
    get isMockMode() { return this.data.isMockMode; }
    get view() { return this.data.view; }

    logout() {
        localStorage.removeItem('proctor_user');
        localStorage.removeItem('proctor_token');
        this.setState({ user: null, token: null, view: 'login' });
    }
}

// Create singleton instance
const state = new State();
window.appState = state; // Global access for debugging
