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

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MediaValidation {
    pub duration_seconds: f64,
    pub format_name: String,
    pub audio_streams: u32,
    pub video_streams: u32,
    pub subtitle_streams: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct NormalizationResult {
    pub target_lufs: f64,
    pub target_true_peak_dbtp: f64,
    pub inspection: MediaInspection,
}

pub fn inspect_media(path: &Path) -> Result<MediaInspection, PlatformError> {
    let path_text = path.to_string_lossy();
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
            &path_text,
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
            &path_text,
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

pub fn validate_media(path: &Path) -> Result<MediaValidation, PlatformError> {
    let path_text = path.to_string_lossy();
    let probe = run(
        "ffprobe",
        &[
            "-v",
            "error",
            "-show_entries",
            "format=duration,format_name:stream=codec_type",
            "-of",
            "json",
            &path_text,
        ],
    )?;
    let raw: Value = serde_json::from_slice(&probe.stdout)
        .map_err(|error| PlatformError::Validation(format!("invalid ffprobe JSON: {error}")))?;
    let format = raw
        .get("format")
        .and_then(Value::as_object)
        .ok_or_else(|| PlatformError::Validation("ffprobe returned no format block".into()))?;
    let duration_seconds = format
        .get("duration")
        .and_then(Value::as_str)
        .and_then(|value| value.parse::<f64>().ok())
        .ok_or_else(|| PlatformError::Validation("ffprobe returned invalid duration".into()))?;
    let format_name = format
        .get("format_name")
        .and_then(Value::as_str)
        .unwrap_or("unknown")
        .to_owned();
    let streams = raw
        .get("streams")
        .and_then(Value::as_array)
        .ok_or_else(|| PlatformError::Validation("ffprobe returned no stream list".into()))?;
    let count_stream = |kind: &str| -> Result<u32, PlatformError> {
        u32::try_from(
            streams
                .iter()
                .filter(|stream| stream.get("codec_type").and_then(Value::as_str) == Some(kind))
                .count(),
        )
        .map_err(|_| PlatformError::Validation("media stream count exceeds u32".into()))
    };
    let result = MediaValidation {
        duration_seconds,
        format_name,
        audio_streams: count_stream("audio")?,
        video_streams: count_stream("video")?,
        subtitle_streams: count_stream("subtitle")?,
    };
    if result.duration_seconds <= 0.0
        || result.audio_streams + result.video_streams + result.subtitle_streams == 0
    {
        return Err(PlatformError::Validation(
            "media validation found no usable timed streams".into(),
        ));
    }
    Ok(result)
}

pub fn convert_audio(
    input: &Path,
    output: &Path,
    format: &str,
) -> Result<MediaInspection, PlatformError> {
    let codec = match format {
        "wav" => "pcm_s24le",
        "flac" => "flac",
        other => {
            return Err(PlatformError::Validation(format!(
                "unsupported professional audio conversion format: {other}"
            )));
        }
    };
    let arguments = vec![
        "-y".into(),
        "-hide_banner".into(),
        "-nostdin".into(),
        "-loglevel".into(),
        "error".into(),
        "-i".into(),
        input.to_string_lossy().into_owned(),
        "-map".into(),
        "0:a:0".into(),
        "-vn".into(),
        "-c:a".into(),
        codec.into(),
        output.to_string_lossy().into_owned(),
    ];
    run_owned("ffmpeg", &arguments)?;
    inspect_media(output)
}

pub fn extract_audio(input: &Path, output: &Path) -> Result<MediaInspection, PlatformError> {
    let arguments = vec![
        "-y".into(),
        "-hide_banner".into(),
        "-nostdin".into(),
        "-loglevel".into(),
        "error".into(),
        "-i".into(),
        input.to_string_lossy().into_owned(),
        "-map".into(),
        "0:a:0".into(),
        "-vn".into(),
        "-c:a".into(),
        "pcm_s24le".into(),
        output.to_string_lossy().into_owned(),
    ];
    run_owned("ffmpeg", &arguments)?;
    inspect_media(output)
}

pub fn normalize_loudness(
    input: &Path,
    output: &Path,
    target_lufs: f64,
    target_true_peak_dbtp: f64,
) -> Result<NormalizationResult, PlatformError> {
    if !(-36.0..=-5.0).contains(&target_lufs) {
        return Err(PlatformError::Validation(
            "target LUFS must be between -36 and -5".into(),
        ));
    }
    if !(-9.0..=0.0).contains(&target_true_peak_dbtp) {
        return Err(PlatformError::Validation(
            "target true peak must be between -9 and 0 dBTP".into(),
        ));
    }
    let input_inspection = inspect_media(input)?;
    let first_filter =
        format!("loudnorm=I={target_lufs}:TP={target_true_peak_dbtp}:LRA=11:print_format=json");
    let first_arguments = vec![
        "-hide_banner".into(),
        "-nostats".into(),
        "-i".into(),
        input.to_string_lossy().into_owned(),
        "-map".into(),
        "0:a:0".into(),
        "-af".into(),
        first_filter,
        "-f".into(),
        "null".into(),
        "-".into(),
    ];
    let first = run_owned("ffmpeg", &first_arguments)?;
    let measured = loudnorm_measurements(&String::from_utf8_lossy(&first.stderr))?;
    let second_filter = format!(
        "loudnorm=I={target_lufs}:TP={target_true_peak_dbtp}:LRA=11:measured_I={}:measured_TP={}:measured_LRA={}:measured_thresh={}:offset={}:linear=true:print_format=summary",
        measured.input_i,
        measured.input_tp,
        measured.input_lra,
        measured.input_thresh,
        measured.target_offset
    );
    let second_arguments = vec![
        "-y".into(),
        "-hide_banner".into(),
        "-nostdin".into(),
        "-loglevel".into(),
        "error".into(),
        "-i".into(),
        input.to_string_lossy().into_owned(),
        "-map".into(),
        "0:a:0".into(),
        "-af".into(),
        second_filter,
        "-c:a".into(),
        "pcm_s24le".into(),
        "-ar".into(),
        input_inspection.sample_rate_hz.to_string(),
        output.to_string_lossy().into_owned(),
    ];
    run_owned("ffmpeg", &second_arguments)?;
    let inspection = inspect_media(output)?;
    if inspection.sample_rate_hz != input_inspection.sample_rate_hz {
        return Err(PlatformError::Validation(format!(
            "normalized output changed sample rate: input={} Hz output={} Hz",
            input_inspection.sample_rate_hz, inspection.sample_rate_hz
        )));
    }
    let measured_lufs = inspection.integrated_lufs.ok_or_else(|| {
        PlatformError::Validation("normalized output has no measurable integrated LUFS".into())
    })?;
    if (measured_lufs - target_lufs).abs() > 0.7 {
        return Err(PlatformError::Validation(format!(
            "normalized output missed target LUFS: measured {measured_lufs:.2}, target {target_lufs:.2}"
        )));
    }
    if let Some(peak) = inspection.true_peak_dbtp
        && peak > target_true_peak_dbtp + 0.2
    {
        return Err(PlatformError::Validation(format!(
            "normalized output exceeded target true peak: measured {peak:.2}, target {target_true_peak_dbtp:.2}"
        )));
    }
    Ok(NormalizationResult {
        target_lufs,
        target_true_peak_dbtp,
        inspection,
    })
}

pub fn mux_audio_video(
    video: &Path,
    audio: &Path,
    output: &Path,
) -> Result<MediaValidation, PlatformError> {
    let arguments = vec![
        "-y".into(),
        "-hide_banner".into(),
        "-nostdin".into(),
        "-loglevel".into(),
        "error".into(),
        "-i".into(),
        video.to_string_lossy().into_owned(),
        "-i".into(),
        audio.to_string_lossy().into_owned(),
        "-map".into(),
        "0:v:0".into(),
        "-map".into(),
        "1:a:0".into(),
        "-c:v".into(),
        "copy".into(),
        "-c:a".into(),
        "flac".into(),
        "-shortest".into(),
        output.to_string_lossy().into_owned(),
    ];
    run_owned("ffmpeg", &arguments)?;
    let validation = validate_media(output)?;
    if validation.video_streams == 0 || validation.audio_streams == 0 {
        return Err(PlatformError::Validation(
            "mux output must contain both video and audio streams".into(),
        ));
    }
    Ok(validation)
}

pub fn tool_version(name: &str) -> Result<String, PlatformError> {
    let output = run(name, &["-version"])?;
    Ok(String::from_utf8_lossy(&output.stdout)
        .lines()
        .next()
        .unwrap_or("unknown")
        .to_owned())
}

struct LoudnormMeasurements {
    input_i: String,
    input_tp: String,
    input_lra: String,
    input_thresh: String,
    target_offset: String,
}

fn loudnorm_measurements(stderr: &str) -> Result<LoudnormMeasurements, PlatformError> {
    let start = stderr.rfind('{').ok_or_else(|| {
        PlatformError::Validation("FFmpeg loudnorm emitted no JSON summary".into())
    })?;
    let relative_end = stderr[start..].find('}').ok_or_else(|| {
        PlatformError::Validation("FFmpeg loudnorm JSON summary is incomplete".into())
    })?;
    let raw: Value =
        serde_json::from_str(&stderr[start..=start + relative_end]).map_err(|error| {
            PlatformError::Validation(format!("invalid FFmpeg loudnorm JSON summary: {error}"))
        })?;
    let field = |name: &str| -> Result<String, PlatformError> {
        let value = raw
            .get(name)
            .and_then(Value::as_str)
            .ok_or_else(|| PlatformError::Validation(format!("loudnorm omitted {name}")))?;
        if matches!(value.to_ascii_lowercase().as_str(), "inf" | "-inf" | "nan") {
            return Err(PlatformError::Validation(format!(
                "loudnorm returned non-finite {name}: {value}"
            )));
        }
        Ok(value.to_owned())
    };
    Ok(LoudnormMeasurements {
        input_i: field("input_i")?,
        input_tp: field("input_tp")?,
        input_lra: field("input_lra")?,
        input_thresh: field("input_thresh")?,
        target_offset: field("target_offset")?,
    })
}

fn run_owned(program: &str, arguments: &[String]) -> Result<Output, PlatformError> {
    let borrowed: Vec<&str> = arguments.iter().map(String::as_str).collect();
    run(program, &borrowed)
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
