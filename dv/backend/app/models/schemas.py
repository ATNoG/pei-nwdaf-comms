"""
Pydantic models for data validation.
"""
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field, HttpUrl, field_validator
from pydantic.config import ConfigDict


class BoxAttribute(BaseModel):
    """Single attribute/parameter for a box."""
    name: str = Field(..., min_length=1, max_length=100)
    type: str = Field(..., pattern=r"^(ok_nok|text)$")
    url: Optional[HttpUrl] = None
    label: str = Field(..., min_length=1, max_length=200)


class ContainerBoxBase(BaseModel):
    """Base container box model."""

    name: str = Field(..., min_length=1, max_length=100)
    x: float = Field(default=0, ge=-10000, le=10000)
    y: float = Field(default=0, ge=-10000, le=10000)
    status_url: Optional[HttpUrl] = None
    parameters: Dict[str, Dict[str, str]] = Field(default_factory=dict)
    attributes: List[BoxAttribute] = Field(default_factory=list)
    expanded: bool = False
    visible_on_map: List[str] = Field(default_factory=list)
    width: Optional[float] = Field(default=200, gt=0, le=2000)
    height: Optional[float] = Field(default=150, gt=0, le=2000)


class ContainerBox(ContainerBoxBase):
    """Full container box model with ID."""

    model_config = ConfigDict(
        json_encoders={HttpUrl: str},
        populate_by_name=True,
    )

    id: str = Field(..., min_length=1, max_length=50)
    type: str = "container"
    position: Optional[Dict[str, float]] = None
    data: Optional[Dict[str, str]] = None
    statusData: Optional[Dict[str, Any]] = Field(default=None)


class ConnectionLineBase(BaseModel):
    """Base connection line model."""

    source_box_id: str = Field(..., min_length=1, max_length=50)
    target_box_id: str = Field(..., min_length=1, max_length=50)
    color: str = Field(default="#000000", pattern=r"^#[0-9A-Fa-f]{6}$")
    polling_interval: int = Field(default=2, ge=1, le=300)
    change_on_response: bool = False
    red_on_failure: bool = False


class ConnectionLine(ConnectionLineBase):
    """Full connection line model with ID and status."""

    id: str = Field(..., min_length=1, max_length=50)
    status: str = "unknown"
    type: str = "smoothstep"
    animated: bool = False
    x1: Optional[float] = None
    y1: Optional[float] = None
    x2: Optional[float] = None
    y2: Optional[float] = None


class ImageLayerBase(BaseModel):
    """Base image layer model."""

    name: str = Field(..., min_length=1, max_length=100)
    layer_type: str = Field(..., pattern=r"^(background|foreground)$")
    url: str = Field(..., min_length=1, max_length=500)
    x: float = Field(default=0, ge=-10000, le=10000)
    y: float = Field(default=0, ge=-10000, le=10000)
    width: float = Field(default=100, gt=0, le=10000)
    height: float = Field(default=100, gt=0, le=10000)


class ImageLayer(ImageLayerBase):
    """Full image layer model with ID."""

    id: str = Field(..., min_length=1, max_length=50)


class FrameBase(BaseModel):
    """Base frame model - transparent rectangle with colored border."""

    name: str = Field(..., min_length=1, max_length=100)
    x: float = Field(default=0, ge=-10000, le=10000)
    y: float = Field(default=0, ge=-10000, le=10000)
    width: float = Field(default=400, gt=0, le=10000)
    height: float = Field(default=300, gt=0, le=10000)
    border_color: str = Field(default="#3b82f6", pattern=r"^#[0-9A-Fa-f]{6}$")
    border_width: float = Field(default=2, ge=1, le=20)
    border_style: str = Field(default="solid", pattern=r"^(solid|dashed|dotted|double)")


class Frame(FrameBase):
    """Full frame model with ID."""

    id: str = Field(..., min_length=1, max_length=50)


class DashboardState(BaseModel):
    """Complete dashboard state model."""

    model_config = {"arbitrary_types_allowed": True}

    boxes: List[ContainerBox] = Field(default_factory=list)
    lines: List[ConnectionLine] = Field(default_factory=list)
    images: List[ImageLayer] = Field(default_factory=list)
    frames: List[Frame] = Field(default_factory=list)
    locked: bool = False
    zoom: float = Field(default=1.0, ge=0.1, le=5.0)
    pan_x: float = Field(default=0, ge=-10000, le=10000)
    pan_y: float = Field(default=0, ge=-10000, le=10000)


class StatusResponse(BaseModel):
    """Status check response model."""

    status: str = Field(..., pattern=r"^(ok|warning|nok|unknown)$")
    value: Union[str, int]
    parameters: Dict[str, Dict] = Field(default_factory=dict)


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str
    version: str
    timestamp: str


class FileUploadResponse(BaseModel):
    """File upload response model."""

    filename: str
    url: str
    size: Optional[int] = None


class ViewSettings(BaseModel):
    """View settings model."""

    zoom: float = Field(default=1.0, ge=0.1, le=5.0)
    pan_x: float = Field(default=0)
    pan_y: float = Field(default=0)
