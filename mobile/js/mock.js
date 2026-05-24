/**
 * ProctorAI Mock Data Engine
 * Simulates backend responses for demo purposes
 */

class MockDataEngine {
    constructor() {
        this.delay = 500; // Simulate network latency
        this.students = [
            { id: 's1', name: 'Mayank Garg', email: 'mayank@college.edu', role: 'student', college_id: 'C101' },
            { id: 's2', name: 'Rahul Sharma', email: 'rahul@college.edu', role: 'student', college_id: 'C101' },
            { id: 's3', name: 'Priya Singh', email: 'priya@college.edu', role: 'student', college_id: 'C101' }
        ];
        
        this.exams = [
            { id: 'e1', title: 'Data Structures & Algorithms', description: 'Final term exam for CS 301', date: new Date().toISOString(), duration_minutes: 90, start_time: new Date().toISOString() },
            { id: 'e2', title: 'Operating Systems', description: 'Mid-term evaluation', date: new Date(Date.now() + 86400000).toISOString(), duration_minutes: 60, start_time: new Date(Date.now() + 86400000).toISOString() },
            { id: 'e3', title: 'Internet of Things', description: 'Practical quiz', date: new Date(Date.now() + 172800000).toISOString(), duration_minutes: 30, start_time: new Date(Date.now() + 172800000).toISOString() }
        ];

        this.sessions = [];
    }

    async handleRequest(endpoint, options) {
        console.log(`[Mock API] ${options.method || 'GET'} ${endpoint}`);
        await new Promise(resolve => setTimeout(resolve, this.delay));

        // Login
        if (endpoint === '/auth/login') {
            const { email } = JSON.parse(options.body);
            // Accept any valid-looking email for demo
            return {
                access_token: 'mock_jwt_token_' + Date.now(),
                token_type: 'bearer',
                role: email.includes('admin') ? 'admin' : (email.includes('proctor') ? 'proctor' : 'student'),
                name: email.split('@')[0].toUpperCase()
            };
        }

        // List Exams
        if (endpoint === '/exams/listings') {
            return this.exams;
        }

        // Start Session
        if (endpoint === '/sessions/start') {
            const { exam_id } = JSON.parse(options.body);
            const session = {
                session_id: 'sess_' + Math.random().toString(36).substr(2, 9),
                state: 'CLEAR',
                penalty_score: 0,
                message: 'Exam session started successfully'
            };
            this.sessions.push(session);
            return session;
        }

        // Get Session State
        if (endpoint.includes('/state')) {
            const sessionId = endpoint.split('/')[2];
            // Simulate random risk increases for demo
            const score = Math.floor(Math.random() * 10); 
            return {
                session_id: sessionId,
                state: this.getStateLabel(score),
                penalty_score: score
            };
        }

        return { status: 'success' };
    }

    getStateLabel(score) {
        if (score <= 0) return "CLEAR";
        if (score <= 30) return "CAUTION";
        if (score <= 60) return "WARNING";
        if (score <= 85) return "ALERT";
        if (score <= 99) return "CRITICAL";
        return "TERMINATED";
    }
}

const mockDataEngine = new MockDataEngine();
