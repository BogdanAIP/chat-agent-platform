#![cfg(windows)]

use std::fs;
use std::io::{Read, Write};
use std::net::{TcpListener, TcpStream};
use std::path::{Path, PathBuf};
use std::sync::{Arc, Mutex};
use std::thread;
use std::time::{Duration, SystemTime, UNIX_EPOCH};

use agent_platform::transport::remove_relay_token;
use serde_json::{Value, json};
use tempfile::tempdir;
use uuid::Uuid;

const PROJECT_ID: &str = "relay-test";
const TOKEN: &str = "abcdefghijklmnopqrstuvwxyz0123456789ABCDEFGH";

#[derive(Default)]
struct GatewayState {
    ping_result_attempts: usize,
    ping_response: Option<Value>,
    ping_accepted: bool,
    self_test_response: Option<Value>,
    offline_seen: bool,
}

struct SecretCleanup {
    root: PathBuf,
    secret_ref: String,
}

impl Drop for SecretCleanup {
    fn drop(&mut self) {
        let _ = remove_relay_token(&self.root, Some(PROJECT_ID), &self.secret_ref);
    }
}

fn source_repo_root() -> PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("../..")
        .canonicalize()
        .expect("repository root must resolve")
}

fn make_test_repo(root: &Path) {
    let source_config = source_repo_root().join("config");
    let config = root.join("config");
    fs::create_dir_all(&config).expect("test config directory");
    for file in [
        "tools.yaml",
        "tool-lock.yaml",
        "capability-requirements.yaml",
        "policy.yaml",
    ] {
        fs::copy(source_config.join(file), config.join(file)).expect("copy test config");
    }
    fs::write(
        config.join("projects.yaml"),
        serde_json::to_string_pretty(&json!({
            "contract_version": "projects-v1",
            "active_project_id": PROJECT_ID,
            "projects": [{
                "project_id": PROJECT_ID,
                "repo_root": "..",
                "local_root": "..",
                "artifact_root": "../artifacts",
                "policy": "policy.yaml"
            }]
        }))
        .expect("serialize projects config"),
    )
    .expect("write projects config");
}

fn run(root: &Path, args: &[&str], token_env: bool) -> Value {
    let mut command = std::process::Command::new(env!("CARGO_BIN_EXE_agent-platform"));
    command.arg("--repo-root").arg(root).args(args);
    if token_env {
        command.env("STAGE4_TEST_RELAY_TOKEN", TOKEN);
    }
    let output = command.output().expect("agent-platform process must start");
    assert!(
        output.status.success(),
        "agent-platform failed: stdout={} stderr={}",
        String::from_utf8_lossy(&output.stdout),
        String::from_utf8_lossy(&output.stderr)
    );
    serde_json::from_slice(&output.stdout).expect("command must return JSON")
}

fn deadline_ms() -> u128 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .expect("system time")
        .as_millis()
        + 30_000
}

fn task(request_id: &str, operation: &str, parameters: Value) -> Value {
    json!({
        "contract_version": "relay-request-v1",
        "request_id": request_id,
        "operation": operation,
        "parameters": parameters,
        "deadline_unix_ms": deadline_ms()
    })
}

fn read_http_request(stream: &mut TcpStream) -> (String, Value) {
    stream
        .set_read_timeout(Some(Duration::from_secs(5)))
        .expect("read timeout");
    let mut bytes = Vec::new();
    let mut buffer = [0_u8; 4096];
    let header_end;
    loop {
        let count = stream.read(&mut buffer).expect("read HTTP request");
        assert!(count > 0, "connection closed before HTTP headers");
        bytes.extend_from_slice(&buffer[..count]);
        if let Some(position) = bytes.windows(4).position(|window| window == b"\r\n\r\n") {
            header_end = position + 4;
            break;
        }
    }
    let headers = String::from_utf8_lossy(&bytes[..header_end]).into_owned();
    let content_length = headers
        .lines()
        .find_map(|line| {
            let (name, value) = line.split_once(':')?;
            name.eq_ignore_ascii_case("content-length")
                .then(|| value.trim().parse::<usize>().ok())
                .flatten()
        })
        .unwrap_or(0);
    while bytes.len() < header_end + content_length {
        let count = stream.read(&mut buffer).expect("read HTTP body");
        assert!(count > 0, "connection closed before HTTP body");
        bytes.extend_from_slice(&buffer[..count]);
    }
    let body = &bytes[header_end..header_end + content_length];
    let value = serde_json::from_slice(body).expect("HTTP body must be JSON");
    (headers, value)
}

fn respond(stream: &mut TcpStream, status: u16, value: &Value) {
    let body = serde_json::to_vec(value).expect("serialize HTTP response");
    let reason = if status == 200 {
        "OK"
    } else {
        "Internal Server Error"
    };
    write!(
        stream,
        "HTTP/1.1 {status} {reason}\r\nContent-Type: application/json\r\nContent-Length: {}\r\nConnection: close\r\n\r\n",
        body.len()
    )
    .expect("write HTTP headers");
    stream.write_all(&body).expect("write HTTP body");
    stream.flush().expect("flush HTTP response");
}

