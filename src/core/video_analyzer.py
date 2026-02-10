"""
Video Analyzer - Main engine for analyzing video files and extracting frames
Optimized for long videos (3h+) with intelligent sampling
"""
import cv2
import numpy as np
from pathlib import Path
from typing import List, Tuple, Optional, Callable, Generator
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

from .frame_scorer import FrameScorer
from .motion_analyzer import MotionAnalyzer


@dataclass
class VideoInfo:
    """Container for video metadata."""
    path: str
    width: int
    height: int
    fps: float
    frame_count: int
    duration: float  # in seconds
    codec: str


@dataclass
class SelectedFrame:
    """Container for a selected frame."""
    frame_number: int
    timestamp: float  # in seconds
    image: np.ndarray
    score: float
    score_details: dict
    is_manual: bool = False


class VideoAnalyzer:
    """
    Main class for video analysis and frame extraction.
    Optimized for long videos with intelligent sampling.
    """

    SUPPORTED_FORMATS = ['.mp4', '.mov', '.mkv', '.avi', '.webm', '.m4v']

    # Sampling configuration based on video length
    SAMPLING_CONFIG = {
        # (max_duration_seconds, target_samples, min_interval_seconds)
        300: (500, 2),       # < 5 min: 500 samples, min 2s apart
        1800: (400, 5),      # < 30 min: 400 samples, min 5s apart
        7200: (300, 15),     # < 2h: 300 samples, min 15s apart
        14400: (250, 30),    # < 4h: 250 samples, min 30s apart
        float('inf'): (200, 60),  # > 4h: 200 samples, min 60s apart
    }

    def __init__(self):
        self.video_path: Optional[str] = None
        self.video_capture: Optional[cv2.VideoCapture] = None
        self.video_info: Optional[VideoInfo] = None
        self.frame_scorer = FrameScorer(fast_mode=True)
        self._lock = threading.Lock()

    def load_video(self, filepath: str) -> Optional[VideoInfo]:
        """Load a video file and extract metadata."""
        path = Path(filepath)
        if not path.exists():
            return None

        if path.suffix.lower() not in self.SUPPORTED_FORMATS:
            return None

        self.close()

        cap = cv2.VideoCapture(str(filepath))
        if not cap.isOpened():
            return None

        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fourcc = int(cap.get(cv2.CAP_PROP_FOURCC))

        codec = "".join([chr((fourcc >> 8 * i) & 0xFF) for i in range(4)])

        duration = frame_count / fps if fps > 0 else 0

        self.video_capture = cap
        self.video_path = filepath
        self.video_info = VideoInfo(
            path=filepath,
            width=width,
            height=height,
            fps=fps,
            frame_count=frame_count,
            duration=duration,
            codec=codec
        )

        self.frame_scorer.reset()

        return self.video_info

    def _get_sampling_config(self) -> Tuple[int, int]:
        """Get sampling configuration based on video duration."""
        if self.video_info is None:
            return (300, 10)

        duration = self.video_info.duration
        for max_duration, (target_samples, min_interval) in self.SAMPLING_CONFIG.items():
            if duration <= max_duration:
                return (target_samples, min_interval)

        return (200, 60)

    def _calculate_sample_positions(self, num_samples: int, min_interval_sec: float) -> List[int]:
        """
        Calculate frame positions to sample, distributed evenly across video.

        Returns list of frame numbers to analyze.
        """
        if self.video_info is None:
            return []

        fps = self.video_info.fps
        total_frames = self.video_info.frame_count
        min_interval_frames = int(min_interval_sec * fps)

        # Calculate even distribution
        interval = max(min_interval_frames, total_frames // num_samples)

        positions = []
        pos = int(fps * 5)  # Start 5 seconds in (skip intro)

        while pos < total_frames - int(fps * 5):  # End 5 seconds before end
            positions.append(pos)
            pos += interval

        return positions

    def get_frame_at_position(self, frame_number: int) -> Optional[np.ndarray]:
        """Get a specific frame by frame number (thread-safe)."""
        if self.video_capture is None:
            return None

        if frame_number < 0 or frame_number >= self.video_info.frame_count:
            return None

        with self._lock:
            self.video_capture.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            ret, frame = self.video_capture.read()

        if ret:
            return frame
        return None

    def get_frame_at_time(self, timestamp: float) -> Optional[np.ndarray]:
        """Get a frame at a specific timestamp."""
        if self.video_info is None:
            return None

        frame_number = int(timestamp * self.video_info.fps)
        return self.get_frame_at_position(frame_number)

    def analyze_video(
        self,
        num_frames: int = 5,
        sample_interval: int = 10,  # Ignored, kept for compatibility
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> List[SelectedFrame]:
        """
        Analyze the video and find the best frames.
        Uses intelligent sampling based on video duration.

        Args:
            num_frames: Number of best frames to find
            sample_interval: Ignored (kept for compatibility)
            progress_callback: Callback function(current, total) for progress updates

        Returns:
            List of SelectedFrame objects
        """
        if self.video_capture is None or self.video_info is None:
            return []

        self.frame_scorer.reset()

        # Get optimal sampling configuration
        target_samples, min_interval_sec = self._get_sampling_config()
        sample_positions = self._calculate_sample_positions(target_samples, min_interval_sec)

        total_samples = len(sample_positions)

        if progress_callback:
            progress_callback(0, total_samples)

        # Phase 1: Quick sharpness pre-filter
        motion_analyzer = MotionAnalyzer(fast_mode=True)
        candidates = []

        for i, frame_num in enumerate(sample_positions):
            frame = self.get_frame_at_position(frame_num)
            if frame is None:
                continue

            # Ultra-fast sharpness check
            sharpness = motion_analyzer.calculate_sharpness_fast(frame)

            # Only keep reasonably sharp frames
            if sharpness > 0.15:
                candidates.append((frame_num, frame, sharpness))

            if progress_callback:
                progress_callback(i + 1, total_samples)

        # Phase 2: Full scoring on candidates only
        scored_frames = []
        for frame_num, frame, sharpness in candidates:
            scores = self.frame_scorer.score_frame(frame)
            scored_frames.append((frame_num, scores['total_score'], scores, frame))

        # Sort by score and select best with minimum interval
        scored_frames.sort(key=lambda x: x[1], reverse=True)

        # Minimum interval between selected frames (in frames)
        min_frame_interval = max(
            int(self.video_info.fps * 30),  # At least 30 seconds apart
            self.video_info.frame_count // (num_frames * 2)
        )

        selected = []
        for frame_num, score, details, frame in scored_frames:
            if len(selected) >= num_frames:
                break

            # Check interval constraint
            too_close = False
            for sel_frame_num, _, _, _ in selected:
                if abs(frame_num - sel_frame_num) < min_frame_interval:
                    too_close = True
                    break

            if not too_close:
                selected.append((frame_num, score, details, frame))

        # Sort by timestamp for chronological order
        selected.sort(key=lambda x: x[0])

        # Convert to SelectedFrame objects
        result = []
        for frame_num, score, details, frame in selected:
            timestamp = frame_num / self.video_info.fps
            result.append(SelectedFrame(
                frame_number=frame_num,
                timestamp=timestamp,
                image=frame,
                score=score,
                score_details=details,
                is_manual=False
            ))

        return result

    def analyze_video_parallel(
        self,
        num_frames: int = 5,
        progress_callback: Optional[Callable[[int, int], None]] = None,
        num_workers: int = 4
    ) -> List[SelectedFrame]:
        """
        Analyze video using parallel processing for even faster results.

        Note: Requires creating separate VideoCapture for each thread.
        """
        if self.video_info is None:
            return []

        # Get sampling config
        target_samples, min_interval_sec = self._get_sampling_config()
        sample_positions = self._calculate_sample_positions(target_samples, min_interval_sec)
        total_samples = len(sample_positions)

        # Split positions among workers
        chunks = [sample_positions[i::num_workers] for i in range(num_workers)]

        results = []
        completed = [0]
        lock = threading.Lock()

        def analyze_chunk(positions: List[int], video_path: str) -> List[Tuple]:
            """Analyze a chunk of positions with own VideoCapture."""
            cap = cv2.VideoCapture(video_path)
            motion_analyzer = MotionAnalyzer(fast_mode=True)
            frame_scorer = FrameScorer(fast_mode=True)
            chunk_results = []

            for frame_num in positions:
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
                ret, frame = cap.read()
                if not ret:
                    continue

                # Quick sharpness check
                sharpness = motion_analyzer.calculate_sharpness_fast(frame)
                if sharpness > 0.15:
                    scores = frame_scorer.score_frame(frame)
                    chunk_results.append((frame_num, scores['total_score'], scores, frame))

                with lock:
                    completed[0] += 1
                    if progress_callback:
                        progress_callback(completed[0], total_samples)

            cap.release()
            return chunk_results

        # Run analysis in parallel
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = [
                executor.submit(analyze_chunk, chunk, self.video_path)
                for chunk in chunks if chunk
            ]

            for future in as_completed(futures):
                results.extend(future.result())

        # Sort and select best frames
        results.sort(key=lambda x: x[1], reverse=True)

        min_frame_interval = max(
            int(self.video_info.fps * 30),
            self.video_info.frame_count // (num_frames * 2)
        )

        selected = []
        for frame_num, score, details, frame in results:
            if len(selected) >= num_frames:
                break

            too_close = any(
                abs(frame_num - sel[0]) < min_frame_interval
                for sel in selected
            )

            if not too_close:
                selected.append((frame_num, score, details, frame))

        selected.sort(key=lambda x: x[0])

        return [
            SelectedFrame(
                frame_number=fn,
                timestamp=fn / self.video_info.fps,
                image=img,
                score=sc,
                score_details=det,
                is_manual=False
            )
            for fn, sc, det, img in selected
        ]

    def create_manual_frame(self, frame_number: int) -> Optional[SelectedFrame]:
        """Create a SelectedFrame from a manually chosen position."""
        frame = self.get_frame_at_position(frame_number)
        if frame is None:
            return None

        scores = self.frame_scorer.score_frame(frame)
        timestamp = frame_number / self.video_info.fps

        return SelectedFrame(
            frame_number=frame_number,
            timestamp=timestamp,
            image=frame,
            score=scores['total_score'],
            score_details=scores,
            is_manual=True
        )

    def get_thumbnail(
        self,
        frame: np.ndarray,
        max_size: Tuple[int, int] = (200, 150)
    ) -> np.ndarray:
        """Create a thumbnail from a frame."""
        h, w = frame.shape[:2]
        scale = min(max_size[0] / w, max_size[1] / h)
        new_w = int(w * scale)
        new_h = int(h * scale)

        return cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_AREA)

    def frame_iterator(
        self,
        start: int = 0,
        end: Optional[int] = None,
        step: int = 1
    ) -> Generator[Tuple[int, np.ndarray], None, None]:
        """Iterate over frames in the video."""
        if self.video_capture is None:
            return

        if end is None:
            end = self.video_info.frame_count

        for frame_num in range(start, end, step):
            frame = self.get_frame_at_position(frame_num)
            if frame is not None:
                yield frame_num, frame

    def close(self):
        """Release video resources."""
        if self.video_capture is not None:
            self.video_capture.release()
            self.video_capture = None
        self.video_info = None
        self.video_path = None

    def __del__(self):
        self.close()

    @staticmethod
    def is_supported_format(filepath: str) -> bool:
        """Check if a file format is supported."""
        return Path(filepath).suffix.lower() in VideoAnalyzer.SUPPORTED_FORMATS

    @staticmethod
    def format_timestamp(seconds: float) -> str:
        """Format seconds as HH:MM:SS.ms string."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        ms = int((seconds % 1) * 100)

        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}.{ms:02d}"
        return f"{minutes:02d}:{secs:02d}.{ms:02d}"
