"""Style configuration models for presentation generation.

This module defines style configuration schemas for customizing the visual
appearance and formatting of generated presentations.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union, Literal
from uuid import uuid4
from enum import Enum

from pydantic import BaseModel, Field, field_validator, model_validator
from backend.api.models import CamelModel


class StyleType(str, Enum):
    """Type of style configuration."""

    PRESET = "preset"
    CUSTOM = "custom"
    USER = "user"


class ColorScheme(str, Enum):
    """Predefined color schemes."""

    DEFAULT = "default"
    ACADEMIC = "academic"
    CREATIVE = "creative"
    CORPORATE = "corporate"
    MINIMAL = "minimal"
    DARK = "dark"

    @classmethod
    def list_all(cls) -> List[str]:
        """Get all available color schemes."""
        return [scheme.value for scheme in cls]


class FontFamily(str, Enum):
    """Available font families."""

    DEFAULT = "default"
    SERIF = "serif"
    SANS_SERIF = "sans_serif"
    MONOSPACE = "monospace"
    MODERN = "modern"
    CLASSIC = "classic"
    PLAYFUL = "playful"

    @classmethod
    def list_all(cls) -> List[str]:
        """Get all available font families."""
        return [font.value for font in cls]


class LayoutType(str, Enum):
    """Available layout types."""

    STANDARD = "standard"
    CENTERED = "centered"
    LEFT_ALIGNED = "left_aligned"
    TWO_COLUMN = "two_column"
    MODERN = "modern"
    TRADITIONAL = "traditional"

    @classmethod
    def list_all(cls) -> List[str]:
        """Get all available layout types."""
        return [layout.value for layout in cls]


class SlideTransition(str, Enum):
    """Slide transition effects."""

    NONE = "none"
    FADE = "fade"
    SLIDE = "slide"
    PUSH = "push"
    WIPE = "wipe"
    DISSOLVE = "dissolve"

    @classmethod
    def list_all(cls) -> List[str]:
        """Get all available transitions."""
        return [transition.value for transition in cls]


class ColorPalette(CamelModel):
    """Color palette configuration."""

    primary: Optional[str] = Field(
        default="#2563eb",
        description="Primary color (hex format)",
        pattern=r"^#[0-9A-Fa-f]{6}$",
    )
    secondary: Optional[str] = Field(
        default="#64748b",
        description="Secondary color (hex format)",
        pattern=r"^#[0-9A-Fa-f]{6}$",
    )
    accent: Optional[str] = Field(
        default="#f59e0b",
        description="Accent color (hex format)",
        pattern=r"^#[0-9A-Fa-f]{6}$",
    )
    background: Optional[str] = Field(
        default="#ffffff",
        description="Background color (hex format)",
        pattern=r"^#[0-9A-Fa-f]{6}$",
    )
    text: Optional[str] = Field(
        default="#1f2937",
        description="Text color (hex format)",
        pattern=r"^#[0-9A-Fa-f]{6}$",
    )
    text_light: Optional[str] = Field(
        default="#6b7280",
        description="Light text color (hex format)",
        pattern=r"^#[0-9A-Fa-f]{6}$",
    )
    error: Optional[str] = Field(
        default="#dc2626",
        description="Error color (hex format)",
        pattern=r"^#[0-9A-Fa-f]{6}$",
    )
    success: Optional[str] = Field(
        default="#16a34a",
        description="Success color (hex format)",
        pattern=r"^#[0-9A-Fa-f]{6}$",
    )

    @field_validator(
        "primary",
        "secondary",
        "accent",
        "background",
        "text",
        "text_light",
        "error",
        "success",
    )
    @classmethod
    def validate_hex_color(cls, v):
        """Validate that color is a valid hex color."""
        if not v:
            return v
        if not v.startswith("#") or len(v) != 7:
            raise ValueError("Color must be in hex format (#RRGGBB)")
        return v

    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary with non-None values."""
        return {k: v for k, v in self.model_dump().items() if v is not None}