fn spawn_gateway() -> (String, Arc<Mutex<GatewayState>>, thread::JoinHandle<()>) {
    let listener = TcpListener::bind("127.0.0.1:0").expect("bind fake gateway");
    let address = listener.local_addr().expect("fake gateway address");
    let state = Arc::new(Mutex::new(GatewayState::default()));
    let server_state = Arc::clone(&state);
    let ping_id = format!("rly_{}", Uuid::new_v4().simple());
    let self_test_id = format!("rly_{}", Uuid::new_v4().simple());
    let handle = thread::spawn(move || {
        for incoming in listener.incoming().take(16) {
            let mut stream = incoming.expect("accept fake gateway request");
            let (headers, body) = read_http_request(&mut stream);
            assert!(
                headers
                    .to_ascii_lowercase()
                    .contains(&format!("x-agent-token: {}", TOKEN.to_ascii_lowercase())),
                "agent token header is required"
            );
            match body["agent_action"].as_str() {
                Some("poll") => {
                    let state = server_state.lock().expect("gateway state");
                    let response = if !state.ping_accepted {
                        json!({"ok": true, "task": task(&ping_id, "local_ping", json!({"message": "stage4-e2e"}))})
                    } else if state.self_test_response.is_none() {
                        json!({"ok": true, "task": task(&self_test_id, "runtime_self_test", json!({}))})
                    } else {
                        json!({"ok": true, "task": null})
                    };
                    drop(state);
                    respond(&mut stream, 200, &response);
                }
                Some("result") => {
                    let response = body["response"].clone();
                    let request_id = response["request_id"]
                        .as_str()
                        .expect("relay response request id");
                    let mut state = server_state.lock().expect("gateway state");
                    if request_id == ping_id {
                        state.ping_result_attempts += 1;
                        if state.ping_result_attempts == 1 {
                            state.ping_response = Some(response);
                            drop(state);
                            respond(
                                &mut stream,
                                500,
                                &json!({"ok": false, "error": "simulated lost result acknowledgement"}),
                            );
                            continue;
                        }
                        assert_eq!(
                            state.ping_response.as_ref(),
                            Some(&response),
                            "duplicate task must reuse the cached local response"
                        );
                        state.ping_accepted = true;
                    } else if request_id == self_test_id {
                        state.self_test_response = Some(response);
                    } else {
                        panic!("unexpected relay response id: {request_id}");
                    }
                    drop(state);
                    respond(&mut stream, 200, &json!({"ok": true}));
                }
                Some("offline") => {
                    let mut state = server_state.lock().expect("gateway state");
                    state.offline_seen = true;
                    drop(state);
                    respond(
                        &mut stream,
                        200,
                        &json!({"ok": true, "agent_online": false}),
                    );
                    break;
                }
                other => panic!("unexpected agent action: {other:?}"),
            }
        }
    });
    (format!("http://{address}"), state, handle)
}

#[test]
fn configure_start_execute_retry_stop_round_trip_uses_one_local_binary() {
    let temporary = tempdir().expect("temp directory");
    make_test_repo(temporary.path());
    let secret_ref = format!("relay.test.{}", Uuid::new_v4().simple());
    let _cleanup = SecretCleanup {
        root: temporary.path().to_path_buf(),
        secret_ref: secret_ref.clone(),
    };
    let (endpoint, gateway_state, gateway) = spawn_gateway();

    let configured = run(
        temporary.path(),
        &[
            "relay",
            "configure",
            "--project-id",
            PROJECT_ID,
            "--endpoint",
            &endpoint,
            "--env-name",
            "STAGE4_TEST_RELAY_TOKEN",
            "--secret-ref",
            &secret_ref,
        ],
        true,
    );
    assert_eq!(configured["status"], "configured");
    assert_eq!(configured["enabled"], false);
    assert_eq!(configured["relay"]["endpoint"], endpoint);
    assert_eq!(configured["credential"]["raw_secret_returned"], false);

    let before = run(
        temporary.path(),
        &["relay", "status", "--project-id", PROJECT_ID],
        false,
    );
    assert_eq!(before["configured"], true);
    assert_eq!(before["enabled"], false);

    let started = run(
        temporary.path(),
        &["relay", "start", "--project-id", PROJECT_ID],
        false,
    );
    assert!(matches!(
        started["status"].as_str(),
        Some("started" | "starting")
    ));

    let mut completed = false;
    for _ in 0..150 {
        let status = run(
            temporary.path(),
            &["relay", "status", "--project-id", PROJECT_ID],
            false,
        );
        if status["last_task_id"].is_string() {
            let state = gateway_state.lock().expect("gateway state");
            if state.self_test_response.is_some() {
                completed = true;
                break;
            }
        }
        thread::sleep(Duration::from_millis(100));
    }
    assert!(completed, "relay did not complete both local operations");

    let stopped = run(
        temporary.path(),
        &["relay", "stop", "--project-id", PROJECT_ID],
        false,
    );
    assert_eq!(stopped["status"], "stopped");
    let after = run(
        temporary.path(),
        &["relay", "status", "--project-id", PROJECT_ID],
        false,
    );
    assert_eq!(after["configured"], true);
    assert_eq!(after["enabled"], false);
    assert_eq!(after["state"], "stopped");

    gateway.join().expect("fake gateway thread");
    let state = gateway_state.lock().expect("gateway state");
    assert_eq!(state.ping_result_attempts, 2);
    assert!(state.ping_accepted);
    let ping = state.ping_response.as_ref().expect("ping response");
    assert_eq!(ping["status"], "success");
    assert_eq!(ping["result"]["pong"], true);
    assert_eq!(ping["result"]["executed_locally"], true);
    let self_test = state
        .self_test_response
        .as_ref()
        .expect("self-test response");
    assert_eq!(self_test["status"], "success");
    assert_eq!(self_test["result"]["status"], "success");
    assert_eq!(self_test["result"]["result"]["ping"], "pong");
    assert!(
        state.offline_seen,
        "relay stop must notify the gateway immediately"
    );
}
