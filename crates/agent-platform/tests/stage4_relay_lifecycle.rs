#![cfg(windows)]

use std::fs::{self, File};
use std::io::{Read, Write};
use std::net::{TcpListener, TcpStream};
use std::path::{Path, PathBuf};
use std::process::Stdio;
use std::sync::{Arc, Mutex, mpsc};
use std::thread;
use std::time::{Duration, SystemTime, UNIX_EPOCH};

use agent_platform::transport::remove_relay_token;
use serde_json::{Value, json};
use tempfile::tempdir;
use uuid::Uuid;
use wait_timeout::ChildExt;

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
    let output_id = Uuid::new_v4().simple();
    let stdout_path = root.join(format!(".stage4-command-{output_id}.stdout"));
    let stderr_path = root.join(format!(".stage4-command-{output_id}.stderr"));
    let stdout_file = File::create(&stdout_path).expect("create command stdout file");
    let stderr_file = File::create(&stderr_path).expect("create command stderr file");

    let mut command = std::process::Command::new(env!("CARGO_BIN_EXE_agent-platform"));
    command
        .arg("--repo-root")
        .arg(root)
        .args(args)
        .stdout(Stdio::from(stdout_file))
        .stderr(Stdio::from(stderr_file));
    if token_env {
        command.env("STAGE4_TEST_RELAY_TOKEN", TOKEN);
    }
    let mut child = command.spawn().expect("agent-platform process must start");
    let timeout = if args.get(1) == Some(&"stop") {
        Duration::from_secs(45)
    } else {
        Duration::from_secs(15)
    };
    let Some(status) = child
        .wait_timeout(timeout)
        .expect("agent-platform wait must succeed")
    else {
        let _ = child.kill();
        let _ = child.wait();
        let stdout = fs::read_to_string(&stdout_path).unwrap_or_default();
        let stderr = fs::read_to_string(&stderr_path).unwrap_or_default();
        panic!(
            "agent-platform command timed out after {timeout:?}: {args:?}; stdout={stdout} stderr={stderr}"
        );
    };
    let stdout = fs::read(&stdout_path).expect("read command stdout");
    let stderr = fs::read(&stderr_path).expect("read command stderr");
    let _ = fs::remove_file(&stdout_path);
    let _ = fs::remove_file(&stderr_path);
    assert!(
        status.success(),
        "agent-platform failed for {args:?}: stdout={} stderr={}",
        String::from_utf8_lossy(&stdout),
        String::from_utf8_lossy(&stderr)
    );
    serde_json::from_slice(&stdout).expect("command must return JSON")
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

fn spawn_gateway() -> (
    String,
    Arc<Mutex<GatewayState>>,
    mpsc::Sender<()>,
    thread::JoinHandle<()>,
) {
    let listener = TcpListener::bind("127.0.0.1:0").expect("bind fake gateway");
    listener
        .set_nonblocking(true)
        .expect("fake gateway nonblocking mode");
    let address = listener.local_addr().expect("fake gateway address");
    let state = Arc::new(Mutex::new(GatewayState::default()));
    let server_state = Arc::clone(&state);
    let ping_id = format!("rly_{}", Uuid::new_v4().simple());
    let self_test_id = format!("rly_{}", Uuid::new_v4().simple());
    let (shutdown_tx, shutdown_rx) = mpsc::channel();
    let handle = thread::spawn(move || {
        loop {
            if shutdown_rx.try_recv().is_ok() {
                break;
            }
            let mut stream = match listener.accept() {
                Ok((stream, _)) => stream,
                Err(error) if error.kind() == std::io::ErrorKind::WouldBlock => {
                    thread::sleep(Duration::from_millis(10));
                    continue;
                }
                Err(error) => panic!("accept fake gateway request: {error}"),
            };
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
                    let (response, idle) = if !state.ping_accepted {
                        (
                            json!({"ok": true, "task": task(&ping_id, "local_ping", json!({"message": "stage4-e2e"}))}),
                            false,
                        )
                    } else if state.self_test_response.is_none() {
                        (
                            json!({"ok": true, "task": task(&self_test_id, "runtime_self_test", json!({}))}),
                            false,
                        )
                    } else {
                        (json!({"ok": true, "task": null}), true)
                    };
                    drop(state);
                    if idle {
                        thread::sleep(Duration::from_millis(500));
                    }
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
    (format!("http://{address}"), state, shutdown_tx, handle)
}

#[test]
fn configure_start_execute_retry_stop_round_trip_uses_one_local_binary() {
    let temporary = tempdir().expect("temp directory");
    make_test_repo(temporary.path());
    let secret_ref = format!("secret://relay/test/{}", Uuid::new_v4().simple());
    let _cleanup = SecretCleanup {
        root: temporary.path().to_path_buf(),
        secret_ref: secret_ref.clone(),
    };
    let (endpoint, gateway_state, gateway_shutdown, gateway) = spawn_gateway();

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

    let mut offline_observed = false;
    for _ in 0..50 {
        if gateway_state.lock().expect("gateway state").offline_seen {
            offline_observed = true;
            break;
        }
        thread::sleep(Duration::from_millis(100));
    }
    let _ = gateway_shutdown.send(());
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
        offline_observed && state.offline_seen,
        "relay stop must notify the gateway within five seconds"
    );
}
