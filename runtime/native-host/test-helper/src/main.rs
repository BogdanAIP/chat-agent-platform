#![forbid(unsafe_op_in_unsafe_fn)]

use std::env;
use std::fs;
use std::fs::OpenOptions;
use std::io;
use std::io::Read;
use std::io::Write;
use std::path::Path;
use std::process::Command;
use std::process::Stdio;
use std::thread;
use std::time::Duration;
use std::time::Instant;

fn main() {
    if let Err(error) = run() {
        eprintln!("native-host-test-helper: {error}");
        std::process::exit(2);
    }
}

fn run() -> Result<(), String> {
    let mut args = env::args().skip(1);
    let mode = args.next().ok_or_else(|| "missing mode".to_owned())?;
    let rest: Vec<String> = args.collect();
    match mode.as_str() {
        "exit" => {
            let code = parse_i32(&rest, "--code")?;
            std::process::exit(code);
        }
        "marker-sleep" => {
            let marker = required(&rest, "--marker")?;
            let sleep_ms = parse_u64(&rest, "--sleep-ms")?;
            fs::write(marker, b"started").map_err(io_error)?;
            thread::sleep(Duration::from_millis(sleep_ms));
        }
        "tree" => tree_mode(&rest)?,
        "burst-output" => {
            let stdout_bytes = parse_u64(&rest, "--stdout-bytes")?;
            let stderr_bytes = parse_u64(&rest, "--stderr-bytes")?;
            let seed = parse_u64(&rest, "--pattern-seed")?;
            write_pattern(io::stdout(), stdout_bytes, seed)?;
            write_pattern(io::stderr(), stderr_bytes, seed.wrapping_add(1))?;
        }
        "infinite-output" => {
            let stream = required(&rest, "--stream")?;
            let chunk_bytes = parse_u64(&rest, "--chunk-bytes")? as usize;
            if chunk_bytes == 0 || chunk_bytes > 1_048_576 {
                return Err("chunk-bytes outside helper bounds".into());
            }
            let chunk = vec![b'x'; chunk_bytes];
            loop {
                match stream.as_str() {
                    "stdout" => io::stdout().write_all(&chunk).map_err(io_error)?,
                    "stderr" => io::stderr().write_all(&chunk).map_err(io_error)?,
                    "both" => {
                        io::stdout().write_all(&chunk).map_err(io_error)?;
                        io::stderr().write_all(&chunk).map_err(io_error)?;
                    }
                    _ => return Err("stream must be stdout|stderr|both".into()),
                }
            }
        }
        "probe-handle" => probe_handle(&rest)?,
        "owner-host" => owner_host(&rest)?,
        "wait-file-exit" => {
            let ready = required(&rest, "--ready-file")?;
            let go = required(&rest, "--go-file")?;
            let code = parse_i32(&rest, "--code")?;
            fs::write(ready, b"ready").map_err(io_error)?;
            let deadline = Instant::now() + Duration::from_secs(30);
            while !Path::new(&go).exists() {
                if Instant::now() >= deadline {
                    return Err("timed out waiting for go-file".into());
                }
                thread::sleep(Duration::from_millis(10));
            }
            std::process::exit(code);
        }
        _ => return Err(format!("unknown mode {mode:?}")),
    }
    Ok(())
}

fn owner_host(args: &[String]) -> Result<(), String> {
    let host_exe = required(args, "--host-exe")?;
    let begin_json = required(args, "--begin-json")?;
    let ready_file = required(args, "--ready-file")?;
    let host_pid_file = required(args, "--host-pid-file")?;
    let mut host = Command::new(host_exe)
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::null())
        .spawn()
        .map_err(io_error)?;
    fs::write(host_pid_file, host.id().to_string()).map_err(io_error)?;

    let stdout = host.stdout.as_mut().ok_or("host stdout missing")?;
    let hello = read_frame(stdout)?;
    if !hello.contains("\"type\":\"host_hello\"") {
        return Err("host did not greet owner".into());
    }
    let stdin = host.stdin.as_mut().ok_or("host stdin missing")?;
    let payload = begin_json.as_bytes();
    stdin
        .write_all(&(payload.len() as u32).to_be_bytes())
        .and_then(|_| stdin.write_all(payload))
        .and_then(|_| stdin.flush())
        .map_err(io_error)?;

    loop {
        let event = read_frame(stdout)?;
        if event.contains("\"type\":\"process_spawned\"") {
            break;
        }
        if event.contains("\"type\":\"operation_terminal\"") {
            return Err("host terminated before spawning target".into());
        }
    }
    fs::write(ready_file, b"target-spawned").map_err(io_error)?;
    loop {
        thread::sleep(Duration::from_secs(1));
    }
}

fn read_frame(reader: &mut impl Read) -> Result<String, String> {
    let mut length = [0_u8; 4];
    reader.read_exact(&mut length).map_err(io_error)?;
    let length = u32::from_be_bytes(length) as usize;
    if !(1..=262_144).contains(&length) {
        return Err("host frame length outside bounds".into());
    }
    let mut payload = vec![0_u8; length];
    reader.read_exact(&mut payload).map_err(io_error)?;
    String::from_utf8(payload).map_err(|error| error.to_string())
}

