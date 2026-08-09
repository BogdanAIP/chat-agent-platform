#![cfg(windows)]

use std::io::{Read, Write};
use std::net::{Shutdown, TcpListener, TcpStream};
use std::path::{Path, PathBuf};
use std::process::{Child, Command, Stdio};
use std::thread;
use std::time::{Duration, Instant};

use uuid::Uuid;

const PROJECT_ID: &str = "demo";
const TOKEN_ENV: &str = "AGENT_PLATFORM_INGRESS_TOKEN";

struct Cleanup {
    child: Option<Child>,
    binary: PathBuf,
    repo_root: PathBuf,
    secret_ref: String,
}

impl Cleanup {
    fn stop_server(&mut self) {
        if let Some(mut child) = self.child.take() {
            let _ = child.kill();
            let _ = child.wait();
        }
    }
}

impl Drop for Cleanup {
    fn drop(&mut self) {
        self.stop_server();
        let _ = Command::new(&self.binary)
            .arg("--repo-root")
            .arg(&self.repo_root)
            .args([
                "ingress",
                "remove-token",
                "--project-id",
                PROJECT_ID,
                "--secret-ref",
                &self.secret_ref,
            ])
            .stdout(Stdio::null())
            .stderr(Stdio::null())
            .status();
    }
}

fn repo_root() -> PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("../..")
        .canonicalize()
        .expect("repository root must resolve")
}

fn free_port() -> u16 {
    let listener = TcpListener::bind(("127.0.0.1", 0)).expect("ephemeral port must bind");
    listener.local_addr().expect("local address").port()
}

fn send_post(port: u16, token: Option<&str>, body: &str) -> String {
    let mut stream = TcpStream::connect(("127.0.0.1", port)).expect("ingress must accept TCP");
    stream
        .set_read_timeout(Some(Duration::from_secs(5)))
        .expect("read timeout");
    stream
        .set_write_timeout(Some(Duration::from_secs(5)))
        .expect("write timeout");
    let auth = token.map_or_else(String::new, |value| format!("X-MCP-Token: {value}\r\n"));
    let request = format!(
        "POST /gpt HTTP/1.1\r\nHost: 127.0.0.1\r\nContent-Type: application/json\r\nContent-Length: {}\r\nConnection: close\r\n{}\r\n{}",
        body.len(),
        auth,
        body
    );
    stream
        .write_all(request.as_bytes())
        .expect("HTTP request must write");
    stream
        .shutdown(Shutdown::Write)
        .expect("request write side must close");
    let mut response = String::new();
    stream
        .read_to_string(&mut response)
        .expect("HTTP response must be readable");
    response
}

fn wait_until_listening(child: &mut Child, port: u16) {
    let deadline = Instant::now() + Duration::from_secs(15);
    loop {
        if TcpStream::connect(("127.0.0.1", port)).is_ok() {
            return;
        }
        if let Some(status) = child.try_wait().expect("child status must be readable") {
            panic!("local ingress exited before listening: {status}");
        }
        assert!(
            Instant::now() < deadline,
            "local ingress did not start in time"
        );
        thread::sleep(Duration::from_millis(100));
    }
}

#[test]
fn direct_ingress_process_authenticates_and_executes_locally() {
    let binary = PathBuf::from(env!("CARGO_BIN_EXE_agent-platform"));
    let repo_root = repo_root();
    let nonce = Uuid::new_v4().simple().to_string();
    let token = format!("ingress-test-token-{nonce}");
    let secret_ref = format!("secret://ingress/test-{nonce}");
    let port = free_port();
    let port_text = port.to_string();

    let configure = Command::new(&binary)
        .arg("--repo-root")
        .arg(&repo_root)
        .args([
            "ingress",
            "configure-token",
            "--project-id",
            PROJECT_ID,
            "--secret-ref",
            &secret_ref,
        ])
        .env(TOKEN_ENV, &token)
        .stdout(Stdio::null())
        .stderr(Stdio::null())
        .status()
        .expect("configure-token must start");
    assert!(configure.success(), "configure-token must succeed");

    let child = Command::new(&binary)
        .arg("--repo-root")
        .arg(&repo_root)
        .args([
            "ingress",
            "serve",
            "--project-id",
            PROJECT_ID,
            "--port",
            &port_text,
            "--secret-ref",
            &secret_ref,
        ])
        .stdout(Stdio::null())
        .stderr(Stdio::null())
        .spawn()
        .expect("local ingress must start");
    let mut cleanup = Cleanup {
        child: Some(child),
        binary,
        repo_root,
        secret_ref,
    };
    wait_until_listening(
        cleanup.child.as_mut().expect("server child must exist"),
        port,
    );

    let unauthorized_body =
        serde_json::json!({"action": "local_ping", "message": "blocked"}).to_string();
    let unauthorized = send_post(port, None, &unauthorized_body);
    assert!(
        unauthorized.starts_with("HTTP/1.1 401"),
        "missing token must be rejected: {unauthorized}"
    );

    let authorized_body =
        serde_json::json!({"action": "local_ping", "message": "direct-e2e"}).to_string();
    let authorized = send_post(port, Some(&token), &authorized_body);
    assert!(
        authorized.starts_with("HTTP/1.1 200"),
        "authenticated request must succeed: {authorized}"
    );
    assert!(
        authorized.contains("\"executed_locally\":true"),
        "response must prove local execution: {authorized}"
    );
    assert!(
        authorized.contains("\"message\":\"direct-e2e\""),
        "response must preserve ping payload: {authorized}"
    );

    cleanup.stop_server();
}
