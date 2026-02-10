"""
Screenshot Exporter - Exports selected frames as image files
"""
import cv2
import numpy as np
from PIL import Image
from pathlib import Path
from typing import List, Optional, Callable
from dataclasses import dataclass

from .video_analyzer import SelectedFrame
from ..utils.lut_processor import LUTProcessor
from ..utils.image_formats import ImageFormats


@dataclass
class ExportSettings:
    """Settings for screenshot export."""
    output_folder: str
    format_name: str = 'PNG'
    quality: int = 95
    prefix: str = 'screenshot'
    apply_lut: bool = False


class ScreenshotExporter:
    """Exports selected frames as image files."""

    def __init__(self, lut_processor: Optional[LUTProcessor] = None):
        """
        Initialize the exporter.

        Args:
            lut_processor: Optional LUT processor for color grading
        """
        self.lut_processor = lut_processor or LUTProcessor()

    def export_frames(
        self,
        frames: List[SelectedFrame],
        settings: ExportSettings,
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> List[str]:
        """
        Export a list of frames to image files.

        Args:
            frames: List of SelectedFrame objects
            settings: Export settings
            progress_callback: Callback(current, total, filename) for progress

        Returns:
            List of exported file paths
        """
        output_path = Path(settings.output_folder)
        output_path.mkdir(parents=True, exist_ok=True)

        extension = ImageFormats.get_extension(settings.format_name)
        exported_files = []

        for i, frame in enumerate(frames):
            # Generate filename
            timestamp_str = self._format_timestamp_filename(frame.timestamp)
            filename = f"{settings.prefix}_{i+1:02d}_{timestamp_str}{extension}"
            filepath = output_path / filename

            # Convert BGR to RGB
            rgb_image = cv2.cvtColor(frame.image, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(rgb_image)

            # Apply LUT if enabled
            if settings.apply_lut and self.lut_processor.is_loaded():
                pil_image = self.lut_processor.apply_to_pil_image(pil_image)

            # Save image
            success = ImageFormats.save_image(
                pil_image,
                str(filepath),
                settings.format_name,
                settings.quality
            )

            if success:
                exported_files.append(str(filepath))

            if progress_callback:
                progress_callback(i + 1, len(frames), filename)

        return exported_files

    def export_single_frame(
        self,
        frame: SelectedFrame,
        filepath: str,
        format_name: str = 'PNG',
        quality: int = 95,
        apply_lut: bool = False
    ) -> bool:
        """
        Export a single frame.

        Args:
            frame: SelectedFrame to export
            filepath: Output file path
            format_name: Image format
            quality: Quality for lossy formats
            apply_lut: Whether to apply loaded LUT

        Returns:
            True if export successful
        """
        # Convert BGR to RGB
        rgb_image = cv2.cvtColor(frame.image, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(rgb_image)

        # Apply LUT if enabled
        if apply_lut and self.lut_processor.is_loaded():
            pil_image = self.lut_processor.apply_to_pil_image(pil_image)

        return ImageFormats.save_image(pil_image, filepath, format_name, quality)

    def preview_with_lut(self, frame: np.ndarray) -> np.ndarray:
        """
        Generate a preview of a frame with LUT applied.

        Args:
            frame: BGR image

        Returns:
            BGR image with LUT applied
        """
        if not self.lut_processor.is_loaded():
            return frame

        # Convert BGR to RGB for LUT processing
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Apply LUT
        rgb_result = self.lut_processor.apply_to_image(rgb)

        # Convert back to BGR
        return cv2.cvtColor(rgb_result, cv2.COLOR_RGB2BGR)

    def load_lut(self, filepath: str) -> bool:
        """Load a LUT file."""
        return self.lut_processor.load_cube(filepath)

    def clear_lut(self):
        """Clear the loaded LUT."""
        self.lut_processor.clear()

    def is_lut_loaded(self) -> bool:
        """Check if a LUT is loaded."""
        return self.lut_processor.is_loaded()

    def get_lut_name(self) -> str:
        """Get the name of the loaded LUT."""
        return self.lut_processor.get_lut_name()

    def _format_timestamp_filename(self, seconds: float) -> str:
        """Format timestamp for use in filename."""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        ms = int((seconds % 1) * 100)
        return f"{minutes:02d}m{secs:02d}s{ms:02d}"

    @staticmethod
    def get_available_formats() -> List[str]:
        """Get list of available export formats."""
        return ImageFormats.get_format_list()
