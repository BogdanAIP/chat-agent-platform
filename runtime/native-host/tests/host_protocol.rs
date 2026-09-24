#![cfg(windows)]

use serde_json::json;
use std::collections::BTreeMap;
use std::io::Read;
use std::io::Write;
use std::path::PathBuf;
use std::process::Command;
use std::process::Stdio;
use std::time::Duration;
use std::time::Instant;

const MAX_FRAME: usize = 262_144;

#[test]
fn executes_one_contained_process_and_reports_terminal_receipt() {
    let binary = env!("CARGO_BIN_EXE_cap-native-host");
    let mut child = Command::new(binary)
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .expect("spawn native host");

    let mut stdin = child.stdin.take().expect("host stdin");
    let mut stdout = child.stdout.take().expect("host stdout");

    let hello = read_json_frame(&mut stdout).expect("host hello");
    assert_eq!(hello["type"], "host_hello");
    assert_eq!(hello["protocol_version"], 1);

    let system_root = std::env::var("SystemRoot").expect("SystemRoot");
    let executable = PathBuf::from(&system_root).join("System32").join("cmd.exe");
    let cwd = PathBuf::from(&system_root);
    let mut env = BTreeMap::new();
    env.insert("SystemRoot".to_owned(), system_root);

    write_json_frame(
        &mut stdin,
        &json!({
            "type": "begin_operation",
            "protocol_version": 1,
            "request_id": "test-request",
            "logical_operation_id": "test-logical",
            "attempt_id": "test-attempt",
            "authorization_ref": "grant:test",
            "native_operation_ref": "native:test",
            "executable": executable.to_string_lossy(),
            "argv": ["/d", "/s", "/c", "echo native-host-ok"],
            "cwd": cwd.to_string_lossy(),
            "env": env,
            "max_runtime_ms": 10000,
            "max_output_bytes": 65536,
            "containment_required": true
        }),
    )
    .expect("write BeginOperation");

    let deadline = Instant::now() + Duration::from_secs(20);
    let mut saw_prepared = false;
    let mut saw_spawned = false;
    let mut output = Vec::new();
    let terminal = loop {
        assert!(
            Instant::now() < deadline,
            "timed out waiting for terminal event"
        );
        let event = read_json_frame(&mut stdout).expect("event");
        match event["type"].as_str().unwrap_or_default() {
            "operation_prepared" => saw_prepared = true,
            "process_spawned" => saw_spawned = true,
            "output_chunk" if event["stream"] == "stdout" => {
                let encoded = event["data"].as_str().expect("base64 output");
                output.push(encoded.to_owned());
            }
            "operation_terminal" => break event,
            _ => {}
        }
    };

    drop(stdin);
    let status = child.wait().expect("wait native host");
    assert!(
        status.success(),
        "host stderr: {}",
        read_stderr(child.stderr.take())
    );

    assert!(saw_prepared);
    assert!(saw_spawned);
    assert_eq!(terminal["delivery_state"], "tree_exited");
    assert_eq!(terminal["reason"], "tree_exited");
    assert_eq!(terminal["target_ever_runnable"], true);
    assert_eq!(terminal["tree_quiescent"], true);
    assert_eq!(terminal["output_complete"], true);
    assert!(!output.is_empty());
}

fn write_json_frame(writer: &mut impl Write, value: &serde_json::Value) -> std::io::Result<()> {
    let payload = serde_json::to_vec(value)?;
    writer.write_all(&(payload.len() as u32).to_be_bytes())?;
    writer.write_all(&payload)?;
    writer.flush()
}

fn read_json_frame(reader: &mut impl Read) -> std::io::Result<serde_json::Value> {
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
