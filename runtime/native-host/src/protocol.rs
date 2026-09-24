use serde::Deserialize;
use serde::Serialize;
use std::collections::BTreeMap;
use std::fmt;
use std::io;
use std::io::Read;
use std::io::Write;
use std::path::Path;

pub const PROTOCOL_VERSION: u32 = 1;
pub const MAX_FRAME_BYTES: usize = 262_144;
pub const MAX_IDENTIFIER_BYTES: usize = 128;
pub const MAX_ARGV: usize = 256;
pub const MAX_ARG_BYTES: usize = 8_192;
pub const MAX_ENV_ENTRIES: usize = 256;
pub const MAX_ENV_NAME_CHARS: usize = 128;
pub const MAX_ENV_VALUE_BYTES: usize = 8_192;
pub const MAX_ENV_VALUE_BYTES_TOTAL: usize = 65_536;
pub const MAX_WINDOWS_COMMAND_LINE_UTF16: usize = 30_000;
pub const MAX_PATH_UTF16: usize = 32_767;
pub const MAX_OUTPUT_BYTES: u64 = 8_388_608;
pub const MAX_RUNTIME_MS: u64 = 3_600_000;
pub const MAX_RAW_OUTPUT_CHUNK: usize = 32_768;

#[derive(Debug)]
pub enum ProtocolError {
    Io(io::Error),
    Json(serde_json::Error),
    InvalidFrame(&'static str),
    InvalidMessage(String),
}

impl fmt::Display for ProtocolError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Io(error) => write!(f, "protocol I/O error: {error}"),
            Self::Json(error) => write!(f, "protocol JSON error: {error}"),
            Self::InvalidFrame(message) => write!(f, "invalid protocol frame: {message}"),
            Self::InvalidMessage(message) => write!(f, "invalid protocol message: {message}"),
        }
    }
}

impl std::error::Error for ProtocolError {}

impl From<io::Error> for ProtocolError {
    fn from(value: io::Error) -> Self {
        Self::Io(value)
    }
}

impl From<serde_json::Error> for ProtocolError {
    fn from(value: serde_json::Error) -> Self {
        Self::Json(value)
    }
}

pub fn read_frame<R: Read>(reader: &mut R) -> Result<Option<Vec<u8>>, ProtocolError> {
    let mut prefix = [0_u8; 4];
    let mut read = 0;
    while read < prefix.len() {
        match reader.read(&mut prefix[read..]) {
            Ok(0) if read == 0 => return Ok(None),
            Ok(0) => return Err(ProtocolError::InvalidFrame("truncated length prefix")),
            Ok(count) => read += count,
            Err(error) if error.kind() == io::ErrorKind::Interrupted => continue,
            Err(error) => return Err(error.into()),
        }
    }

    let length = u32::from_be_bytes(prefix) as usize;
    if length == 0 {
        return Err(ProtocolError::InvalidFrame("zero-length payload"));
    }
    if length > MAX_FRAME_BYTES {
        return Err(ProtocolError::InvalidFrame("payload exceeds hard frame ceiling"));
    }

    let mut payload = vec![0_u8; length];
    reader.read_exact(&mut payload)?;
    std::str::from_utf8(&payload)
        .map_err(|_| ProtocolError::InvalidFrame("payload is not valid UTF-8"))?;
    Ok(Some(payload))
}

pub fn write_frame<W: Write, T: Serialize>(
    writer: &mut W,
    value: &T,
) -> Result<(), ProtocolError> {
    let payload = serde_json::to_vec(value)?;
    if payload.is_empty() || payload.len() > MAX_FRAME_BYTES {
        return Err(ProtocolError::InvalidFrame(
            "serialized payload exceeds frame bounds",
        ));
    }
    writer.write_all(&(payload.len() as u32).to_be_bytes())?;
    writer.write_all(&payload)?;
    writer.flush()?;
    Ok(())
}

#[derive(Clone, Debug, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct BeginOperation {
    #[serde(rename = "type")]
    pub message_type: String,
    pub protocol_version: u32,
    pub request_id: String,
    pub logical_operation_id: String,
    pub attempt_id: String,
    pub authorization_ref: String,
    pub native_operation_ref: String,
    pub executable: String,
    pub argv: Vec<String>,
    pub cwd: String,
    pub env: BTreeMap<String, String>,
    pub max_runtime_ms: u64,
    pub max_output_bytes: u64,
    pub containment_required: bool,
}

