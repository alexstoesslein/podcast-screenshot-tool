"""
Image Formats - Handles image format conversion and export
"""
from PIL import Image
from pathlib import Path
from typing import Dict, Any, Optional


class ImageFormats:
    """Handles image format conversion and export settings."""

    FORMATS = {
        'JPG': {
            'extension': '.jpg',
            'pillow_format': 'JPEG',
            'options': {'quality': 95, 'optimize': True}
        },
        'PNG': {
            'extension': '.png',
            'pillow_format': 'PNG',
            'options': {'compress_level': 6}
        },
        'TIFF': {
            'extension': '.tiff',
            'pillow_format': 'TIFF',
            'options': {'compression': 'lzw'}
        },
        'WebP': {
            'extension': '.webp',
            'pillow_format': 'WEBP',
            'options': {'quality': 95, 'method': 4}
        },
        'BMP': {
            'extension': '.bmp',
            'pillow_format': 'BMP',
            'options': {}
        }
    }

    @classmethod
    def get_format_list(cls) -> list:
        """Get list of available format names."""
        return list(cls.FORMATS.keys())

    @classmethod
    def get_extension(cls, format_name: str) -> str:
        """Get file extension for a format."""
        return cls.FORMATS.get(format_name, {}).get('extension', '.png')

    @classmethod
    def save_image(
        cls,
        image: Image.Image,
        filepath: str,
        format_name: str,
        quality: Optional[int] = None
    ) -> bool:
        """
        Save an image in the specified format.

        Args:
            image: PIL Image to save
            filepath: Output file path
            format_name: Format name (JPG, PNG, etc.)
            quality: Optional quality override for lossy formats (1-100)

        Returns:
            True if saved successfully
        """
        try:
            format_info = cls.FORMATS.get(format_name)
            if not format_info:
                return False

            # Ensure correct extension
            path = Path(filepath)
            if path.suffix.lower() != format_info['extension']:
                filepath = str(path.with_suffix(format_info['extension']))

            # Build save options
            options = format_info['options'].copy()

            # Override quality if specified
            if quality is not None and format_name in ['JPG', 'WebP']:
                options['quality'] = max(1, min(100, quality))

            # Convert to RGB for formats that don't support alpha
            if format_name in ['JPG', 'BMP'] and image.mode == 'RGBA':
                image = image.convert('RGB')

            # Save the image
            image.save(filepath, format_info['pillow_format'], **options)
            return True

        except Exception as e:
            print(f"Error saving image: {e}")
            return False

    @classmethod
    def get_format_description(cls, format_name: str) -> str:
        """Get a description of the format."""
        descriptions = {
            'JPG': 'JPEG - Komprimiert, gut fuer Web (verlustbehaftet)',
            'PNG': 'PNG - Verlustfrei, transparenz moeglich',
            'TIFF': 'TIFF - Verlustfrei, fuer Archivierung',
            'WebP': 'WebP - Modern, gute Kompression',
            'BMP': 'BMP - Unkomprimiert, gross'
        }
        return descriptions.get(format_name, format_name)