class FontConfig(CamelModel):
    """Font configuration settings."""

    family: FontFamily = Field(default=FontFamily.DEFAULT, description="Font family")
    size_title: int = Field(
        default=48, ge=24, le=96, description="Title font size in points"
    )
    size_subtitle: int = Field(
        default=32, ge=16, le=72, description="Subtitle font size in points"
    )
    size_body: int = Field(
        default=24, ge=12, le=48, description="Body font size in points"
    )
    size_small: int = Field(
        default=18, ge=10, le=36, description="Small text font size in points"
    )
    weight_title: str = Field(default="bold", description="Title font weight")
    weight_subtitle: str = Field(default="semibold", description="Subtitle font weight")
    weight_body: str = Field(default="normal", description="Body font weight")
    line_height_title: float = Field(
        default=1.2, ge=0.8, le=2.0, description="Title line height"
    )
    line_height_body: float = Field(
        default=1.5, ge=0.8, le=2.0, description="Body line height"
    )

    @field_validator("weight_title", "weight_subtitle", "weight_body")
    @classmethod
    def validate_font_weight(cls, v):
        """Validate font weight values."""
        valid_weights = ["normal", "bold", "semibold", "light", "medium", "heavy"]
        if v.lower() not in valid_weights:
            raise ValueError(f"Font weight must be one of: {valid_weights}")
        return v.lower()


class LayoutConfig(CamelModel):
    """Layout configuration settings."""

    type: LayoutType = Field(default=LayoutType.STANDARD, description="Layout type")
    margin_horizontal: float = Field(
        default=0.1,
        ge=0.0,
        le=0.3,
        description="Horizontal margin as fraction of slide width",
    )
    margin_vertical: float = Field(
        default=0.1,
        ge=0.0,
        le=0.3,
        description="Vertical margin as fraction of slide height",
    )
    spacing_section: float = Field(
        default=1.5, ge=0.5, le=3.0, description="Spacing between sections in em"
    )
    spacing_item: float = Field(
        default=1.0, ge=0.3, le=2.0, description="Spacing between items in em"
    )
    content_max_width: float = Field(
        default=0.8,
        ge=0.3,
        le=1.0,
        description="Max content width as fraction of slide width",
    )
    header_height: float = Field(
        default=0.15,
        ge=0.05,
        le=0.3,
        description="Header height as fraction of slide height",
    )
    footer_height: float = Field(
        default=0.1,
        ge=0.0,
        le=0.2,
        description="Footer height as fraction of slide height",
    )


class TransitionConfig(CamelModel):
    """Slide transition configuration."""

    type: SlideTransition = Field(
        default=SlideTransition.FADE, description="Transition type"
    )
    duration: float = Field(
        default=0.5, ge=0.1, le=5.0, description="Transition duration in seconds"
    )
    speed: str = Field(default="medium", description="Transition speed")

    @field_validator("speed")
    @classmethod
    def validate_speed(cls, v):
        """Validate transition speed."""
        valid_speeds = ["slow", "medium", "fast"]
        if v.lower() not in valid_speeds:
            raise ValueError(f"Transition speed must be one of: {valid_speeds}")
        return v.lower()


