use crate::events::EventSink;
use crate::protocol::BeginOperation;
use std::sync::mpsc::Receiver;

#[derive(Debug)]
pub enum ControlSignal {
    Cancel,
    OwnerLost,
    ProtocolViolation(String),
}

#[cfg(windows)]
mod windows;

#[cfg(windows)]
pub fn run_operation(
    begin: &BeginOperation,
    sink: &EventSink,
    control: Receiver<ControlSignal>,
) -> Result<(), String> {
    windows::run_operation(begin, sink, control)
}

#[cfg(not(windows))]
pub fn run_operation(
    _begin: &BeginOperation,
    sink: &EventSink,
    _control: Receiver<ControlSignal>,
) -> Result<(), String> {
    use crate::events::DeliveryState;
    use crate::events::TerminalReason;
    use crate::events::TerminalSnapshot;
    let empty = empty_sha256();
    sink.terminal(&TerminalSnapshot {
        delivery_state: DeliveryState::NeverRunnable,
        reason: TerminalReason::UnsupportedPlatform,
        root_exit_code: None,
        target_ever_runnable: false,
        tree_quiescent: true,
        stdout_bytes: 0,
        stderr_bytes: 0,
        stdout_sha256: empty.clone(),
        stderr_sha256: empty,
        output_complete: true,
    })
    .map_err(|error| error.to_string())
}

#[cfg(not(windows))]
fn empty_sha256() -> String {
    use sha2::Digest;
    use sha2::Sha256;
    let digest = Sha256::digest([]);
    digest.iter().map(|byte| format!("{byte:02x}")).collect()
}
