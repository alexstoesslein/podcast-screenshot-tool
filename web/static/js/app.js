/**
 * Screenshot Tool Web App
 * Handles video upload, analysis, and frame export
 */

class ScreenshotTool {
    constructor() {
        this.jobId = null;
        this.videoInfo = null;
        this.currentFrame = 0;
        this.selectedFrames = [];
        this.lutData = null;
        this.chunkSize = 5 * 1024 * 1024; // 5MB

        this.initElements();
        this.initEventListeners();
    }

    initElements() {
        // Upload
        this.uploadArea = document.getElementById('upload-area');
        this.fileInput = document.getElementById('file-input');
        this.uploadProgress = document.getElementById('upload-progress');
        this.uploadProgressFill = document.getElementById('upload-progress-fill');
        this.uploadProgressText = document.getElementById('upload-progress-text');

        // Video preview
        this.videoPreview = document.getElementById('video-preview');
        this.frameImage = document.getElementById('frame-image');
        this.timelineSlider = document.getElementById('timeline-slider');
        this.currentTime = document.getElementById('current-time');
        this.duration = document.getElementById('duration');
        this.frameInfo = document.getElementById('frame-info');
        this.prevFrameBtn = document.getElementById('prev-frame-btn');
        this.nextFrameBtn = document.getElementById('next-frame-btn');
        this.addFrameBtn = document.getElementById('add-frame-btn');

        // Frames
        this.framesSection = document.getElementById('frames-section');
        this.framesList = document.getElementById('frames-list');

        // Settings
        this.projectType = document.getElementById('project-type');
        this.numScreenshots = document.getElementById('num-screenshots');
        this.analyzeBtn = document.getElementById('analyze-btn');
        this.analysisProgress = document.getElementById('analysis-progress');
        this.analysisProgressFill = document.getElementById('analysis-progress-fill');
        this.analysisProgressText = document.getElementById('analysis-progress-text');

        // LUT
        this.lutInput = document.getElementById('lut-input');
        this.lutLabel = document.getElementById('lut-label');
        this.applyLut = document.getElementById('apply-lut');
        this.previewLut = document.getElementById('preview-lut');

        // Export
        this.exportFormat = document.getElementById('export-format');
        this.qualitySlider = document.getElementById('quality-slider');
        this.qualityValue = document.getElementById('quality-value');
        this.qualityInfo = document.getElementById('quality-info');
        this.exportBtn = document.getElementById('export-btn');

        // Status
        this.statusText = document.getElementById('status-text');
    }

    initEventListeners() {
        // File upload
        this.fileInput.addEventListener('change', (e) => this.handleFileSelect(e));
        this.uploadArea.addEventListener('dragover', (e) => this.handleDragOver(e));
        this.uploadArea.addEventListener('dragleave', (e) => this.handleDragLeave(e));
        this.uploadArea.addEventListener('drop', (e) => this.handleDrop(e));

        // Video controls
        this.timelineSlider.addEventListener('input', () => this.seekToFrame(parseInt(this.timelineSlider.value)));
        this.prevFrameBtn.addEventListener('click', () => this.prevFrame());
        this.nextFrameBtn.addEventListener('click', () => this.nextFrame());
        this.addFrameBtn.addEventListener('click', () => this.addCurrentFrame());

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => this.handleKeyboard(e));

        // Analysis
        this.analyzeBtn.addEventListener('click', () => this.analyzeVideo());

        // LUT
        this.lutInput.addEventListener('change', (e) => this.loadLut(e));

