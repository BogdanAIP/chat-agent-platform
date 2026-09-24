#![cfg(windows)]

use serde_json::Value;
use serde_json::json;
use std::collections::BTreeMap;
use std::io::Read;
use std::io::Write;
use std::path::PathBuf;
use std::process::Child;
use std::process::ChildStdin;
use std::process::Command;
use std::process::Stdio;
use std::sync::mpsc;
use std::sync::mpsc::Receiver;
use std::thread;
use std::time::Duration;
use std::time::Instant;

const MAX_FRAME: usize = 262_144;
const EVENT_TIMEOUT: Duration = Duration::from_secs(15);
const TERMINATION_BOUND: Duration = Duration::from_secs(8);
const LONG_RUNTIME_MS: u64 = 3_600_000;

#[test]
fn executes_one_contained_process_and_reports_terminal_receipt() {
    let mut host = HostHarness::spawn();
    host.send(&begin_message(
        "normal-request",
        "normal-attempt",
        "echo native-host-ok",
        10_000,
        65_536,
    ));

    let (terminal, events) = host.collect_until_terminal(EVENT_TIMEOUT);
    host.wait_success();

    assert!(
        events
            .iter()
            .any(|event| event["type"] == "operation_prepared")
    );
    assert!(
        events
            .iter()
            .any(|event| event["type"] == "process_spawned")
    );
    assert!(
        events
            .iter()
            .any(|event| { event["type"] == "output_chunk" && event["stream"] == "stdout" })
    );
    let spawned_index = events
        .iter()
        .position(|event| event["type"] == "process_spawned")
        .expect("process_spawned event");
    let first_output_index = events
        .iter()
        .position(|event| event["type"] == "output_chunk")
        .expect("output_chunk event");
    assert!(
        spawned_index < first_output_index,
        "process_spawned must precede output_chunk"
    );
    assert_eq!(terminal["delivery_state"], "tree_exited");
    assert_eq!(terminal["reason"], "tree_exited");
    assert_eq!(terminal["target_ever_runnable"], true);
    assert_eq!(terminal["tree_quiescent"], true);
    assert_eq!(terminal["output_complete"], true);
}

#[test]
fn early_cancel_terminates_tree_without_waiting_for_runtime_budget() {
    let mut host = HostHarness::spawn();
    host.send(&begin_message(
        "cancel-request",
        "cancel-attempt",
        "ping -n 30 127.0.0.1 >nul",
        LONG_RUNTIME_MS,
        65_536,
    ));
    host.wait_for_type("process_spawned", EVENT_TIMEOUT);

    let cancellation_started = Instant::now();
    host.send(&json!({
        "type": "cancel_operation",
        "protocol_version": 1,
        "request_id": "cancel-request",
        "attempt_id": "cancel-attempt"
    }));
    let (terminal, _) = host.collect_until_terminal(EVENT_TIMEOUT);
    let cancellation_elapsed = cancellation_started.elapsed();
    host.wait_success();

    assert!(
        cancellation_elapsed < TERMINATION_BOUND,
        "cancel took {cancellation_elapsed:?}"
    );
    assert_eq!(terminal["delivery_state"], "terminated");
    assert_eq!(terminal["reason"], "cancelled");
    assert_eq!(terminal["target_ever_runnable"], true);
    assert_eq!(terminal["tree_quiescent"], true);
}

#[test]
fn owner_eof_terminates_active_tree() {
    let mut host = HostHarness::spawn();
    host.send(&begin_message(
        "owner-request",
        "owner-attempt",
        "ping -n 30 127.0.0.1 >nul",
        LONG_RUNTIME_MS,
        65_536,
    ));
    host.wait_for_type("process_spawned", EVENT_TIMEOUT);

    let owner_loss_started = Instant::now();
    host.close_stdin();
    let (terminal, _) = host.collect_until_terminal(EVENT_TIMEOUT);
    let owner_loss_elapsed = owner_loss_started.elapsed();
    host.wait_success();

    assert!(
        owner_loss_elapsed < TERMINATION_BOUND,
        "owner EOF cleanup took {owner_loss_elapsed:?}"
    );
    assert_eq!(terminal["delivery_state"], "terminated");
    assert_eq!(terminal["reason"], "owner_lost");
    assert_eq!(terminal["target_ever_runnable"], true);
    assert_eq!(terminal["tree_quiescent"], true);
}