class StyleConfig(CamelModel):
    """Complete style configuration for presentations."""

    id: str = Field(
        default_factory=lambda: str(uuid4()), description="Unique style identifier"
    )
    name: str = Field(..., min_length=1, max_length=100, description="Style name")
    description: Optional[str] = Field(
        None, max_length=500, description="Style description"
    )

    # Style metadata
    type: StyleType = Field(default=StyleType.CUSTOM, description="Style type")
    user_id: Optional[str] = Field(None, description="User ID for user-specific styles")
    is_public: bool = Field(
        default=False, description="Whether style is publicly available"
    )
    is_active: bool = Field(default=True, description="Whether style is active")

    # Color and visual configuration
    color_scheme: ColorScheme = Field(
        default=ColorScheme.DEFAULT, description="Color scheme"
    )
    colors: ColorPalette = Field(
        default_factory=ColorPalette, description="Custom color palette"
    )

    # Typography
    fonts: FontConfig = Field(
        default_factory=FontConfig, description="Font configuration"
    )

    # Layout
    layout: LayoutConfig = Field(
        default_factory=LayoutConfig, description="Layout configuration"
    )

    # Transitions and animation
    transitions: TransitionConfig = Field(
        default_factory=TransitionConfig, description="Transition configuration"
    )

    # Content style
    show_progress_indicator: bool = Field(
        default=True, description="Show progress indicator on slides"
    )
    show_slide_numbers: bool = Field(default=True, description="Show slide numbers")
    show_section_headers: bool = Field(default=True, description="Show section headers")
    use_animations: bool = Field(default=False, description="Use animations")

    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return self.model_dump(mode="json")

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StyleConfig":
        """Create from dictionary."""
        return cls.model_validate(data)

    @model_validator(mode="before")
    def validate_style_consistency(cls, data):
        """Validate style configuration consistency."""
        # If using a preset scheme, ensure colors align with scheme defaults where not overridden
        if isinstance(data, dict):
            color_scheme = data.get("color_scheme")
            colors = data.get("colors")

            if (
                color_scheme == ColorScheme.DARK
                and colors
                and not colors.get("background")
            ):
                colors["background"] = "#1f2937"  # Dark background for dark theme
                data["colors"] = colors

        return data

    def update_timestamp(self):
        """Update the updated_at timestamp."""
        self.updated_at = datetime.now(timezone.utc)


class PresetStyle(CamelModel):
    """Preset style definition."""

    id: str
    name: str
    description: str
    config: StyleConfig

    @classmethod
    def get_default_presets(cls) -> List["PresetStyle"]:
        """Get the default built-in preset styles."""

        # Default style
        default_config = StyleConfig(
            id="default",
            name="Default",
            description="Clean, professional default style",
            type=StyleType.PRESET,
            color_scheme=ColorScheme.DEFAULT,
            is_public=True,
        )

        # Academic style
        academic_colors = ColorPalette(
            primary="#1e40af",
            secondary="#6b7280",
            accent="#dc2626",
            background="#ffffff",
            text="#1f2937",
        )
        academic_fonts = FontConfig(
            family=FontFamily.SERIF, size_title=54, size_body=26
        )
        academic_config = StyleConfig(
            id="academic",
            name="Academic",
            description="Formal academic style suitable for educational presentations",
            type=StyleType.PRESET,
            color_scheme=ColorScheme.ACADEMIC,
            colors=academic_colors,
            fonts=academic_fonts,
            is_public=True,
        )

        # Creative style
        creative_colors = ColorPalette(
            primary="#7c3aed",
            secondary="#ec4899",
            accent="#f59e0b",
            background="#fef3c7",
            text="#1f2937",
        )
        creative_fonts = FontConfig(
            family=FontFamily.MODERN, size_title=52, weight_subtitle="medium"
        )
        creative_config = StyleConfig(
            id="creative",
            name="Creative",
            description="Vibrant, creative style with bold colors",
            type=StyleType.PRESET,
            color_scheme=ColorScheme.CREATIVE,
            colors=creative_colors,
            fonts=creative_fonts,
            layout=LayoutConfig(type=LayoutType.MODERN),
            is_public=True,
        )

        # Corporate style
        corporate_colors = ColorPalette(
            primary="#1e293b",
            secondary="#64748b",
            accent="#0ea5e9",
            background="#f8fafc",
            text="#1e293b",
        )
        corporate_fonts = FontConfig(
            family=FontFamily.SANS_SERIF,
            size_title=50,
            size_body=24,
            weight_title="bold",
            weight_body="medium",
        )
        corporate_config = StyleConfig(
            id="corporate",
            name="Corporate",
            description="Professional corporate style with conservative colors",
            type=StyleType.PRESET,
            color_scheme=ColorScheme.CORPORATE,
            colors=corporate_colors,
            fonts=corporate_fonts,
            layout=LayoutConfig(type=LayoutType.TWO_COLUMN),
            transitions=TransitionConfig(type=SlideTransition.NONE),
            is_public=True,
        )

        return [
            cls(
                id="default",
                name="Default",
                description=default_config.name,
                config=default_config,
            ),
            cls(
                id="academic",
                name="Academic",
                description=academic_config.name,
                config=academic_config,
            ),
            cls(
                id="creative",
                name="Creative",
                description=creative_config.name,
                config=creative_config,
            ),
            cls(
                id="corporate",
                name="Corporate",
                description=corporate_config.name,
                config=corporate_config,
            ),
        ]

    @classmethod
    def get_preset_by_id(cls, preset_id: str) -> Optional["PresetStyle"]:
        """Get a specific preset by ID."""
        for preset in cls.get_default_presets():
            if preset.id == preset_id:
                return preset
        return None


