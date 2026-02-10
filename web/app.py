"""
Web App for Screenshot Tool
Flask backend with chunked upload support for large video files
"""
import os
import uuid
import json
import threading
from pathlib import Path
from flask import Flask, request, jsonify, send_file, render_template, send_from_directory
from werkzeug.utils import secure_filename

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.video_analyzer import VideoAnalyzer
from src.core.project_types import ProjectTypes
from src.utils.lut_processor import LUTProcessor
from src.utils.image_formats import ImageFormats

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024 * 1024  # 10GB max
app.config['UPLOAD_FOLDER'] = Path(__file__).parent / 'uploads'
app.config['UPLOAD_FOLDER'].mkdir(exist_ok=True)

# Store job status
jobs = {}
jobs_lock = threading.Lock()


class AnalysisJob:
    def __init__(self, job_id, video_path):
        self.job_id = job_id
        self.video_path = video_path
        self.status = 'pending'
        self.progress = 0
        self.total = 0
        self.frames = []
        self.error = None
        self.video_info = None


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/project-types')
def get_project_types():
    """Get available project types."""
    types = ProjectTypes.get_type_names()
    return jsonify({
        'types': types,
        'descriptions': {t: ProjectTypes.get_description(t) for t in types}
    })


@app.route('/api/formats')
def get_formats():
    """Get available export formats."""
    return jsonify({
        'formats': ImageFormats.get_format_list()
    })


@app.route('/api/upload/init', methods=['POST'])
def init_upload():
    """Initialize a chunked upload session."""
    data = request.json
    filename = secure_filename(data.get('filename', 'video.mp4'))
    file_size = data.get('size', 0)

    job_id = str(uuid.uuid4())
    upload_path = app.config['UPLOAD_FOLDER'] / job_id
    upload_path.mkdir(exist_ok=True)

    with jobs_lock:
        jobs[job_id] = {
            'status': 'uploading',
            'filename': filename,
            'file_size': file_size,
            'uploaded_size': 0,
            'chunks_received': set(),
            'upload_path': str(upload_path),
            'video_path': str(upload_path / filename)
        }

    return jsonify({
        'job_id': job_id,
        'chunk_size': 5 * 1024 * 1024  # 5MB chunks
    })


@app.route('/api/upload/chunk/<job_id>', methods=['POST'])
def upload_chunk(job_id):
    """Upload a chunk of the video file."""
    if job_id not in jobs:
        return jsonify({'error': 'Job not found'}), 404

    job = jobs[job_id]
    chunk_index = int(request.form.get('chunk_index', 0))
    total_chunks = int(request.form.get('total_chunks', 1))

    if 'chunk' not in request.files:
        return jsonify({'error': 'No chunk provided'}), 400

    chunk = request.files['chunk']
    chunk_path = Path(job['upload_path']) / f'chunk_{chunk_index:06d}'
    chunk.save(str(chunk_path))

    with jobs_lock:
        job['chunks_received'].add(chunk_index)
        job['uploaded_size'] += os.path.getsize(str(chunk_path))

    # Check if all chunks received
    if len(job['chunks_received']) == total_chunks:
        # Combine chunks
        video_path = Path(job['video_path'])
        with open(video_path, 'wb') as outfile:
            for i in range(total_chunks):
                chunk_path = Path(job['upload_path']) / f'chunk_{i:06d}'
                with open(chunk_path, 'rb') as infile:
                    outfile.write(infile.read())
                chunk_path.unlink()  # Delete chunk

        job['status'] = 'uploaded'
        return jsonify({'status': 'complete', 'job_id': job_id})

    progress = len(job['chunks_received']) / total_chunks * 100
    return jsonify({
        'status': 'uploading',
        'progress': progress,
        'chunks_received': len(job['chunks_received']),
        'total_chunks': total_chunks
    })


@app.route('/api/upload/status/<job_id>')
def upload_status(job_id):
    """Get upload status."""
    if job_id not in jobs:
        return jsonify({'error': 'Job not found'}), 404

    job = jobs[job_id]
    return jsonify({
        'status': job['status'],
        'uploaded_size': job.get('uploaded_size', 0),
        'file_size': job.get('file_size', 0),
        'progress': job.get('uploaded_size', 0) / max(job.get('file_size', 1), 1) * 100
    })


@app.route('/api/video/info/<job_id>')
def video_info(job_id):
    """Get video information."""
    if job_id not in jobs:
        return jsonify({'error': 'Job not found'}), 404

    job = jobs[job_id]
    if job['status'] != 'uploaded' and job['status'] != 'analyzed':
        return jsonify({'error': 'Video not ready'}), 400

    analyzer = VideoAnalyzer()
    info = analyzer.load_video(job['video_path'])
    analyzer.close()

    if info is None:
        return jsonify({'error': 'Could not load video'}), 400

    return jsonify({
        'width': info.width,
        'height': info.height,
        'fps': info.fps,
        'duration': info.duration,
        'frame_count': info.frame_count,
        'duration_formatted': VideoAnalyzer.format_timestamp(info.duration)
    })


