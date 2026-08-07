use serde::Serialize;
use thiserror::Error;

#[derive(Debug, Error)]
pub enum PlatformError {
    #[error("{0}")]
    Binding(String),
    #[error("{0}")]
    PolicyDenied(String),
    #[error("{0}")]
    SecretDenied(String),
    #[error("{0}")]
    ToolUnavailable(String),
    #[error("{0}")]
    ToolTimeout(String),
    #[error("{0}")]
    Validation(String),
    #[error("{context}: {source}")]
    Io {
        context: String,
        #[source]
        source: std::io::Error,
    },
}

#[derive(Debug, Serialize)]
pub struct ErrorPayload<'a> {
    pub code: &'a str,
    pub message: String,
    pub retryable: bool,
    pub safe_to_retry: bool,
}

impl PlatformError {
    #[must_use]
    pub const fn code(&self) -> &'static str {
        match self {
            Self::Binding(_) => "PROJECT_BINDING_ERROR",
            Self::PolicyDenied(_) => "POLICY_DENIED",
            Self::SecretDenied(_) => "SECRET_ACCESS_DENIED",
            Self::ToolUnavailable(_) => "TOOL_UNAVAILABLE",
            Self::ToolTimeout(_) => "TOOL_TIMEOUT",
            Self::Validation(_) | Self::Io { .. } => "VALIDATION_FAILED",
        }
    }

    #[must_use]
    pub const fn retryable(&self) -> bool {
        matches!(self, Self::ToolUnavailable(_) | Self::ToolTimeout(_))
    }

    #[must_use]
    pub fn payload(&self) -> ErrorPayload<'_> {
        ErrorPayload {
            code: self.code(),
            message: self.to_string(),
            retryable: self.retryable(),
            safe_to_retry: self.retryable(),
        }
    }
}

pub fn io_error(context: impl Into<String>, source: std::io::Error) -> PlatformError {
    PlatformError::Io {
        context: context.into(),
        source,
    }
}