#[test]
fn second_begin_is_protocol_violation_and_cannot_spawn_again() {
    let mut host = HostHarness::spawn();
    host.send(&begin_message(
        "first-request",
        "first-attempt",
        "ping -n 30 127.0.0.1 >nul",
        LONG_RUNTIME_MS,
        65_536,
    ));
    host.wait_for_type("process_spawned", EVENT_TIMEOUT);

    host.send(&begin_message(
        "second-request",
        "second-attempt",
        "echo forbidden-second-spawn",
        10_000,
        65_536,
    ));
    let (terminal, events_after_second_begin) = host.collect_until_terminal(EVENT_TIMEOUT);
    host.wait_success();

    assert!(
        !events_after_second_begin
            .iter()
            .any(|event| event["type"] == "process_spawned"),
        "second BeginOperation produced a second process_spawned event"
    );
    assert_eq!(terminal["delivery_state"], "terminated");
    assert_eq!(terminal["reason"], "protocol_rejected");
    assert_eq!(terminal["tree_quiescent"], true);
}

#[test]
fn runtime_budget_terminates_active_tree() {
    let mut host = HostHarness::spawn();
    host.send(&begin_message(
        "timeout-request",
        "timeout-attempt",
        "ping -n 30 127.0.0.1 >nul",
        250,
        65_536,
    ));

    let timeout_started = Instant::now();
    let (terminal, _) = host.collect_until_terminal(EVENT_TIMEOUT);
    let timeout_elapsed = timeout_started.elapsed();
    host.wait_success();

    assert!(
        timeout_elapsed < TERMINATION_BOUND,
        "runtime timeout cleanup took {timeout_elapsed:?}"
    );
    assert_eq!(terminal["delivery_state"], "terminated");
    assert_eq!(terminal["reason"], "runtime_timeout");
    assert_eq!(terminal["tree_quiescent"], true);
    assert_eq!(terminal["output_complete"], false);
}

#[test]
fn test_helper_tree_keeps_job_active_after_root_exit() {
    let helper = std::env::var("CAP_NATIVE_HOST_TEST_HELPER").expect("CAP_NATIVE_HOST_TEST_HELPER");
    let unique = format!(
        "cap-native-host-tree-{}-{}.txt",
        std::process::id(),
        Instant::now().elapsed().as_nanos()
    );
    let pid_file = std::env::temp_dir().join(unique);
    let _ = std::fs::remove_file(&pid_file);

    let mut host = HostHarness::spawn();
    host.send(&begin_custom_message(
        "tree-request",
        "tree-attempt",
        &helper,
        &[
            "tree",
            "--pid-file",
            &pid_file.to_string_lossy(),
            "--root-exit-after-ms",
            "50",
            "--child-ms",
            "450",
            "--grandchild-ms",
            "850",
        ],
        5_000,
        65_536,
    ));

    let started = Instant::now();
    let (terminal, events) = host.collect_until_terminal(EVENT_TIMEOUT);
    let elapsed = started.elapsed();
    host.wait_success();

    assert!(
        events.iter().any(|event| event["type"] == "root_exited"),
        "root exit must be observed before terminal"
    );
    assert!(
        elapsed >= Duration::from_millis(500),
        "terminal arrived before descendants could keep the Job active: {elapsed:?}"
    );
    assert_eq!(terminal["reason"], "tree_exited");
    assert_eq!(terminal["tree_quiescent"], true);

    let evidence = std::fs::read_to_string(&pid_file).expect("tree pid evidence");
    assert!(evidence.contains("root="));
    assert!(evidence.contains("child="));
    assert!(evidence.contains("grandchild="));
    let _ = std::fs::remove_file(pid_file);
}

