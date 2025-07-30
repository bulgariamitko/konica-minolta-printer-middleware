"""Custom exceptions for the middleware."""


class MiddlewareError(Exception):
    """Base exception for middleware-related errors."""
    
    def __init__(self, message: str, error_code: str = None, details: dict = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or "MIDDLEWARE_ERROR"
        self.details = details or {}


class DeviceError(MiddlewareError):
    """Exception for device-related errors."""
    
    def __init__(self, message: str, device_id: str = None, error_code: str = None, details: dict = None):
        super().__init__(message, error_code or "DEVICE_ERROR", details)
        self.device_id = device_id


class DeviceConnectionError(DeviceError):
    """Exception for device connection errors."""
    
    def __init__(self, message: str, device_id: str = None, details: dict = None):
        super().__init__(message, device_id, "DEVICE_CONNECTION_ERROR", details)


class DeviceAuthenticationError(DeviceError):
    """Exception for device authentication errors."""
    
    def __init__(self, message: str, device_id: str = None, details: dict = None):
        super().__init__(message, device_id, "DEVICE_AUTH_ERROR", details)


class DeviceNotFoundError(DeviceError):
    """Exception when device is not found."""
    
    def __init__(self, device_id: str):
        super().__init__(f"Device not found: {device_id}", device_id, "DEVICE_NOT_FOUND")


class JobError(MiddlewareError):
    """Exception for job-related errors."""
    
    def __init__(self, message: str, job_id: str = None, error_code: str = None, details: dict = None):
        super().__init__(message, error_code or "JOB_ERROR", details)
        self.job_id = job_id


class JobNotFoundError(JobError):
    """Exception when job is not found."""
    
    def __init__(self, job_id: str):
        super().__init__(f"Job not found: {job_id}", job_id, "JOB_NOT_FOUND")


class JobValidationError(JobError):
    """Exception for job validation errors."""
    
    def __init__(self, message: str, job_id: str = None, details: dict = None):
        super().__init__(message, job_id, "JOB_VALIDATION_ERROR", details)


class PrinterBusyError(DeviceError):
    """Exception when printer is busy and cannot accept new jobs."""
    
    def __init__(self, device_id: str, current_job_id: str = None):
        message = f"Printer {device_id} is busy"
        if current_job_id:
            message += f" with job {current_job_id}"
        super().__init__(message, device_id, "PRINTER_BUSY")
        self.current_job_id = current_job_id


class UnsupportedFileTypeError(JobError):
    """Exception for unsupported file types."""
    
    def __init__(self, file_type: str, job_id: str = None):
        super().__init__(f"Unsupported file type: {file_type}", job_id, "UNSUPPORTED_FILE_TYPE")
        self.file_type = file_type


class InsufficientResourcesError(DeviceError):
    """Exception when device lacks resources (paper, toner, etc.)."""
    
    def __init__(self, device_id: str, resource: str, current_level: int = None):
        message = f"Insufficient {resource} on device {device_id}"
        if current_level is not None:
            message += f" (current level: {current_level}%)"
        super().__init__(message, device_id, "INSUFFICIENT_RESOURCES")
        self.resource = resource
        self.current_level = current_level