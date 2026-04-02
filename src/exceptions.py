class PipelineError(Exception):
    """Base exception for pipeline failures."""


class ConfigurationError(PipelineError):
    """Raised when runtime configuration is invalid or incomplete."""


class DataQualityError(PipelineError):
    """Raised when dataset validation fails."""


class PipelineStageError(PipelineError):
    """Raised when a pipeline stage cannot complete successfully."""