class StyleTemplate(CamelModel):
    """Style template for creating new styles."""

    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    based_on: Optional[str] = Field(None, description="Base style ID to inherit from")

    # Override configs (optional)
    colors: Optional[ColorPalette] = None
    fonts: Optional[FontConfig] = None
    layout: Optional[LayoutConfig] = None
    transitions: Optional[TransitionConfig] = None

    def create_style(self, user_id: Optional[str] = None) -> StyleConfig:
        """Create a StyleConfig from this template."""

        # Start with default or base style
        if self.based_on:
            base_preset = PresetStyle.get_preset_by_id(self.based_on)
            base_config = base_preset.config if base_preset else StyleConfig()
        else:
            base_config = StyleConfig()

        # Create new style with overrides
        style_data = {
            "name": self.name,
            "description": self.description,
            "type": StyleType.USER,
            "user_id": user_id,
            **base_config.model_dump(
                exclude={
                    "id",
                    "name",
                    "description",
                    "type",
                    "user_id",
                    "created_at",
                    "updated_at",
                }
            ),
        }

        # Apply overrides
        if self.colors:
            style_data["colors"] = self.colors
        if self.fonts:
            style_data["fonts"] = self.fonts
        if self.layout:
            style_data["layout"] = self.layout
        if self.transitions:
            style_data["transitions"] = self.transitions

        return StyleConfig(**style_data)


# Style validation functions
def validate_style_config(style: StyleConfig) -> bool:
    """Validate a style configuration."""
    try:
        # Ensure all colors are valid hex
        for color_key, color_value in style.colors.to_dict().items():
            if color_value and not color_value.startswith("#"):
                return False

        # Validate font sizes are reasonable
        if not (12 <= style.fonts.size_body <= 72):
            return False

        # Validate layout margins are reasonable
        if not (0 <= style.layout.margin_horizontal <= 0.3):
            return False

        return True
    except Exception:
        return False


def merge_styles(base: StyleConfig, override: StyleConfig) -> StyleConfig:
    """Merge two style configurations, with override taking precedence."""
    base_data = base.model_dump()
    override_data = override.model_dump()

    # Create merged data
    merged = {**base_data, **override_data}

    # For nested configs, merge at the field level
    if override.colors:
        merged["colors"] = {**base_data["colors"], **override_data["colors"]}
    if override.fonts:
        merged["fonts"] = {**base_data["fonts"], **override_data["fonts"]}
    if override.layout:
        merged["layout"] = {**base_data["layout"], **override_data["layout"]}
    if override.transitions:
        merged["transitions"] = {
            **base_data["transitions"],
            **override_data["transitions"],
        }

    return StyleConfig(**merged)


# Style export/import functions
def export_style_config(style: StyleConfig) -> Dict[str, Any]:
    """Export style configuration to JSON-serializable dictionary."""
    return style.to_dict()


def import_style_config(
    data: Dict[str, Any], validate: bool = True
) -> Optional[StyleConfig]:
    """Import style configuration from dictionary."""
    try:
        style = StyleConfig.from_dict(data)
        if validate and not validate_style_config(style):
            return None
        return style
    except Exception:
        return None