#[derive(Clone, Debug, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct CancelOperation {
    #[serde(rename = "type")]
    pub message_type: String,
    pub protocol_version: u32,
    pub request_id: String,
    pub attempt_id: String,
}

#[derive(Debug)]
pub enum ClientMessage {
    Begin(BeginOperation),
    Cancel(CancelOperation),
}

pub fn parse_client_message(payload: &[u8]) -> Result<ClientMessage, ProtocolError> {
    let value: serde_json::Value = serde_json::from_slice(payload)?;
    let message_type = value
        .get("type")
        .and_then(serde_json::Value::as_str)
        .ok_or_else(|| ProtocolError::InvalidMessage("missing string type".to_owned()))?;

    match message_type {
        "begin_operation" => Ok(ClientMessage::Begin(serde_json::from_value(value)?)),
        "cancel_operation" => Ok(ClientMessage::Cancel(serde_json::from_value(value)?)),
        other => Err(ProtocolError::InvalidMessage(format!(
            "unknown message type {other:?}"
        ))),
    }
}

#[derive(Clone, Debug)]
pub struct OperationIdentity {
    pub request_id: String,
    pub logical_operation_id: String,
    pub attempt_id: String,
    pub authorization_ref: String,
    pub native_operation_ref: String,
}

impl From<&BeginOperation> for OperationIdentity {
    fn from(value: &BeginOperation) -> Self {
        Self {
            request_id: value.request_id.clone(),
            logical_operation_id: value.logical_operation_id.clone(),
            attempt_id: value.attempt_id.clone(),
            authorization_ref: value.authorization_ref.clone(),
            native_operation_ref: value.native_operation_ref.clone(),
        }
    }
}

impl BeginOperation {
    pub fn validate(&self) -> Result<(), ProtocolError> {
        if self.message_type != "begin_operation" {
            return invalid("BeginOperation type mismatch");
        }
        if self.protocol_version != PROTOCOL_VERSION {
            return invalid("unsupported protocol_version");
        }
        validate_identifier("request_id", &self.request_id)?;
        validate_identifier("logical_operation_id", &self.logical_operation_id)?;
        validate_identifier("attempt_id", &self.attempt_id)?;
        validate_identifier("authorization_ref", &self.authorization_ref)?;
        validate_identifier("native_operation_ref", &self.native_operation_ref)?;

        validate_path("executable", &self.executable)?;
        validate_path("cwd", &self.cwd)?;
        if !Path::new(&self.executable).is_absolute() {
            return invalid("executable must be an absolute path");
        }
        if !Path::new(&self.cwd).is_absolute() {
            return invalid("cwd must be an absolute path");
        }

        if self.argv.len() > MAX_ARGV {
            return invalid("argv exceeds hard count ceiling");
        }
        for arg in &self.argv {
            if arg.as_bytes().len() > MAX_ARG_BYTES {
                return invalid("argv element exceeds hard byte ceiling");
            }
            if arg.contains('\0') {
                return invalid("argv contains NUL");
            }
        }

        if self.env.len() > MAX_ENV_ENTRIES {
            return invalid("environment exceeds hard entry ceiling");
        }
        let mut total_values = 0_usize;
        for (name, value) in &self.env {
            if name.is_empty() || name.chars().count() > MAX_ENV_NAME_CHARS {
                return invalid("environment name exceeds bounds");
            }
            if name.contains('=') || name.contains('\0') {
                return invalid("environment name contains forbidden character");
            }
            if value.contains('\0') || value.as_bytes().len() > MAX_ENV_VALUE_BYTES {
                return invalid("environment value exceeds bounds");
            }
            total_values = total_values
                .checked_add(value.as_bytes().len())
                .ok_or_else(|| ProtocolError::InvalidMessage("environment size overflow".into()))?;
        }
        if total_values > MAX_ENV_VALUE_BYTES_TOTAL {
            return invalid("environment values exceed aggregate byte ceiling");
        }

        if !(1..=MAX_RUNTIME_MS).contains(&self.max_runtime_ms) {
            return invalid("max_runtime_ms outside hard bounds");
        }
        if self.max_output_bytes > MAX_OUTPUT_BYTES {
            return invalid("max_output_bytes exceeds hard ceiling");
        }
        if !self.containment_required {
            return invalid("containment_required must be true");
        }
        Ok(())
    }
}

