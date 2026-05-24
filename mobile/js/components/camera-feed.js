/**
 * ProctorAI Camera Feed Component
 */

class CameraFeed {
    constructor(videoElementId) {
        this.videoElementId = videoElementId;
        this.stream = null;
    }

    async start() {
        const video = document.getElementById(this.videoElementId);
        if (!video) return;

        try {
            this.stream = await navigator.mediaDevices.getUserMedia({ 
                video: { facingMode: 'user' }, 
                audio: false 
            });
            video.srcObject = this.stream;
            video.play();
            Toast.success('Camera connected');
        } catch (err) {
            console.error('Camera Access Error:', err);
            Toast.error('Please allow camera access to continue');
        }
    }

    stop() {
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
        }
    }
}