fn tree_mode(args: &[String]) -> Result<(), String> {
    let pid_file = required(args, "--pid-file")?;
    let root_exit = required(args, "--root-exit-after-ms")?;
    let child_ms = parse_u64(args, "--child-ms")?;
    let grandchild_ms = parse_u64(args, "--grandchild-ms")?;
    let role = env::var("CAP_NATIVE_HOST_TEST_TREE_ROLE").unwrap_or_else(|_| "root".into());

    append_pid(&pid_file, &role)?;

    match role.as_str() {
        "root" => {
            let mut command = Command::new(env::current_exe().map_err(io_error)?);
            command
                .arg("tree")
                .arg("--pid-file")
                .arg(&pid_file)
                .arg("--root-exit-after-ms")
                .arg(&root_exit)
                .arg("--child-ms")
                .arg(child_ms.to_string())
                .arg("--grandchild-ms")
                .arg(grandchild_ms.to_string())
                .env("CAP_NATIVE_HOST_TEST_TREE_ROLE", "child");
            let child = command.spawn().map_err(io_error)?;
            append_named_pid(&pid_file, "spawned_child", child.id())?;
            if root_exit == "never" {
                let mut child = child;
                child.wait().map_err(io_error)?;
            } else {
                thread::sleep(Duration::from_millis(
                    root_exit
                        .parse::<u64>()
                        .map_err(|_| "invalid root-exit-after-ms")?,
                ));
            }
        }
        "child" => {
            let mut command = Command::new(env::current_exe().map_err(io_error)?);
            command
                .arg("tree")
                .arg("--pid-file")
                .arg(&pid_file)
                .arg("--root-exit-after-ms")
                .arg(&root_exit)
                .arg("--child-ms")
                .arg(child_ms.to_string())
                .arg("--grandchild-ms")
                .arg(grandchild_ms.to_string())
                .env("CAP_NATIVE_HOST_TEST_TREE_ROLE", "grandchild");
            let grandchild = command.spawn().map_err(io_error)?;
            append_named_pid(&pid_file, "spawned_grandchild", grandchild.id())?;
            thread::sleep(Duration::from_millis(child_ms));
        }
        "grandchild" => {
            thread::sleep(Duration::from_millis(grandchild_ms));
        }
        _ => return Err("invalid internal tree role".into()),
    }
    Ok(())
}

fn append_pid(path: &str, role: &str) -> Result<(), String> {
    append_named_pid(path, role, std::process::id())
}

fn append_named_pid(path: &str, role: &str, pid: u32) -> Result<(), String> {
    let mut file = OpenOptions::new()
        .create(true)
        .append(true)
        .open(path)
        .map_err(io_error)?;
    writeln!(file, "{role}={pid}").map_err(io_error)?;
    file.flush().map_err(io_error)
}

fn write_pattern(mut writer: impl Write, bytes: u64, seed: u64) -> Result<(), String> {
    let mut remaining = bytes;
    let mut offset = 0_u64;
    let mut chunk = [0_u8; 8192];
    while remaining > 0 {
        let count = usize::try_from(remaining.min(chunk.len() as u64))
            .map_err(|_| "pattern length conversion failed")?;
        for (index, byte) in chunk[..count].iter_mut().enumerate() {
            *byte = pattern_byte(seed, offset + index as u64);
        }
        writer.write_all(&chunk[..count]).map_err(io_error)?;
        offset += count as u64;
        remaining -= count as u64;
    }
    writer.flush().map_err(io_error)
}

fn pattern_byte(seed: u64, offset: u64) -> u8 {
    seed.wrapping_mul(31)
        .wrapping_add(offset.wrapping_mul(17))
        .wrapping_add(offset >> 3) as u8
}

#[cfg(windows)]
fn probe_handle(args: &[String]) -> Result<(), String> {
    use windows_sys::Win32::Foundation::GetHandleInformation;
    use windows_sys::Win32::Foundation::HANDLE;

    let raw = required(args, "--raw-handle")?
        .parse::<usize>()
        .map_err(|_| "invalid raw-handle")?;
    let result_file = required(args, "--result-file")?;
    let mut flags = 0_u32;
    let valid = unsafe { GetHandleInformation(raw as HANDLE, &mut flags) } != 0;
    fs::write(result_file, if valid { "valid" } else { "invalid" }).map_err(io_error)
}

#[cfg(not(windows))]
fn probe_handle(_args: &[String]) -> Result<(), String> {
    Err("probe-handle is Windows-only".into())
}

fn required(args: &[String], name: &str) -> Result<String, String> {
    let index = args
        .iter()
        .position(|value| value == name)
        .ok_or_else(|| format!("missing {name}"))?;
    args.get(index + 1)
        .cloned()
        .ok_or_else(|| format!("missing value for {name}"))
}

fn parse_u64(args: &[String], name: &str) -> Result<u64, String> {
    required(args, name)?
        .parse::<u64>()
        .map_err(|_| format!("invalid {name}"))
}

fn parse_i32(args: &[String], name: &str) -> Result<i32, String> {
    required(args, name)?
        .parse::<i32>()
        .map_err(|_| format!("invalid {name}"))
}

fn io_error(error: io::Error) -> String {
    error.to_string()
}