@app.route('/api/video/frame/<job_id>/<int:frame_number>')
def get_frame(job_id, frame_number):
    """Get a specific frame as JPEG."""
    if job_id not in jobs:
        return jsonify({'error': 'Job not found'}), 404

    job = jobs[job_id]

    analyzer = VideoAnalyzer()
    analyzer.load_video(job['video_path'])

    frame = analyzer.get_frame_at_position(frame_number)
    analyzer.close()

    if frame is None:
        return jsonify({'error': 'Could not get frame'}), 400

    import cv2
    import io

    # Resize for preview (max 800px width)
    h, w = frame.shape[:2]
    if w > 800:
        scale = 800 / w
        frame = cv2.resize(frame, (800, int(h * scale)))

    _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])

    return send_file(
        io.BytesIO(buffer.tobytes()),
        mimetype='image/jpeg'
    )


@app.route('/api/analyze/<job_id>', methods=['POST'])
def analyze_video(job_id):
    """Start video analysis."""
    if job_id not in jobs:
        return jsonify({'error': 'Job not found'}), 404

    job = jobs[job_id]
    data = request.json or {}

    num_frames = data.get('num_frames', 5)
    project_type = data.get('project_type', 'Podcast')

    # Start analysis in background thread
    def run_analysis():
        try:
            with jobs_lock:
                job['status'] = 'analyzing'
                job['progress'] = 0
                job['total'] = 100

            analyzer = VideoAnalyzer()
            info = analyzer.load_video(job['video_path'])

            if info is None:
                with jobs_lock:
                    job['status'] = 'error'
                    job['error'] = 'Could not load video'
                return

            settings = ProjectTypes.get_settings(project_type)
            analyzer.frame_scorer.set_weights(
                settings.face_weight,
                settings.sharpness_weight,
                settings.stability_weight
            )

            def progress_callback(current, total):
                with jobs_lock:
                    job['progress'] = current
                    job['total'] = total

            frames = analyzer.analyze_video(
                num_frames=num_frames,
                progress_callback=progress_callback
            )

            # Convert frames to serializable format
            frame_data = []
            for f in frames:
                frame_data.append({
                    'frame_number': f.frame_number,
                    'timestamp': f.timestamp,
                    'score': f.score
                })

            with jobs_lock:
                job['status'] = 'analyzed'
                job['frames'] = frame_data

            analyzer.close()

        except Exception as e:
            with jobs_lock:
                job['status'] = 'error'
                job['error'] = str(e)

    thread = threading.Thread(target=run_analysis)
    thread.start()

    return jsonify({'status': 'started', 'job_id': job_id})


@app.route('/api/analyze/status/<job_id>')
def analysis_status(job_id):
    """Get analysis status."""
    if job_id not in jobs:
        return jsonify({'error': 'Job not found'}), 404

    job = jobs[job_id]
    return jsonify({
        'status': job['status'],
        'progress': job.get('progress', 0),
        'total': job.get('total', 100),
        'frames': job.get('frames', []),
        'error': job.get('error')
    })


@app.route('/api/export/<job_id>', methods=['POST'])
def export_frames(job_id):
    """Export selected frames."""
    if job_id not in jobs:
        return jsonify({'error': 'Job not found'}), 404

    job = jobs[job_id]
    data = request.json or {}

    frame_numbers = data.get('frames', [])
    format_name = data.get('format', 'PNG')
    quality = data.get('quality', 95)
    apply_lut = data.get('apply_lut', False)
    lut_data = data.get('lut_data')  # Base64 encoded LUT file

    import cv2
    import io
    import zipfile
    import base64

    analyzer = VideoAnalyzer()
    analyzer.load_video(job['video_path'])

    lut_processor = None
    if apply_lut and lut_data:
        # Save LUT temporarily
        lut_path = Path(job['upload_path']) / 'temp.cube'
        with open(lut_path, 'wb') as f:
            f.write(base64.b64decode(lut_data))
        lut_processor = LUTProcessor()
        lut_processor.load_cube(str(lut_path))

    # Create ZIP with all frames
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        for i, frame_num in enumerate(frame_numbers):
            frame = analyzer.get_frame_at_position(frame_num)
            if frame is None:
                continue

            # Apply LUT if enabled
            if lut_processor and lut_processor.is_loaded():
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame = lut_processor.apply_to_image(frame)
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

            # Encode frame
            ext = ImageFormats.get_extension(format_name)
            params = ImageFormats.get_encoding_params(format_name, quality)
            _, buffer = cv2.imencode(ext, frame, params)

            filename = f'frame_{i+1:03d}_{frame_num}{ext}'
            zf.writestr(filename, buffer.tobytes())

    analyzer.close()
    zip_buffer.seek(0)

    return send_file(
        zip_buffer,
        mimetype='application/zip',
        as_attachment=True,
        download_name=f'screenshots_{job_id[:8]}.zip'
    )


@app.route('/api/cleanup/<job_id>', methods=['DELETE'])
def cleanup_job(job_id):
    """Clean up job files."""
    if job_id not in jobs:
        return jsonify({'error': 'Job not found'}), 404

    job = jobs[job_id]
    upload_path = Path(job['upload_path'])

    # Delete all files
    import shutil
    if upload_path.exists():
        shutil.rmtree(upload_path)

    with jobs_lock:
        del jobs[job_id]

    return jsonify({'status': 'cleaned'})


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5001, debug=True)
