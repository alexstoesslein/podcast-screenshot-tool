"""
Motion Analyzer - Analyzes frame sharpness and motion blur
Optimized for fast analysis on long videos
"""
import cv2
import numpy as np
from typing import Optional, Tuple


class MotionAnalyzer:
    """Analyzes frames for sharpness and motion blur."""

    def __init__(self, fast_mode: bool = True):
        """
        Initialize motion analyzer.

        Args:
            fast_mode: If True, uses faster analysis with lower accuracy
        """
        self.previous_frame = None
        self.fast_mode = fast_mode
        # Analysis resolution
        self.analysis_width = 320 if fast_mode else 640

    def _prepare_frame(self, frame: np.ndarray) -> np.ndarray:
        """Resize frame for faster analysis."""
        h, w = frame.shape[:2]
        if w > self.analysis_width:
            scale = self.analysis_width / w
            new_w = int(w * scale)
            new_h = int(h * scale)
            return cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_AREA)
        return frame

    def calculate_sharpness(self, frame: np.ndarray) -> float:
        """
        Calculate sharpness score using Laplacian variance.

        Args:
            frame: BGR image

        Returns:
            Sharpness score (normalized 0-1)
        """
        # Work on smaller image for speed
        small = self._prepare_frame(frame)
        gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)

        # Calculate Laplacian variance
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        variance = laplacian.var()

        # Normalize to 0-1 range
        normalized = min(1.0, variance / 500.0)

        return normalized

    def calculate_sharpness_fast(self, frame: np.ndarray) -> float:
        """
        Ultra-fast sharpness check for pre-filtering.

        Args:
            frame: BGR image

        Returns:
            Sharpness score (normalized 0-1)
        """
        # Very small image for quick check
        h, w = frame.shape[:2]
        small = cv2.resize(frame, (160, int(160 * h / w)), interpolation=cv2.INTER_AREA)
        gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)

        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        variance = laplacian.var()

        return min(1.0, variance / 500.0)

    def calculate_motion_blur(self, frame: np.ndarray) -> float:
        """
        Estimate motion blur in the frame.

        Args:
            frame: BGR image

        Returns:
            Motion blur score (0 = no blur, 1 = heavy blur)
        """
        if self.fast_mode:
            # Skip FFT in fast mode, use simpler edge detection
            return self._calculate_blur_simple(frame)

        small = self._prepare_frame(frame)
        gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)

        # Apply FFT
        f = np.fft.fft2(gray)
        fshift = np.fft.fftshift(f)
        magnitude = np.log(np.abs(fshift) + 1)

        rows, cols = magnitude.shape
        center_row, center_col = rows // 2, cols // 2

        h_profile = magnitude[center_row, :]
        v_profile = magnitude[:, center_col]

        h_var = np.var(h_profile)
        v_var = np.var(v_profile)
        avg_var = (h_var + v_var) / 2

        blur_score = 1.0 - min(1.0, avg_var / 10.0)

        return blur_score

    def _calculate_blur_simple(self, frame: np.ndarray) -> float:
        """Simple blur detection using edge strength."""
        small = self._prepare_frame(frame)
        gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)

        # Sobel edge detection
        sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        sobely = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)

        # Edge magnitude
        edge_strength = np.mean(np.abs(sobelx) + np.abs(sobely))

        # Higher edge strength = less blur
        # Normalize (typical values 10-100)
        blur_score = 1.0 - min(1.0, edge_strength / 80.0)

        return blur_score

    def calculate_frame_difference(
        self,
        frame: np.ndarray,
        reference_frame: Optional[np.ndarray] = None
    ) -> float:
        """
        Calculate difference between current frame and reference.

        Args:
            frame: Current BGR frame
            reference_frame: Reference frame (uses previous if None)

        Returns:
            Difference score (0 = identical, 1 = very different)
        """
        small = self._prepare_frame(frame)

        if reference_frame is None:
            if self.previous_frame is None:
                self.previous_frame = small.copy()
                return 0.0
            reference_frame = self.previous_frame
        else:
            reference_frame = self._prepare_frame(reference_frame)

        # Ensure same size
        if small.shape != reference_frame.shape:
            reference_frame = cv2.resize(
                reference_frame,
                (small.shape[1], small.shape[0])
            )

        gray1 = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(reference_frame, cv2.COLOR_BGR2GRAY)

        diff = cv2.absdiff(gray1, gray2)
        mean_diff = np.mean(diff)

        normalized = min(1.0, mean_diff / 50.0)

        self.previous_frame = small.copy()

        return normalized

    def calculate_stability_score(self, frame: np.ndarray) -> float:
        """
        Calculate overall stability score.

        Args:
            frame: BGR image

        Returns:
            Stability score (0-1, higher is more stable)
        """
        sharpness = self.calculate_sharpness(frame)

        if self.fast_mode:
            # Skip motion blur and frame diff for speed
            return sharpness
        else:
            motion_blur = self.calculate_motion_blur(frame)
            frame_diff = self.calculate_frame_difference(frame)

            stability = (
                sharpness * 0.5 +
                (1.0 - motion_blur) * 0.3 +
                (1.0 - frame_diff) * 0.2
            )
            return stability

    def reset(self):
        """Reset the analyzer state."""
        self.previous_frame = None