#[test]
fn test_helper_binary_output_is_reported_complete() {
    let helper = std::env::var("CAP_NATIVE_HOST_TEST_HELPER").expect("CAP_NATIVE_HOST_TEST_HELPER");
    let mut host = HostHarness::spawn();
    host.send(&begin_custom_message(
        "output-request",
        "output-attempt",
        &helper,
        &[
            "burst-output",
            "--stdout-bytes",
            "70000",
            "--stderr-bytes",
            "33000",
            "--pattern-seed",
            "17",
        ],
        10_000,
        200_000,
    ));

    let (terminal, events) = host.collect_until_terminal(EVENT_TIMEOUT);
    host.wait_success();

    let stdout_bytes: u64 = events
        .iter()
        .filter(|event| event["type"] == "output_chunk" && event["stream"] == "stdout")
        .map(|event| event["raw_len"].as_u64().expect("stdout raw_len"))
        .sum();
    let stderr_bytes: u64 = events
        .iter()
        .filter(|event| event["type"] == "output_chunk" && event["stream"] == "stderr")
        .map(|event| event["raw_len"].as_u64().expect("stderr raw_len"))
        .sum();

    assert_eq!(stdout_bytes, 70_000);
    assert_eq!(stderr_bytes, 33_000);
    assert_eq!(terminal["stdout_bytes"], 70_000);
    assert_eq!(terminal["stderr_bytes"], 33_000);
    assert_eq!(terminal["output_complete"], true);
    assert_eq!(terminal["reason"], "tree_exited");
}

struct HostHarness {
    child: Child,
    stdin: Option<ChildStdin>,
    events: Receiver<Result<Value, String>>,
}

impl HostHarness {
    fn spawn() -> Self {
        let binary = env!("CARGO_BIN_EXE_cap-native-host");
        let mut child = Command::new(binary)
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .spawn()
            .expect("spawn native host");

        let stdin = child.stdin.take().expect("host stdin");
        let mut stdout = child.stdout.take().expect("host stdout");
        let (event_tx, events) = mpsc::channel();

        thread::spawn(move || {
            loop {
                match read_json_frame(&mut stdout) {
                    Ok(event) => {
                        if event_tx.send(Ok(event)).is_err() {
                            return;
                        }
                    }
                    Err(error) => {
                        let _ = event_tx.send(Err(error.to_string()));
                        return;
                    }
                }
            }
        });

        let hello = recv_event(&events, EVENT_TIMEOUT);
        assert_eq!(hello["type"], "host_hello");
        assert_eq!(hello["protocol_version"], 1);

        Self {
            child,
            stdin: Some(stdin),
            events,
        }
    }

    fn send(&mut self, value: &Value) {
        let stdin = self.stdin.as_mut().expect("host stdin is closed");
        write_json_frame(stdin, value).expect("write host frame");
    }

    fn close_stdin(&mut self) {
        self.stdin.take();
    }

    fn wait_for_type(&self, message_type: &str, timeout: Duration) -> Value {
        let deadline = Instant::now() + timeout;
        loop {
            let event = recv_event(&self.events, remaining(deadline));
            if event["type"] == message_type {
                return event;
            }
        }
    }

    fn collect_until_terminal(&self, timeout: Duration) -> (Value, Vec<Value>) {
        let deadline = Instant::now() + timeout;
        let mut events = Vec::new();
        loop {
            let event = recv_event(&self.events, remaining(deadline));
            if event["type"] == "operation_terminal" {
                return (event, events);
            }
            events.push(event);
        }
    }

    fn wait_success(&mut self) {
        self.stdin.take();
        let status = self.child.wait().expect("wait native host");
        assert!(
            status.success(),
            "host stderr: {}",
            read_stderr(self.child.stderr.take())
        );
    }
}

