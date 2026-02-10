"""
Face Detector - Detects faces in video frames using OpenCV
Optimized for fast detection on long videos
"""
import cv2
import numpy as np
from pathlib import Path
from typing import List, Tuple, Optional


class FaceDetector:
    """Detects faces in images using OpenCV Haar Cascades."""

    def __init__(self, fast_mode: bool = True):
        """
        Initialize face detector.

        Args:
            fast_mode: If True, uses faster detection with lower accuracy
        """
        # Load Haar Cascade classifiers
        cv2_data_path = cv2.data.haarcascades

        self.face_cascade = cv2.CascadeClassifier(
            cv2_data_path + 'haarcascade_frontalface_default.xml'
        )
        self.eye_cascade = cv2.CascadeClassifier(
            cv2_data_path + 'haarcascade_eye.xml'
        )
        self.profile_cascade = cv2.CascadeClassifier(
            cv2_data_path + 'haarcascade_profileface.xml'
        )

        self.fast_mode = fast_mode
        # Detection parameters based on mode
        if fast_mode:
            self.scale_factor = 1.2  # Faster but less accurate
            self.min_neighbors = 3
            self.detection_width = 320  # Process at lower resolution
        else:
            self.scale_factor = 1.1
            self.min_neighbors = 5
            self.detection_width = 640

    def _prepare_frame(self, frame: np.ndarray) -> Tuple[np.ndarray, float]:
        """
        Prepare frame for detection (resize for speed).

        Returns:
            Tuple of (resized_gray_frame, scale_factor)
        """
        h, w = frame.shape[:2]
        scale = self.detection_width / w if w > self.detection_width else 1.0

        if scale < 1.0:
            new_w = int(w * scale)
            new_h = int(h * scale)
            resized = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_AREA)
        else:
            resized = frame
            scale = 1.0

        gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
        return gray, scale

    def detect_faces(self, frame: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """
        Detect faces in a frame.

        Args:
            frame: BGR image as numpy array

        Returns:
            List of face rectangles (x, y, w, h)
        """
        gray, scale = self._prepare_frame(frame)
        min_size = int(40 * scale) if self.fast_mode else int(60 * scale)

        # Detect frontal faces
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=self.scale_factor,
            minNeighbors=self.min_neighbors,
            minSize=(min_size, min_size)
        )

        # Scale coordinates back to original size
        all_faces = []
        if len(faces) > 0:
            for (x, y, w, h) in faces:
                all_faces.append((
                    int(x / scale),
                    int(y / scale),
                    int(w / scale),
                    int(h / scale)
                ))

        # Skip profile detection in fast mode
        if not self.fast_mode:
            profiles = self.profile_cascade.detectMultiScale(
                gray,
                scaleFactor=self.scale_factor,
                minNeighbors=self.min_neighbors,
                minSize=(min_size, min_size)
            )
            if len(profiles) > 0:
                for (x, y, w, h) in profiles:
                    scaled_profile = (
                        int(x / scale),
                        int(y / scale),
                        int(w / scale),
                        int(h / scale)
                    )
                    if not self._is_overlapping(scaled_profile, all_faces):
                        all_faces.append(scaled_profile)

        return all_faces

    def detect_faces_fast(self, frame: np.ndarray) -> bool:
        """
        Quick check if any faces are present.

        Args:
            frame: BGR image

        Returns:
            True if at least one face detected
        """
        gray, scale = self._prepare_frame(frame)
        min_size = int(40 * scale)

        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.3,  # Even faster
            minNeighbors=2,
            minSize=(min_size, min_size),
            flags=cv2.CASCADE_SCALE_IMAGE
        )

        return len(faces) > 0

    def _is_overlapping(
        self,
        rect: Tuple[int, int, int, int],
        rects: List[Tuple[int, int, int, int]],
        threshold: float = 0.5
    ) -> bool:
        """Check if a rectangle overlaps significantly with any in the list."""
        x1, y1, w1, h1 = rect
        for x2, y2, w2, h2 in rects:
            ix = max(0, min(x1 + w1, x2 + w2) - max(x1, x2))
            iy = max(0, min(y1 + h1, y2 + h2) - max(y1, y2))
            intersection = ix * iy
            area1 = w1 * h1
            area2 = w2 * h2
            union = area1 + area2 - intersection
            if union > 0 and intersection / union > threshold:
                return True
        return False

    def calculate_face_score(self, frame: np.ndarray, skip_eyes: bool = True) -> float:
        """
        Calculate a face quality score for a frame.

        Args:
            frame: BGR image
            skip_eyes: Skip eye detection for speed

        Returns:
            Score between 0 and 1
        """
        faces = self.detect_faces(frame)

        if len(faces) == 0:
            return 0.0

        height, width = frame.shape[:2]
        frame_area = width * height
        frame_center_x = width / 2
        frame_center_y = height / 2

        max_score = 0.0

        for face in faces:
            x, y, w, h = face
            face_area = w * h

            # Size score (larger faces are better, up to a point)
            size_ratio = face_area / frame_area
            size_score = min(1.0, size_ratio * 10)

            # Position score (centered is better)
            face_center_x = x + w / 2
            face_center_y = y + h / 2
            dist_x = abs(face_center_x - frame_center_x) / (width / 2)
            dist_y = abs(face_center_y - frame_center_y) / (height / 2)
            position_score = 1.0 - (dist_x * 0.5 + dist_y * 0.5)

            # Skip eye detection in fast mode
            if skip_eyes:
                eye_score = 0.5  # Assume average
            else:
                eyes = self._detect_eyes_in_face(frame, face)
                eye_score = min(1.0, len(eyes) / 2)

            face_score = (size_score * 0.35 + position_score * 0.35 + eye_score * 0.3)
            max_score = max(max_score, face_score)

        # Bonus for multiple faces (podcast with multiple hosts)
        multi_face_bonus = min(0.15, (len(faces) - 1) * 0.075)

        return min(1.0, max_score + multi_face_bonus)

    def _detect_eyes_in_face(
        self,
        frame: np.ndarray,
        face_rect: Tuple[int, int, int, int]
    ) -> List[Tuple[int, int, int, int]]:
        """Detect eyes within a face region."""
        x, y, w, h = face_rect
        face_roi = frame[y:y+h, x:x+w]
        gray_roi = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY)

        eyes = self.eye_cascade.detectMultiScale(
            gray_roi,
            scaleFactor=1.1,
            minNeighbors=3,
            minSize=(20, 20),
            maxSize=(w // 2, h // 2)
        )

        return list(eyes)
