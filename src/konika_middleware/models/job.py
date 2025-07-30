"""Print job models."""

from enum import Enum
from typing import Optional, Any, Dict
from datetime import datetime
from pydantic import BaseModel, Field, validator


class JobStatus(str, Enum):
    """Print job status states."""
    PENDING = "pending"
    QUEUED = "queued"
    PROCESSING = "processing"
    PRINTING = "printing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PaperSize(str, Enum):
    """Supported paper sizes."""
    A4 = "A4"
    A3 = "A3"
    LETTER = "Letter" 
    LEGAL = "Legal"
    TABLOID = "Tabloid"


class ColorMode(str, Enum):
    """Color printing modes."""
    COLOR = "color"
    GRAYSCALE = "grayscale"
    MONOCHROME = "monochrome"


class DuplexMode(str, Enum):
    """Duplex printing modes."""
    SIMPLEX = "simplex"
    DUPLEX_LONG_EDGE = "duplex_long_edge"
    DUPLEX_SHORT_EDGE = "duplex_short_edge"


class PrintQuality(str, Enum):
    """Print quality settings."""
    DRAFT = "draft"
    NORMAL = "normal"
    HIGH = "high"
    BEST = "best"


class PrintSettings(BaseModel):
    """Print job settings and preferences."""
    
    # Basic settings
    copies: int = Field(default=1, ge=1, le=999, description="Number of copies")
    paper_size: PaperSize = Field(default=PaperSize.A4, description="Paper size")
    color_mode: ColorMode = Field(default=ColorMode.COLOR, description="Color mode")
    duplex_mode: DuplexMode = Field(default=DuplexMode.SIMPLEX, description="Duplex mode")
    quality: PrintQuality = Field(default=PrintQuality.NORMAL, description="Print quality")
    
    # Advanced settings
    collate: bool = Field(default=True, description="Collate pages")
    staple: bool = Field(default=False, description="Staple documents")
    hole_punch: bool = Field(default=False, description="Hole punch")
    
    # Page settings
    orientation: str = Field(default="portrait", description="Page orientation")
    pages_per_sheet: int = Field(default=1, ge=1, le=16, description="Pages per sheet")
    scale: float = Field(default=100.0, ge=25.0, le=400.0, description="Scale percentage")
    
    # Paper source
    paper_source: Optional[str] = Field(None, description="Paper tray/source")
    
    @validator('orientation')
    def validate_orientation(cls, v):
        """Validate orientation values."""
        if v.lower() not in ['portrait', 'landscape']:
            raise ValueError('Orientation must be portrait or landscape')
        return v.lower()


class PrintJob(BaseModel):
    """Print job model."""
    
    id: str = Field(..., description="Unique job identifier")
    title: str = Field(..., description="Job title/name")
    status: JobStatus = Field(default=JobStatus.PENDING, description="Current job status")
    
    # Job source
    user_id: Optional[str] = Field(None, description="User who submitted the job")
    platform_job_id: Optional[str] = Field(None, description="External platform job ID")
    
    # File information
    file_path: str = Field(..., description="Path to the file to print")
    file_type: str = Field(..., description="File type (PDF, JPEG, etc.)")
    file_size: int = Field(..., description="File size in bytes")
    page_count: Optional[int] = Field(None, description="Number of pages")
    
    # Print settings
    settings: PrintSettings = Field(default_factory=PrintSettings)
    
    # Device assignment
    device_id: Optional[str] = Field(None, description="Assigned device ID")
    device_name: Optional[str] = Field(None, description="Assigned device name")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Progress and status
    progress_percent: float = Field(default=0.0, ge=0.0, le=100.0)
    pages_printed: int = Field(default=0, ge=0)
    error_message: Optional[str] = None
    
    # Cost and accounting
    estimated_cost: Optional[float] = None
    actual_cost: Optional[float] = None
    
    # Retry information
    retry_count: int = Field(default=0, ge=0)
    max_retries: int = Field(default=3, ge=0)
    
    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class PrintJobRequest(BaseModel):
    """Request model for submitting print jobs."""
    
    title: str = Field(..., description="Job title")
    file_data: bytes = Field(..., description="File content as bytes")
    file_type: str = Field(..., description="File type")
    
    # Optional settings
    settings: Optional[PrintSettings] = None
    device_id: Optional[str] = Field(None, description="Preferred device ID")
    priority: int = Field(default=5, ge=1, le=10, description="Job priority (1=highest)")
    
    # External reference
    user_id: Optional[str] = None
    platform_job_id: Optional[str] = None


class PrintJobResponse(BaseModel):
    """Response model for print job operations."""
    
    job_id: str
    status: JobStatus
    message: str
    estimated_completion: Optional[datetime] = None


class JobListResponse(BaseModel):
    """Response model for job listing."""
    
    jobs: list[PrintJob]
    total_count: int
    pending_count: int
    processing_count: int
    completed_count: int
    failed_count: int