impl Drop for HostHarness {
    fn drop(&mut self) {
        self.stdin.take();
        match self.child.try_wait() {
            Ok(Some(_)) => {}
            Ok(None) | Err(_) => {
                let _ = self.child.kill();
                let _ = self.child.wait();
            }
        }
    }
}

fn begin_custom_message(
    request_id: &str,
    attempt_id: &str,
    executable: &str,
    argv: &[&str],
    max_runtime_ms: u64,
    max_output_bytes: u64,
) -> Value {
    let executable_path = PathBuf::from(executable);
    let cwd = executable_path
        .parent()
        .expect("helper executable parent")
        .to_path_buf();
    json!({
        "type": "begin_operation",
        "protocol_version": 1,
        "request_id": request_id,
        "logical_operation_id": format!("logical-{request_id}"),
        "attempt_id": attempt_id,
        "authorization_ref": format!("grant:{request_id}"),
        "native_operation_ref": format!("native:{request_id}"),
        "executable": executable_path.to_string_lossy(),
        "argv": argv,
        "cwd": cwd.to_string_lossy(),
        "env": {},
        "max_runtime_ms": max_runtime_ms,
        "max_output_bytes": max_output_bytes,
        "containment_required": true
    })
}

fn begin_message(
    request_id: &str,
    attempt_id: &str,
    command: &str,
    max_runtime_ms: u64,
    max_output_bytes: u64,
) -> Value {
    let system_root = std::env::var("SystemRoot").expect("SystemRoot");
    let system32 = PathBuf::from(&system_root).join("System32");
    let executable = system32.join("cmd.exe");
    let mut env = BTreeMap::new();
    env.insert("SystemRoot".to_owned(), system_root);
    env.insert("PATH".to_owned(), system32.to_string_lossy().into_owned());

    json!({
        "type": "begin_operation",
        "protocol_version": 1,
        "request_id": request_id,
        "logical_operation_id": format!("logical-{request_id}"),
        "attempt_id": attempt_id,
        "authorization_ref": format!("grant:{request_id}"),
        "native_operation_ref": format!("native:{request_id}"),
        "executable": executable.to_string_lossy(),
        "argv": ["/d", "/s", "/c", command],
        "cwd": system32.to_string_lossy(),
        "env": env,
        "max_runtime_ms": max_runtime_ms,
        "max_output_bytes": max_output_bytes,
        "containment_required": true
    })
}

fn recv_event(events: &Receiver<Result<Value, String>>, timeout: Duration) -> Value {
    match events.recv_timeout(timeout) {
        Ok(Ok(event)) => event,
        Ok(Err(error)) => panic!("host protocol reader failed: {error}"),
        Err(mpsc::RecvTimeoutError::Timeout) => {
            panic!("timed out waiting for host protocol event")
        }
        Err(mpsc::RecvTimeoutError::Disconnected) => {
            panic!("host protocol event channel disconnected")
        }
    }
}

fn remaining(deadline: Instant) -> Duration {
    let now = Instant::now();
    assert!(now < deadline, "timed out waiting for host protocol event");
    deadline.saturating_duration_since(now)
}

fn write_json_frame(writer: &mut impl Write, value: &Value) -> std::io::Result<()> {
    let payload = serde_json::to_vec(value)?;
    writer.write_all(&(payload.len() as u32).to_be_bytes())?;
    writer.write_all(&payload)?;
    writer.flush()
}

fn read_json_frame(reader: &mut impl Read) -> std::io::Result<Value> {
    let mut prefix = [0_u8; 4];
    reader.read_exact(&mut prefix)?;
    let length = u32::from_be_bytes(prefix) as usize;
    assert!((1..=MAX_FRAME).contains(&length));
    let mut payload = vec![0_u8; length];
    reader.read_exact(&mut payload)?;
    serde_json::from_slice(&payload).map_err(std::io::Error::other)
}

fn read_stderr(stderr: Option<std::process::ChildStderr>) -> String {
    let Some(mut stderr) = stderr else {
        return String::new();
    };
    let mut text = String::new();
    let _ = stderr.read_to_string(&mut text);
    text
}
