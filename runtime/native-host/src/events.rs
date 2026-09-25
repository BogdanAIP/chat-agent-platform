use crate::protocol::OperationIdentity;
use crate::protocol::PROTOCOL_VERSION;
use crate::protocol::ProtocolError;
use crate::protocol::write_frame;
use serde::Serialize;
use std::io::Stdout;
use std::sync::Arc;
use std::sync::Mutex;

#[derive(Clone)]
pub struct ProtocolOutput {
    inner: Arc<Mutex<WriterState>>,
}

struct WriterState {
    stdout: Stdout,
    next_event_seq: u64,
}

impl ProtocolOutput {
    pub fn new(stdout: Stdout) -> Self {
        Self {
            inner: Arc::new(Mutex::new(WriterState {
                stdout,
                next_event_seq: 1,
            })),
        }
    }

    pub fn write_hello(&self, hello: &HostHello) -> Result<(), ProtocolError> {
        let mut state = self
            .inner
            .lock()
            .map_err(|_| ProtocolError::InvalidMessage("stdout lock poisoned".into()))?;
        write_frame(&mut state.stdout, hello)
    }

    pub fn sink(&self, identity: OperationIdentity, host_instance_id: String) -> EventSink {
        EventSink {
            output: self.clone(),
            identity,
            host_instance_id,
        }
    }
}

#[derive(Debug, Serialize)]
pub struct HostHello {
    #[serde(rename = "type")]
    pub message_type: &'static str,
    pub protocol_version: u32,
    pub host_instance_id: String,
    pub build_id: String,
    pub target: String,
}

impl HostHello {
    pub fn new(host_instance_id: String) -> Self {
        Self {
            message_type: "host_hello",
            protocol_version: PROTOCOL_VERSION,
            host_instance_id,
            build_id: option_env!("CAP_NATIVE_HOST_BUILD_ID")
                .unwrap_or(env!("CARGO_PKG_VERSION"))
                .to_owned(),
            target: current_target(),
        }
    }
}

#[derive(Clone)]
pub struct EventSink {
    output: ProtocolOutput,
    identity: OperationIdentity,
    host_instance_id: String,
}

#[derive(Debug, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum DeliveryState {
    NeverRunnable,
    TreeExited,
    Terminated,
    HostFailureAfterStart,
}

#[derive(Debug, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum TerminalReason {
    InvalidBounds,
    JobCreateFailed,
    ProcessCreateFailed,
    JobAssignFailed,
    ProcessResumeFailed,
    Cancelled,
    RuntimeTimeout,
    OutputLimitExceeded,
    OwnerLost,
    ProtocolRejected,
    OutputIntegrityFailed,
    HostInternalFailure,
    #[cfg(not(windows))]
    UnsupportedPlatform,
    TreeExited,
}

#[derive(Debug)]
pub struct TerminalSnapshot {
    pub delivery_state: DeliveryState,
    pub reason: TerminalReason,
    pub root_exit_code: Option<u32>,
    pub target_ever_runnable: bool,
    pub tree_quiescent: bool,
    pub stdout_bytes: u64,
    pub stderr_bytes: u64,
    pub stdout_sha256: String,
    pub stderr_sha256: String,
    pub output_complete: bool,
}

#[derive(Serialize)]
struct EventEnvelope<'a, T: Serialize> {
    #[serde(rename = "type")]
    message_type: &'static str,
    protocol_version: u32,
    host_instance_id: &'a str,
    request_id: &'a str,
    logical_operation_id: &'a str,
    attempt_id: &'a str,
    authorization_ref: &'a str,
    native_operation_ref: &'a str,
    event_seq: u64,
    #[serde(flatten)]
    body: T,
}

#[derive(Serialize)]
struct EmptyBody {}

#[derive(Serialize)]
struct ProcessSpawnedBody {
    process_id: u32,
}

#[derive(Serialize)]
struct OutputChunkBody<'a> {
    stream: &'static str,
    stream_seq: u64,
    encoding: &'static str,
    data: &'a str,
    raw_len: usize,
}

#[derive(Serialize)]
struct RootExitedBody {
    root_exit_code: u32,
}

#[derive(Serialize)]
struct TerminalBody<'a> {
    delivery_state: &'a DeliveryState,
    reason: &'a TerminalReason,
    root_exit_code: Option<u32>,
    target_ever_runnable: bool,
    tree_quiescent: bool,
    stdout_bytes: u64,
    stderr_bytes: u64,
    stdout_sha256: &'a str,
    stderr_sha256: &'a str,
    output_complete: bool,
}

impl EventSink {
    pub fn operation_prepared(&self) -> Result<(), ProtocolError> {
        self.emit("operation_prepared", EmptyBody {})
    }

    pub fn process_spawned(&self, process_id: u32) -> Result<(), ProtocolError> {
        self.emit("process_spawned", ProcessSpawnedBody { process_id })
    }

    pub fn output_chunk(
        &self,
        stream: &'static str,
        stream_seq: u64,
        data: &str,
        raw_len: usize,
    ) -> Result<(), ProtocolError> {
        self.emit(
            "output_chunk",
            OutputChunkBody {
                stream,
                stream_seq,
                encoding: "base64",
                data,
                raw_len,
            },
        )
    }

    pub fn root_exited(&self, root_exit_code: u32) -> Result<(), ProtocolError> {
        self.emit("root_exited", RootExitedBody { root_exit_code })
    }

    pub fn terminal(&self, snapshot: &TerminalSnapshot) -> Result<(), ProtocolError> {
        self.emit(
            "operation_terminal",
            TerminalBody {
                delivery_state: &snapshot.delivery_state,
                reason: &snapshot.reason,
                root_exit_code: snapshot.root_exit_code,
                target_ever_runnable: snapshot.target_ever_runnable,
                tree_quiescent: snapshot.tree_quiescent,
                stdout_bytes: snapshot.stdout_bytes,
                stderr_bytes: snapshot.stderr_bytes,
                stdout_sha256: &snapshot.stdout_sha256,
                stderr_sha256: &snapshot.stderr_sha256,
                output_complete: snapshot.output_complete,
            },
        )
    }

    fn emit<T: Serialize>(&self, message_type: &'static str, body: T) -> Result<(), ProtocolError> {
        let mut state = self
            .output
            .inner
            .lock()
            .map_err(|_| ProtocolError::InvalidMessage("stdout lock poisoned".into()))?;
        let event_seq = state.next_event_seq;
        state.next_event_seq = state
            .next_event_seq
            .checked_add(1)
            .ok_or_else(|| ProtocolError::InvalidMessage("event_seq overflow".into()))?;
        let envelope = EventEnvelope {
            message_type,
            protocol_version: PROTOCOL_VERSION,
            host_instance_id: &self.host_instance_id,
            request_id: &self.identity.request_id,
            logical_operation_id: &self.identity.logical_operation_id,
            attempt_id: &self.identity.attempt_id,
            authorization_ref: &self.identity.authorization_ref,
            native_operation_ref: &self.identity.native_operation_ref,
            event_seq,
            body,
        };
        write_frame(&mut state.stdout, &envelope)
    }
}

fn current_target() -> String {
    if cfg!(all(windows, target_arch = "x86_64")) {
        "x86_64-pc-windows-msvc".to_owned()
    } else {
        format!("{}-{}", std::env::consts::ARCH, std::env::consts::OS)
    }
}
