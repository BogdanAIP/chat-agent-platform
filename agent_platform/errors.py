class PlatformError(Exception):
    """Base error with a stable machine-readable code."""

    code = "PLATFORM_ERROR"
    retryable = False
    safe_to_retry = False

    def as_dict(self) -> dict:
        return {
            "code": self.code,
            "message": str(self),
            "retryable": self.retryable,
            "safe_to_retry": self.safe_to_retry,
        }


class BindingError(PlatformError):
    code = "PROJECT_BINDING_ERROR"


class PolicyDenied(PlatformError):
    code = "POLICY_DENIED"


class ToolUnavailable(PlatformError):
    code = "TOOL_UNAVAILABLE"
    retryable = True
    safe_to_retry = True


class ValidationError(PlatformError):
    code = "VALIDATION_FAILED"

