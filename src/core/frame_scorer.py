"""
Frame Scorer - Combines face detection and motion analysis for frame scoring
Optimized for fast scoring on long videos
"""
import numpy as np
from typing import List, Tuple, Dict
from .face_detector import FaceDetector
from .motion_analyzer import MotionAnalyzer


class FrameScorer:
    """
    Scores video frames based on multiple quality criteria.

    Combines:
    - Face detection (visibility, size, position)
    - Sharpness analysis
    """

    def __init__(
        self,
        face_weight: float = 0.5,
        sharpness_weight: float = 0.3,
        stability_weight: float = 0.2,
        fast_mode: bool = True
    ):
        """
        Initialize the frame scorer.

        Args:
            face_weight: Weight for face detection score (0-1)
            sharpness_weight: Weight for sharpness score (0-1)
            stability_weight: Weight for stability score (0-1)
            fast_mode: Use fast detection algorithms
        """
        self.face_detector = FaceDetector(fast_mode=fast_mode)
        self.motion_analyzer = MotionAnalyzer(fast_mode=fast_mode)
        self.fast_mode = fast_mode

        # Normalize weights
        total = face_weight + sharpness_weight + stability_weight
        self.face_weight = face_weight / total
        self.sharpness_weight = sharpness_weight / total
        self.stability_weight = stability_weight / total

    def score_frame(self, frame: np.ndarray) -> Dict[str, float]:
        """
        Calculate comprehensive score for a single frame.

        Args:
            frame: BGR image as numpy array

        Returns:
            Dictionary with individual scores and total score
        """
        # Calculate individual scores
        face_score = self.face_detector.calculate_face_score(frame, skip_eyes=self.fast_mode)
        sharpness = self.motion_analyzer.calculate_sharpness(frame)

        if self.fast_mode:
            # In fast mode, use sharpness as stability proxy
            stability = sharpness
        else:
            stability = self.motion_analyzer.calculate_stability_score(frame)

        # Calculate weighted total
        total_score = (
            face_score * self.face_weight +
            sharpness * self.sharpness_weight +
            stability * self.stability_weight
        )

        return {
            'face_score': face_score,
            'sharpness': sharpness,
            'stability': stability,
            'total_score': total_score
        }

    def score_frame_fast(self, frame: np.ndarray) -> float:
        """
        Ultra-fast scoring for pre-filtering.

        Args:
            frame: BGR image

        Returns:
            Quick score estimate
        """
        # Just check if faces present and basic sharpness
        has_faces = self.face_detector.detect_faces_fast(frame)
        sharpness = self.motion_analyzer.calculate_sharpness_fast(frame)

        if has_faces:
            return 0.5 + sharpness * 0.5
        else:
            return sharpness * 0.3

    def find_best_frames(
        self,
        frames: List[Tuple[int, np.ndarray]],
        num_frames: int = 5,
        min_interval: int = 30
    ) -> List[Tuple[int, float, Dict[str, float]]]:
        """
        Find the best frames from a list.

        Args:
            frames: List of (frame_number, frame_image) tuples
            num_frames: Number of best frames to return
            min_interval: Minimum frame interval between selected frames

        Returns:
            List of (frame_number, total_score, score_details) tuples
        """
        # Score all frames
        scored_frames = []
        for frame_num, frame in frames:
            scores = self.score_frame(frame)
            scored_frames.append((frame_num, scores['total_score'], scores))

        # Sort by score descending
        scored_frames.sort(key=lambda x: x[1], reverse=True)

        # Select best frames with minimum interval
        selected = []
        for frame_num, score, details in scored_frames:
            if len(selected) >= num_frames:
                break

            # Check interval constraint
            too_close = False
            for selected_num, _, _ in selected:
                if abs(frame_num - selected_num) < min_interval:
                    too_close = True
                    break

            if not too_close:
                selected.append((frame_num, score, details))

        # Sort by frame number for chronological order
        selected.sort(key=lambda x: x[0])

        return selected

    def reset(self):
        """Reset analyzer state for new video."""
        self.motion_analyzer.reset()

    def set_weights(
        self,
        face_weight: float,
        sharpness_weight: float,
        stability_weight: float
    ):
        """Update scoring weights."""
        total = face_weight + sharpness_weight + stability_weight
        self.face_weight = face_weight / total
        self.sharpness_weight = sharpness_weight / total
        self.stability_weight = stability_weight / total
