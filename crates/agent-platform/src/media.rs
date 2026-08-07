use std::io::Read;
use std::path::Path;
use std::process::{ChildStderr, ChildStdout, Command, Output, Stdio};
use std::thread;
use std::time::Duration;

use regex::Regex;
use serde::{Deserialize, Serialize};
use serde_json::Value;
use wait_timeout::ChildExt;

use crate::error::PlatformError;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MediaInspection {
    pub duration_seconds: f64,
    pub sample_rate_hz: u32,
    pub channels: u32,
    pub codec: String,
    pub integrated_lufs: Option<f64>,
    pub integrated_lufs_status: String,
    pub loudness_range_lu: f64,
    pub true_peak_dbtp: Option<f64>,
    pub true_peak_status: String,
}

pub fn inspect_media(path: &Path) -> Result<MediaInspection, PlatformError> {
    let probe = run(
        "ffprobe",
        &[
            "-v",
            "error",
            "-select_streams",
            "a:0",
            "-show_entries",
            "format=duration:stream=codec_name,sample_rate,channels",
            "-of",
            "json",
            &path.to_string_lossy(),
        ],
    )?;
    let raw: Value = serde_json::from_slice(&probe.stdout)
        .map_err(|error| PlatformError::Validation(format!("invalid ffprobe JSON: {error}")))?;
    let stream = raw
        .get("streams")
        .and_then(Value::as_array)
        .and_then(|streams| streams.first())
        .ok_or_else(|| {
            PlatformError::Validation("ffprobe returned no primary audio stream".into())
        })?;
    let duration_seconds = raw
        .pointer("/format/duration")
        .and_then(Value::as_str)
        .and_then(|value| value.parse().ok())
        .ok_or_else(|| PlatformError::Validation("ffprobe returned invalid duration".into()))?;
    let sample_rate_hz = stream
        .get("sample_rate")
        .and_then(Value::as_str)
        .and_then(|value| value.parse().ok())
        .ok_or_else(|| PlatformError::Validation("ffprobe returned invalid sample rate".into()))?;
    let channels = stream
        .get("channels")
        .and_then(Value::as_u64)
        .and_then(|value| u32::try_from(value).ok())
        .ok_or_else(|| PlatformError::Validation("ffprobe returned invalid channels".into()))?;
    let codec = stream
        .get("codec_name")
        .and_then(Value::as_str)
        .unwrap_or("unknown")
        .to_owned();

    let loudness = run(
        "ffmpeg",
        &[
            "-hide_banner",
            "-nostats",
            "-i",
            &path.to_string_lossy(),
            "-filter_complex",
            "ebur128=peak=true:framelog=verbose",
            "-f",
            "null",
            "-",
        ],
    )?;
    let stderr = String::from_utf8_lossy(&loudness.stderr);
    let pattern = Regex::new(
        r"(?is)Integrated loudness:\s*I:\s*(?<lufs>-?(?:inf|\d+(?:\.\d+)?))\s*LUFS.*?Loudness range:\s*LRA:\s*(?<lra>\d+(?:\.\d+)?)\s*LU.*?True peak:\s*Peak:\s*(?<peak>-?(?:inf|\d+(?:\.\d+)?))\s*dBFS",
    )
    .map_err(|error| PlatformError::Validation(format!("invalid loudness parser: {error}")))?;
    let captures = pattern.captures(&stderr).ok_or_else(|| {
        PlatformError::Validation("FFmpeg EBU R128 summary could not be parsed".into())
    })?;
    let raw_lufs = captures
        .name("lufs")
        .ok_or_else(|| PlatformError::Validation("FFmpeg omitted integrated LUFS".into()))?
        .as_str();
    let integrated_lufs = if raw_lufs.eq_ignore_ascii_case("-inf") {
        None
    } else {
        Some(raw_lufs.parse().map_err(|error| {
            PlatformError::Validation(format!("invalid integrated LUFS: {error}"))
        })?)
    };
    let loudness_range_lu = captures
        .name("lra")
        .ok_or_else(|| PlatformError::Validation("FFmpeg omitted loudness range".into()))?
        .as_str()
        .parse()
        .map_err(|error| PlatformError::Validation(format!("invalid loudness range: {error}")))?;
    let raw_peak = captures
        .name("peak")
        .ok_or_else(|| PlatformError::Validation("FFmpeg omitted true peak".into()))?
        .as_str();
    let true_peak_dbtp =
        if raw_peak.eq_ignore_ascii_case("-inf") {
            None
        } else {
            Some(raw_peak.parse().map_err(|error| {
                PlatformError::Validation(format!("invalid true peak: {error}"))
            })?)
        };
    let result = MediaInspection {
        duration_seconds,
        sample_rate_hz,
        channels,
        codec,
        integrated_lufs,
        integrated_lufs_status: if integrated_lufs.is_some() {
            "measured"
        } else {
            "below_measurement_floor"
        }
        .into(),
        loudness_range_lu,
        true_peak_dbtp,
        true_peak_status: if true_peak_dbtp.is_some() {
            "measured"
        } else {
            "below_measurement_floor"
        }
        .into(),
    };
    if result.duration_seconds <= 0.0 || result.sample_rate_hz == 0 || result.channels == 0 {
        return Err(PlatformError::Validation(
            "media inspection returned non-positive technical metadata".into(),
        ));
    }
    Ok(result)
}