impl CancelOperation {
    pub fn validate_for(&self, identity: &OperationIdentity) -> Result<(), ProtocolError> {
        if self.message_type != "cancel_operation" {
            return invalid("CancelOperation type mismatch");
        }
        if self.protocol_version != PROTOCOL_VERSION {
            return invalid("unsupported protocol_version");
        }
        validate_identifier("request_id", &self.request_id)?;
        validate_identifier("attempt_id", &self.attempt_id)?;
        if self.request_id != identity.request_id || self.attempt_id != identity.attempt_id {
            return invalid("CancelOperation identity mismatch");
        }
        Ok(())
    }
}

fn validate_identifier(name: &str, value: &str) -> Result<(), ProtocolError> {
    if value.is_empty() || value.as_bytes().len() > MAX_IDENTIFIER_BYTES {
        return Err(ProtocolError::InvalidMessage(format!(
            "{name} exceeds identifier bounds"
        )));
    }
    if !value
        .bytes()
        .all(|byte| byte.is_ascii() && !byte.is_ascii_control())
    {
        return Err(ProtocolError::InvalidMessage(format!(
            "{name} must contain printable ASCII only"
        )));
    }
    Ok(())
}

fn validate_path(name: &str, value: &str) -> Result<(), ProtocolError> {
    if value.is_empty() || value.contains('\0') || value.encode_utf16().count() > MAX_PATH_UTF16 {
        return Err(ProtocolError::InvalidMessage(format!(
            "{name} exceeds path bounds"
        )));
    }
    Ok(())
}

fn invalid<T>(message: &str) -> Result<T, ProtocolError> {
    Err(ProtocolError::InvalidMessage(message.to_owned()))
}

#[cfg(test)]
mod tests {
    use super::*;

    fn valid_begin() -> BeginOperation {
        BeginOperation {
            message_type: "begin_operation".into(),
            protocol_version: PROTOCOL_VERSION,
            request_id: "request-1".into(),
            logical_operation_id: "logical-1".into(),
            attempt_id: "attempt-1".into(),
            authorization_ref: "grant:abc".into(),
            native_operation_ref: "native:abc".into(),
            executable: if cfg!(windows) {
                r"C:\Windows\System32\cmd.exe".into()
            } else {
                "/bin/echo".into()
            },
            argv: vec!["hello".into()],
            cwd: if cfg!(windows) {
                r"C:\Windows".into()
            } else {
                "/tmp".into()
            },
            env: BTreeMap::new(),
            max_runtime_ms: 1_000,
            max_output_bytes: 4_096,
            containment_required: true,
        }
    }

    #[test]
    fn frame_round_trip() {
        #[derive(Serialize)]
        struct Sample<'a> {
            value: &'a str,
        }
        let mut encoded = Vec::new();
        write_frame(&mut encoded, &Sample { value: "ok" }).unwrap();
        let decoded = read_frame(&mut encoded.as_slice()).unwrap().unwrap();
        assert_eq!(serde_json::from_slice::<serde_json::Value>(&decoded).unwrap()["value"], "ok");
    }

    #[test]
    fn rejects_zero_length_frame() {
        let error = read_frame(&mut [0_u8; 4].as_slice()).unwrap_err();
        assert!(matches!(error, ProtocolError::InvalidFrame(_)));
    }

    #[test]
    fn begin_validation_is_bounded() {
        let begin = valid_begin();
        begin.validate().unwrap();

        let mut invalid_begin = begin.clone();
        invalid_begin.argv = (0..=MAX_ARGV).map(|_| "x".into()).collect();
        assert!(invalid_begin.validate().is_err());
    }

    #[test]
    fn rejects_unknown_message_fields() {
        let payload = br#"{
          "type":"cancel_operation",
          "protocol_version":1,
          "request_id":"request-1",
          "attempt_id":"attempt-1",
          "extra":true
        }"#;
        assert!(parse_client_message(payload).is_err());
    }
}

#[cfg(test)]
pub(crate) mod tests_support {
    use super::*;

    pub(crate) fn valid_begin_for_windows() -> BeginOperation {
        BeginOperation {
            message_type: "begin_operation".into(),
            protocol_version: PROTOCOL_VERSION,
            request_id: "request-1".into(),
            logical_operation_id: "logical-1".into(),
            attempt_id: "attempt-1".into(),
            authorization_ref: "grant:abc".into(),
            native_operation_ref: "native:abc".into(),
            executable: r"C:\Windows\System32\cmd.exe".into(),
            argv: vec!["/d".into(), "/c".into(), "echo ok".into()],
            cwd: r"C:\Windows".into(),
            env: BTreeMap::new(),
            max_runtime_ms: 5_000,
            max_output_bytes: 65_536,
            containment_required: true,
        }
    }
}