        // Export
        this.qualitySlider.addEventListener('input', () => {
            this.qualityValue.textContent = this.qualitySlider.value + '%';
        });
        this.exportFormat.addEventListener('change', () => this.updateQualityVisibility());
        this.exportBtn.addEventListener('click', () => this.exportFrames());
    }

    handleDragOver(e) {
        e.preventDefault();
        this.uploadArea.classList.add('dragover');
    }

    handleDragLeave(e) {
        e.preventDefault();
        this.uploadArea.classList.remove('dragover');
    }

    handleDrop(e) {
        e.preventDefault();
        this.uploadArea.classList.remove('dragover');
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            this.uploadFile(files[0]);
        }
    }

    handleFileSelect(e) {
        const files = e.target.files;
        if (files.length > 0) {
            this.uploadFile(files[0]);
        }
    }

    async uploadFile(file) {
        this.setStatus(`Bereite Upload vor: ${file.name}`);

        // Initialize upload
        const initRes = await fetch('/api/upload/init', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                filename: file.name,
                size: file.size
            })
        });
        const initData = await initRes.json();
        this.jobId = initData.job_id;
        this.chunkSize = initData.chunk_size;

        // Show progress
        this.uploadArea.classList.add('hidden');
        this.uploadProgress.classList.remove('hidden');

        // Upload chunks
        const totalChunks = Math.ceil(file.size / this.chunkSize);
        let uploadedChunks = 0;

        for (let i = 0; i < totalChunks; i++) {
            const start = i * this.chunkSize;
            const end = Math.min(start + this.chunkSize, file.size);
            const chunk = file.slice(start, end);

            const formData = new FormData();
            formData.append('chunk', chunk);
            formData.append('chunk_index', i);
            formData.append('total_chunks', totalChunks);

            await fetch(`/api/upload/chunk/${this.jobId}`, {
                method: 'POST',
                body: formData
            });

            uploadedChunks++;
            const progress = (uploadedChunks / totalChunks) * 100;
            this.uploadProgressFill.style.width = progress + '%';
            this.uploadProgressText.textContent = `${Math.round(progress)}% (${this.formatSize(end)} / ${this.formatSize(file.size)})`;
        }

        this.setStatus('Video hochgeladen, lade Informationen...');
        await this.loadVideoInfo();
    }

    async loadVideoInfo() {
        const res = await fetch(`/api/video/info/${this.jobId}`);
        const data = await res.json();

        if (data.error) {
            this.setStatus('Fehler: ' + data.error);
            return;
        }

        this.videoInfo = data;
        this.timelineSlider.max = data.frame_count - 1;
        this.duration.textContent = data.duration_formatted;

        // Show video preview
        this.uploadProgress.classList.add('hidden');
        this.videoPreview.classList.remove('hidden');
        this.framesSection.classList.remove('hidden');
        this.analyzeBtn.disabled = false;

        // Load first frame
        this.seekToFrame(0);
        this.setStatus(`Video geladen: ${data.width}×${data.height} | ${data.fps.toFixed(1)} fps | ${data.duration_formatted}`);
    }

    async seekToFrame(frameNumber) {
        this.currentFrame = frameNumber;
        this.timelineSlider.value = frameNumber;

        // Update time display
        if (this.videoInfo) {
            const timestamp = frameNumber / this.videoInfo.fps;
            this.currentTime.textContent = this.formatTimestamp(timestamp);
            this.frameInfo.textContent = `Frame: ${frameNumber} / ${this.videoInfo.frame_count - 1}`;
        }

        // Load frame image
        this.frameImage.src = `/api/video/frame/${this.jobId}/${frameNumber}`;
    }

    prevFrame() {
        if (this.currentFrame > 0) {
            this.seekToFrame(this.currentFrame - 1);
        }
    }

    nextFrame() {
        if (this.videoInfo && this.currentFrame < this.videoInfo.frame_count - 1) {
            this.seekToFrame(this.currentFrame + 1);
        }
    }

    handleKeyboard(e) {
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'SELECT') return;

        switch (e.key) {
            case 'ArrowLeft':
                this.prevFrame();
                break;
            case 'ArrowRight':
                this.nextFrame();
                break;
            case ' ':
                e.preventDefault();
                this.addCurrentFrame();
                break;
        }
    }

    addCurrentFrame() {
        // Check if already added
        if (this.selectedFrames.includes(this.currentFrame)) {
            this.setStatus('Frame bereits in der Auswahl');
            return;
        }

        this.selectedFrames.push(this.currentFrame);
        this.renderFramesList();
        this.updateExportButton();
        this.setStatus(`Frame ${this.currentFrame} hinzugefügt – ${this.selectedFrames.length} Frames insgesamt`);
    }

    removeFrame(frameNumber) {
        this.selectedFrames = this.selectedFrames.filter(f => f !== frameNumber);
        this.renderFramesList();
        this.updateExportButton();
    }

    renderFramesList() {
        this.framesList.innerHTML = '';

        for (const frameNumber of this.selectedFrames) {
            const div = document.createElement('div');
            div.className = 'frame-thumbnail';
            div.innerHTML = `
                <img src="/api/video/frame/${this.jobId}/${frameNumber}" alt="Frame ${frameNumber}">
                <button class="remove-btn" onclick="app.removeFrame(${frameNumber})">×</button>
                <div class="frame-info">Frame ${frameNumber}</div>
            `;
            this.framesList.appendChild(div);
        }
    }

    async analyzeVideo() {
        this.analyzeBtn.disabled = true;
        this.analysisProgress.classList.remove('hidden');
        this.setStatus('Analysiere Video...');

        const res = await fetch(`/api/analyze/${this.jobId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                num_frames: parseInt(this.numScreenshots.value),
                project_type: this.projectType.value
            })
        });

        // Poll for status
        const pollInterval = setInterval(async () => {
            const statusRes = await fetch(`/api/analyze/status/${this.jobId}`);
            const status = await statusRes.json();

            if (status.status === 'analyzing') {
                const progress = (status.progress / status.total) * 100;
                this.analysisProgressFill.style.width = progress + '%';
                this.analysisProgressText.textContent = `Analysiere... ${Math.round(progress)}%`;
            } else if (status.status === 'analyzed') {
                clearInterval(pollInterval);
                this.analysisProgress.classList.add('hidden');
                this.analyzeBtn.disabled = false;

                // Add frames
                this.selectedFrames = status.frames.map(f => f.frame_number);
                this.renderFramesList();
                this.updateExportButton();
                this.setStatus(`Analyse abgeschlossen – ${status.frames.length} Frames gefunden`);
            } else if (status.status === 'error') {
                clearInterval(pollInterval);
                this.analysisProgress.classList.add('hidden');
                this.analyzeBtn.disabled = false;
                this.setStatus('Fehler: ' + status.error);
            }
        }, 500);
    }

    async loadLut(e) {
        const file = e.target.files[0];
        if (!file) return;

        const reader = new FileReader();
        reader.onload = () => {
            this.lutData = btoa(reader.result);
            this.lutLabel.textContent = '✓ ' + file.name;
            this.lutLabel.style.color = '#34c759';
            this.applyLut.disabled = false;
            this.previewLut.disabled = false;
            this.setStatus('LUT geladen: ' + file.name);
        };
        reader.readAsBinaryString(file);
    }

    updateQualityVisibility() {
        const format = this.exportFormat.value;
        if (format === 'JPG' || format === 'WebP') {
            this.qualitySlider.disabled = false;
            this.qualityInfo.textContent = 'Nur für JPG/WebP';
        } else {
            this.qualitySlider.disabled = true;
            this.qualityInfo.textContent = 'Verlustfrei';
        }
    }

    updateExportButton() {
        this.exportBtn.disabled = this.selectedFrames.length === 0;
    }

    async exportFrames() {
        if (this.selectedFrames.length === 0) {
            this.setStatus('Keine Frames ausgewählt');
            return;
        }

        this.exportBtn.disabled = true;
        this.setStatus('Exportiere Screenshots...');

        const res = await fetch(`/api/export/${this.jobId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                frames: this.selectedFrames,
                format: this.exportFormat.value,
                quality: parseInt(this.qualitySlider.value),
                apply_lut: this.applyLut.checked,
                lut_data: this.applyLut.checked ? this.lutData : null
            })
        });

        if (res.ok) {
            // Download ZIP
            const blob = await res.blob();
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `screenshots.zip`;
            a.click();
            URL.revokeObjectURL(url);
            this.setStatus(`${this.selectedFrames.length} Screenshots exportiert`);
        } else {
            this.setStatus('Export fehlgeschlagen');
        }

        this.exportBtn.disabled = false;
    }

    setStatus(text) {
        this.statusText.textContent = text;
    }

    formatTimestamp(seconds) {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins.toString().padStart(2, '0')}:${secs.toFixed(2).padStart(5, '0')}`;
    }

    formatSize(bytes) {
        if (bytes < 1024) return bytes + ' B';
        if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
        if (bytes < 1024 * 1024 * 1024) return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
        return (bytes / (1024 * 1024 * 1024)).toFixed(2) + ' GB';
    }
}

// Initialize app
const app = new ScreenshotTool();