pub fn tool_version(name: &str) -> Result<String, PlatformError> {
    let output = run(name, &["-version"])?;
    Ok(String::from_utf8_lossy(&output.stdout)
        .lines()
        .next()
        .unwrap_or("unknown")
        .to_owned())
}

fn run(program: &str, arguments: &[&str]) -> Result<Output, PlatformError> {
    run_with_timeout(program, arguments, Duration::from_mins(1))
}

fn run_with_timeout(
    program: &str,
    arguments: &[&str],
    timeout: Duration,
) -> Result<Output, PlatformError> {
    let mut child = Command::new(program)
        .args(arguments)
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .map_err(|error| {
            if error.kind() == std::io::ErrorKind::NotFound {
                PlatformError::ToolUnavailable(format!("{program} is unavailable on PATH"))
            } else {
                PlatformError::Validation(format!("cannot start {program}: {error}"))
            }
        })?;
    let stdout = child
        .stdout
        .take()
        .ok_or_else(|| PlatformError::Validation(format!("cannot capture {program} stdout")))?;
    let stderr = child
        .stderr
        .take()
        .ok_or_else(|| PlatformError::Validation(format!("cannot capture {program} stderr")))?;
    let stdout_reader = thread::spawn(move || read_stdout(stdout));
    let stderr_reader = thread::spawn(move || read_stderr(stderr));

    let Some(status) = child.wait_timeout(timeout).map_err(|error| {
        PlatformError::Validation(format!("cannot wait for {program}: {error}"))
    })?
    else {
        let _ = child.kill();
        let _ = child.wait();
        let _ = stdout_reader.join();
        let _ = stderr_reader.join();
        return Err(PlatformError::ToolTimeout(format!(
            "{program} exceeded the {} second execution limit",
            timeout.as_secs_f64()
        )));
    };
    let stdout = join_reader(stdout_reader, program, "stdout")?;
    let stderr = join_reader(stderr_reader, program, "stderr")?;
    let output = Output {
        status,
        stdout,
        stderr,
    };
    if output.status.success() {
        return Ok(output);
    }
    let stderr = String::from_utf8_lossy(&output.stderr);
    let detail = stderr.lines().last().unwrap_or("unknown error");
    Err(PlatformError::Validation(format!(
        "{program} failed: {detail}"
    )))
}

fn read_stdout(mut stream: ChildStdout) -> std::io::Result<Vec<u8>> {
    let mut bytes = Vec::new();
    stream.read_to_end(&mut bytes)?;
    Ok(bytes)
}

fn read_stderr(mut stream: ChildStderr) -> std::io::Result<Vec<u8>> {
    let mut bytes = Vec::new();
    stream.read_to_end(&mut bytes)?;
    Ok(bytes)
}

fn join_reader(
    reader: thread::JoinHandle<std::io::Result<Vec<u8>>>,
    program: &str,
    stream: &str,
) -> Result<Vec<u8>, PlatformError> {
    reader
        .join()
        .map_err(|_| PlatformError::Validation(format!("{program} {stream} reader panicked")))?
        .map_err(|error| {
            PlatformError::Validation(format!("cannot read {program} {stream}: {error}"))
        })
}

#[cfg(all(test, windows))]
mod tests {
    use super::*;

    #[test]
    fn external_process_is_killed_after_timeout() {
        let error = run_with_timeout(
            "powershell",
            &["-NoProfile", "-Command", "Start-Sleep -Seconds 5"],
            Duration::from_millis(50),
        )
        .expect_err("sleeping process must time out");
        assert!(matches!(error, PlatformError::ToolTimeout(_)));
        assert_eq!(error.code(), "TOOL_TIMEOUT");
        assert!(error.retryable());
    }
}
