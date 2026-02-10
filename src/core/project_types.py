"""
Project Types - Defines different project types with their analysis settings
"""
from dataclasses import dataclass
from typing import Dict


@dataclass
class ProjectTypeSettings:
    """Settings for a specific project type."""
    name: str
    description: str
    # Scoring weights
    face_weight: float
    sharpness_weight: float
    stability_weight: float
    # Detection settings
    require_faces: bool
    motion_blur_penalty: float  # 0.0 = no penalty, 1.0 = heavy penalty
    # Sampling adjustments
    min_sharpness_threshold: float


class ProjectTypes:
    """Available project types with their settings."""

    TYPES: Dict[str, ProjectTypeSettings] = {
        "Podcast": ProjectTypeSettings(
            name="Podcast",
            description="Optimiert fuer Podcast-Aufnahmen mit Personen",
            face_weight=0.5,
            sharpness_weight=0.3,
            stability_weight=0.2,
            require_faces=True,
            motion_blur_penalty=0.8,
            min_sharpness_threshold=0.15
        ),
        "Dokumentation": ProjectTypeSettings(
            name="Dokumentation",
            description="Fuer Dokumentationen - visuell ansprechende Frames",
            face_weight=0.2,
            sharpness_weight=0.5,
            stability_weight=0.3,
            require_faces=False,
            motion_blur_penalty=0.3,
            min_sharpness_threshold=0.1
        ),
        "Commercial": ProjectTypeSettings(
            name="Commercial",
            description="Fuer Werbung - aesthetische, dynamische Frames",
            face_weight=0.3,
            sharpness_weight=0.4,
            stability_weight=0.3,
            require_faces=False,
            motion_blur_penalty=0.1,  # Motion blur kann aesthetisch sein
            min_sharpness_threshold=0.08
        ),
        "Interview": ProjectTypeSettings(
            name="Interview",
            description="Fuer Interviews - Fokus auf Gesichter und Ausdruck",
            face_weight=0.6,
            sharpness_weight=0.25,
            stability_weight=0.15,
            require_faces=True,
            motion_blur_penalty=0.7,
            min_sharpness_threshold=0.12
        ),
        "B-Roll": ProjectTypeSettings(
            name="B-Roll",
            description="Fuer B-Roll Material - visuelle Vielfalt",
            face_weight=0.1,
            sharpness_weight=0.5,
            stability_weight=0.4,
            require_faces=False,
            motion_blur_penalty=0.2,
            min_sharpness_threshold=0.05
        ),
    }

    @classmethod
    def get_type_names(cls) -> list:
        """Get list of available project type names."""
        return list(cls.TYPES.keys())

    @classmethod
    def get_settings(cls, type_name: str) -> ProjectTypeSettings:
        """Get settings for a project type."""
        return cls.TYPES.get(type_name, cls.TYPES["Podcast"])

    @classmethod
    def get_description(cls, type_name: str) -> str:
        """Get description for a project type."""
        settings = cls.TYPES.get(type_name)
        return settings.description if settings else ""
