use super::ControlSignal;
use crate::events::DeliveryState;
use crate::events::EventSink;
use crate::events::TerminalReason;
use crate::events::TerminalSnapshot;
use crate::protocol::BeginOperation;
use crate::protocol::MAX_RAW_OUTPUT_CHUNK;
use crate::protocol::MAX_WINDOWS_COMMAND_LINE_UTF16;
use base64::Engine as _;
use base64::engine::general_purpose::STANDARD as BASE64_STANDARD;
use sha2::Digest;
use sha2::Sha256;
use std::ffi::c_void;
use std::fs::File;
use std::io;
use std::io::Read;
use std::mem::size_of;
use std::mem::size_of_val;
use std::os::windows::io::AsRawHandle;
use std::os::windows::io::FromRawHandle;
use std::os::windows::io::OwnedHandle;
use std::path::Path;
use std::ptr;
use std::sync::Arc;
use std::sync::Mutex;
use std::sync::mpsc;
use std::sync::mpsc::Receiver;
use std::thread;
use std::time::Duration;
use std::time::Instant;
use windows_sys::Win32::Foundation::HANDLE;
use windows_sys::Win32::Foundation::HANDLE_FLAG_INHERIT;
use windows_sys::Win32::Foundation::SetHandleInformation;
use windows_sys::Win32::Foundation::WAIT_OBJECT_0;
use windows_sys::Win32::Foundation::WAIT_TIMEOUT;
use windows_sys::Win32::Security::SECURITY_ATTRIBUTES;
use windows_sys::Win32::System::JobObjects::AssignProcessToJobObject;
use windows_sys::Win32::System::JobObjects::CreateJobObjectW;
use windows_sys::Win32::System::JobObjects::JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE;
use windows_sys::Win32::System::JobObjects::JOBOBJECT_BASIC_ACCOUNTING_INFORMATION;
use windows_sys::Win32::System::JobObjects::JOBOBJECT_EXTENDED_LIMIT_INFORMATION;
use windows_sys::Win32::System::JobObjects::JobObjectBasicAccountingInformation;
use windows_sys::Win32::System::JobObjects::JobObjectExtendedLimitInformation;
use windows_sys::Win32::System::JobObjects::QueryInformationJobObject;
use windows_sys::Win32::System::JobObjects::SetInformationJobObject;
use windows_sys::Win32::System::JobObjects::TerminateJobObject;
use windows_sys::Win32::System::Pipes::CreatePipe;
use windows_sys::Win32::System::Threading::CREATE_NO_WINDOW;
use windows_sys::Win32::System::Threading::CREATE_SUSPENDED;
use windows_sys::Win32::System::Threading::CREATE_UNICODE_ENVIRONMENT;
use windows_sys::Win32::System::Threading::CreateProcessW;
use windows_sys::Win32::System::Threading::DeleteProcThreadAttributeList;
use windows_sys::Win32::System::Threading::EXTENDED_STARTUPINFO_PRESENT;
use windows_sys::Win32::System::Threading::GetExitCodeProcess;
use windows_sys::Win32::System::Threading::InitializeProcThreadAttributeList;
use windows_sys::Win32::System::Threading::PROC_THREAD_ATTRIBUTE_HANDLE_LIST;
use windows_sys::Win32::System::Threading::PROCESS_INFORMATION;
use windows_sys::Win32::System::Threading::ResumeThread;
use windows_sys::Win32::System::Threading::STARTF_USESTDHANDLES;
use windows_sys::Win32::System::Threading::STARTUPINFOEXW;
use windows_sys::Win32::System::Threading::STILL_ACTIVE;
use windows_sys::Win32::System::Threading::TerminateProcess;
use windows_sys::Win32::System::Threading::UpdateProcThreadAttribute;
use windows_sys::Win32::System::Threading::WaitForSingleObject;

const TERMINATION_EXIT_CODE: u32 = 0xCA01;
const POLL_INTERVAL: Duration = Duration::from_millis(20);
const TERMINATION_QUIESCE_TIMEOUT: Duration = Duration::from_secs(5);

pub fn run_operation(
    begin: &BeginOperation,
    sink: &EventSink,
    control: Receiver<ControlSignal>,
) -> Result<(), String> {
    validate_windows_payload(begin)?;

    let prepared = PreparedOperation::new(begin).map_err(|error| error.to_string())?;
    sink.operation_prepared()
        .map_err(|error| error.to_string())?;

    let mut child = match prepared.spawn(begin) {
        Ok(child) => child,
        Err(error) => {
            let empty = empty_sha256();
            let reason = match error.kind {
                SpawnFailureKind::Assignment => TerminalReason::AssignmentFailed,
                SpawnFailureKind::Resume => TerminalReason::ResumeFailed,
                SpawnFailureKind::Spawn => TerminalReason::SpawnFailed,
            };
            sink.terminal(&TerminalSnapshot {
                delivery_state: DeliveryState::NeverRunnable,
                reason,
                root_exit_code: None,
                target_ever_runnable: false,
                tree_quiescent: true,
                stdout_bytes: 0,
                stderr_bytes: 0,
                stdout_sha256: empty.clone(),
                stderr_sha256: empty,
                output_complete: true,
            })
            .map_err(|write_error| write_error.to_string())?;
            return Ok(());
        }
    };

    let output_budget = Arc::new(Mutex::new(OutputBudget {
        used: 0,
        limit: begin.max_output_bytes,
    }));
    let (output_signal_tx, output_signal_rx) = mpsc::channel();
    let stdout_thread = spawn_output_reader(
        "stdout",
        child.stdout,
        Arc::clone(&output_budget),
        output_signal_tx.clone(),
        sink.clone(),
    );
    let stderr_thread = spawn_output_reader(
        "stderr",
        child.stderr,
        output_budget,
        output_signal_tx,
        sink.clone(),
    );

    child
        .resume()
        .map_err(|error| format!("failed to resume contained target: {error}"))?;
    sink.process_spawned(child.process_id)
        .map_err(|error| error.to_string())?;

    let started = Instant::now();
    let mut root_exit_code = None;
    let mut terminal_reason = None;
    let mut delivery_state = None;
    let mut output_complete = true;

    loop {
        while let Ok(signal) = control.try_recv() {
            match signal {
                ControlSignal::Cancel => {
                    terminate_for_reason(
                        &child.job,
                        TerminalReason::Cancelled,
                        &mut terminal_reason,
                        &mut delivery_state,
                    )?;
                }
                ControlSignal::OwnerLost => {
                    terminate_for_reason(
                        &child.job,
                        TerminalReason::OwnerLost,
                        &mut terminal_reason,
                        &mut delivery_state,
                    )?;
                }
                ControlSignal::ProtocolViolation(message) => {
                    eprintln!("native-host protocol violation after Begin: {message}");
                    terminate_for_reason(
                        &child.job,
                        TerminalReason::ProtocolViolation,
                        &mut terminal_reason,
                        &mut delivery_state,
                    )?;
                }
            }
        }

        while let Ok(signal) = output_signal_rx.try_recv() {
            match signal {
                OutputSignal::LimitExceeded => {
                    output_complete = false;
                    terminate_for_reason(
                        &child.job,
                        TerminalReason::OutputLimitExceeded,
                        &mut terminal_reason,
                        &mut delivery_state,
                    )?;
                }
                OutputSignal::ReadFailed(message) => {
                    eprintln!("native-host output read failed: {message}");
                    output_complete = false;
                    terminate_for_reason(
                        &child.job,
                        TerminalReason::OutputFailure,
                        &mut terminal_reason,
                        &mut delivery_state,
                    )?;
                }
                OutputSignal::WriteFailed(message) => {
                    eprintln!("native-host protocol output failed: {message}");
                    output_complete = false;
                    child.job.terminate().map_err(|error| error.to_string())?;
                    return Err("protocol output channel failed after target start".into());
                }
            }
        }

        if terminal_reason.is_none()
            && started.elapsed() >= Duration::from_millis(begin.max_runtime_ms)
        {
            output_complete = false;
            terminate_for_reason(
                &child.job,
                TerminalReason::Timeout,
                &mut terminal_reason,
                &mut delivery_state,
            )?;
        }

        if root_exit_code.is_none() {
            if let Some(code) = child.root_exit_code().map_err(|error| error.to_string())? {
                root_exit_code = Some(code);
                sink.root_exited(code).map_err(|error| error.to_string())?;
            }
        }

        let active = child
            .job
            .active_processes()
            .map_err(|error| error.to_string())?;

        if terminal_reason.is_some() {
            if active == 0 {
                break;
            }
            if started.elapsed()
                >= Duration::from_millis(begin.max_runtime_ms) + TERMINATION_QUIESCE_TIMEOUT
            {
                delivery_state = Some(DeliveryState::HostFailureAfterStart);
                terminal_reason = Some(TerminalReason::LifecycleFailure);
                output_complete = false;
                break;
            }
        } else if active == 0 {
            delivery_state = Some(DeliveryState::TreeExited);
            terminal_reason = Some(TerminalReason::TreeExited);
            break;
        }

        thread::sleep(POLL_INTERVAL);
    }

    let stdout_summary = stdout_thread
        .join()
        .map_err(|_| "stdout reader thread panicked".to_owned())?;
    let stderr_summary = stderr_thread
        .join()
        .map_err(|_| "stderr reader thread panicked".to_owned())?;

    output_complete &= stdout_summary.complete && stderr_summary.complete;

    if root_exit_code.is_none() {
        root_exit_code = child.root_exit_code().map_err(|error| error.to_string())?;
    }

    let tree_quiescent = child
        .job
        .active_processes()
        .map_err(|error| error.to_string())?
        == 0;

    let snapshot = TerminalSnapshot {
        delivery_state: delivery_state.unwrap_or(DeliveryState::HostFailureAfterStart),
        reason: terminal_reason.unwrap_or(TerminalReason::LifecycleFailure),
        root_exit_code,
        target_ever_runnable: true,
        tree_quiescent,
        stdout_bytes: stdout_summary.bytes,
        stderr_bytes: stderr_summary.bytes,
        stdout_sha256: stdout_summary.sha256,
        stderr_sha256: stderr_summary.sha256,
        output_complete,
    };
    sink.terminal(&snapshot)
        .map_err(|error| error.to_string())?;
    Ok(())
}

fn terminate_for_reason(
    job: &JobObject,
    reason: TerminalReason,
    terminal_reason: &mut Option<TerminalReason>,
    delivery_state: &mut Option<DeliveryState>,
) -> Result<(), String> {
    if terminal_reason.is_none() {
        job.terminate().map_err(|error| error.to_string())?;
        *terminal_reason = Some(reason);
        *delivery_state = Some(DeliveryState::Terminated);
    }
    Ok(())
}

fn validate_windows_payload(begin: &BeginOperation) -> Result<(), String> {
    let extension = Path::new(&begin.executable)
        .extension()
        .and_then(|value| value.to_str())
        .unwrap_or_default()
        .to_ascii_lowercase();
    if extension == "bat" || extension == "cmd" {
        return Err("batch-file executables are outside Native Host v1".into());
    }
    let command_line = build_command_line(&begin.executable, &begin.argv);
    if command_line.encode_utf16().count() > MAX_WINDOWS_COMMAND_LINE_UTF16 {
        return Err("encoded Windows command line exceeds hard ceiling".into());
    }
    Ok(())
}

struct PreparedOperation {
    job: JobObject,
    stdin_read: OwnedHandle,
    stdin_write: OwnedHandle,
    stdout_read: OwnedHandle,
    stdout_write: OwnedHandle,
    stderr_read: OwnedHandle,
    stderr_write: OwnedHandle,
}

impl PreparedOperation {
    fn new(_begin: &BeginOperation) -> io::Result<Self> {
        let job = JobObject::new()?;
        let (stdin_read, stdin_write) = create_pipe_pair()?;
        let (stdout_read, stdout_write) = create_pipe_pair()?;
        let (stderr_read, stderr_write) = create_pipe_pair()?;
        clear_inherit(stdin_write.as_raw_handle() as HANDLE)?;
        clear_inherit(stdout_read.as_raw_handle() as HANDLE)?;
        clear_inherit(stderr_read.as_raw_handle() as HANDLE)?;
        Ok(Self {
            job,
            stdin_read,
            stdin_write,
            stdout_read,
            stdout_write,
            stderr_read,
            stderr_write,
        })
    }

    fn spawn(self, begin: &BeginOperation) -> Result<ContainedProcess, SpawnFailure> {
        let mut command_line: Vec<u16> = build_command_line(&begin.executable, &begin.argv)
            .encode_utf16()
            .chain(std::iter::once(0))
            .collect();
        let executable: Vec<u16> = begin
            .executable
            .encode_utf16()
            .chain(std::iter::once(0))
            .collect();
        let cwd: Vec<u16> = begin.cwd.encode_utf16().chain(std::iter::once(0)).collect();
        let environment = build_environment_block(begin);

        let child_handles = [
            self.stdin_read.as_raw_handle() as HANDLE,
            self.stdout_write.as_raw_handle() as HANDLE,
            self.stderr_write.as_raw_handle() as HANDLE,
        ];

        let mut attributes = ProcThreadAttributes::new(1).map_err(SpawnFailure::spawn)?;
        attributes
            .set_handle_list(&child_handles)
            .map_err(SpawnFailure::spawn)?;

        let mut startup: STARTUPINFOEXW = unsafe { std::mem::zeroed() };
        startup.StartupInfo.cb = size_of::<STARTUPINFOEXW>() as u32;
        startup.StartupInfo.dwFlags = STARTF_USESTDHANDLES;
        startup.StartupInfo.hStdInput = child_handles[0];
        startup.StartupInfo.hStdOutput = child_handles[1];
        startup.StartupInfo.hStdError = child_handles[2];
        startup.lpAttributeList = attributes.ptr;

        let mut process_information: PROCESS_INFORMATION = unsafe { std::mem::zeroed() };
        let flags = CREATE_SUSPENDED
            | CREATE_UNICODE_ENVIRONMENT
            | CREATE_NO_WINDOW
            | EXTENDED_STARTUPINFO_PRESENT;

        let created = unsafe {
            CreateProcessW(
                executable.as_ptr(),
                command_line.as_mut_ptr(),
                ptr::null(),
                ptr::null(),
                1,
                flags,
                environment.as_ptr().cast::<c_void>(),
                cwd.as_ptr(),
                ptr::addr_of!(startup.StartupInfo),
                ptr::addr_of_mut!(process_information),
            )
        };
        if created == 0 {
            return Err(SpawnFailure::spawn(io::Error::last_os_error()));
        }

        let process = unsafe { OwnedHandle::from_raw_handle(process_information.hProcess.cast()) };
        let thread_handle =
            unsafe { OwnedHandle::from_raw_handle(process_information.hThread.cast()) };

        if unsafe {
            AssignProcessToJobObject(
                self.job.handle.as_raw_handle() as HANDLE,
                process.as_raw_handle() as HANDLE,
            )
        } == 0
        {
            let error = io::Error::last_os_error();
            unsafe {
                TerminateProcess(process.as_raw_handle() as HANDLE, TERMINATION_EXIT_CODE);
                WaitForSingleObject(process.as_raw_handle() as HANDLE, 5_000);
            }
            return Err(SpawnFailure::assignment(error));
        }

        drop(self.stdin_read);
        drop(self.stdout_write);
        drop(self.stderr_write);
        drop(self.stdin_write);

        Ok(ContainedProcess {
            job: self.job,
            process,
            thread: Some(thread_handle),
            process_id: process_information.dwProcessId,
            stdout: File::from(self.stdout_read),
            stderr: File::from(self.stderr_read),
        })
    }
}

struct ContainedProcess {
    job: JobObject,
    process: OwnedHandle,
    thread: Option<OwnedHandle>,
    process_id: u32,
    stdout: File,
    stderr: File,
}

impl ContainedProcess {
    fn resume(&mut self) -> io::Result<()> {
        let thread = self
            .thread
            .take()
            .ok_or_else(|| io::Error::other("primary thread handle missing"))?;
        let result = unsafe { ResumeThread(thread.as_raw_handle() as HANDLE) };
        if result == u32::MAX {
            let error = io::Error::last_os_error();
            let _ = self.job.terminate();
            return Err(error);
        }
        drop(thread);
        Ok(())
    }

    fn root_exit_code(&self) -> io::Result<Option<u32>> {
        let wait = unsafe { WaitForSingleObject(self.process.as_raw_handle() as HANDLE, 0) };
        match wait {
            WAIT_TIMEOUT => Ok(None),
            WAIT_OBJECT_0 => {
                let mut code = 0_u32;
                if unsafe { GetExitCodeProcess(self.process.as_raw_handle() as HANDLE, &mut code) }
                    == 0
                {
                    return Err(io::Error::last_os_error());
                }
                if code == STILL_ACTIVE {
                    Ok(None)
                } else {
                    Ok(Some(code))
                }
            }
            _ => Err(io::Error::last_os_error()),
        }
    }
}

struct JobObject {
    handle: OwnedHandle,
}

impl JobObject {
    fn new() -> io::Result<Self> {
        let raw = unsafe { CreateJobObjectW(ptr::null(), ptr::null()) };
        if raw.is_null() {
            return Err(io::Error::last_os_error());
        }
        let handle = unsafe { OwnedHandle::from_raw_handle(raw.cast()) };
        let mut limits = JOBOBJECT_EXTENDED_LIMIT_INFORMATION::default();
        limits.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE;
        let configured = unsafe {
            SetInformationJobObject(
                handle.as_raw_handle() as HANDLE,
                JobObjectExtendedLimitInformation,
                ptr::addr_of_mut!(limits).cast::<c_void>(),
                size_of_val(&limits) as u32,
            )
        };
        if configured == 0 {
            return Err(io::Error::last_os_error());
        }
        Ok(Self { handle })
    }

    fn terminate(&self) -> io::Result<()> {
        if unsafe {
            TerminateJobObject(self.handle.as_raw_handle() as HANDLE, TERMINATION_EXIT_CODE)
        } == 0
        {
            Err(io::Error::last_os_error())
        } else {
            Ok(())
        }
    }

    fn active_processes(&self) -> io::Result<u32> {
        let mut info = JOBOBJECT_BASIC_ACCOUNTING_INFORMATION::default();
        let ok = unsafe {
            QueryInformationJobObject(
                self.handle.as_raw_handle() as HANDLE,
                JobObjectBasicAccountingInformation,
                ptr::addr_of_mut!(info).cast::<c_void>(),
                size_of_val(&info) as u32,
                ptr::null_mut(),
            )
        };
        if ok == 0 {
            Err(io::Error::last_os_error())
        } else {
            Ok(info.ActiveProcesses)
        }
    }
}

struct ProcThreadAttributes {
    storage: Vec<u8>,
    ptr: *mut c_void,
}

impl ProcThreadAttributes {
    fn new(count: u32) -> io::Result<Self> {
        let mut bytes = 0_usize;
        unsafe {
            InitializeProcThreadAttributeList(ptr::null_mut(), count, 0, &mut bytes);
        }
        if bytes == 0 {
            return Err(io::Error::last_os_error());
        }
        let mut storage = vec![0_u8; bytes];
        let ptr = storage.as_mut_ptr().cast::<c_void>();
        if unsafe { InitializeProcThreadAttributeList(ptr, count, 0, &mut bytes) } == 0 {
            return Err(io::Error::last_os_error());
        }
        Ok(Self { storage, ptr })
    }

    fn set_handle_list(&mut self, handles: &[HANDLE]) -> io::Result<()> {
        let ok = unsafe {
            UpdateProcThreadAttribute(
                self.ptr,
                0,
                PROC_THREAD_ATTRIBUTE_HANDLE_LIST as usize,
                handles.as_ptr().cast::<c_void>(),
                size_of_val(handles),
                ptr::null_mut(),
                ptr::null(),
            )
        };
        if ok == 0 {
            Err(io::Error::last_os_error())
        } else {
            Ok(())
        }
    }
}

impl Drop for ProcThreadAttributes {
    fn drop(&mut self) {
        if !self.ptr.is_null() {
            unsafe {
                DeleteProcThreadAttributeList(self.ptr);
            }
        }
        let _ = self.storage.len();
    }
}

fn create_pipe_pair() -> io::Result<(OwnedHandle, OwnedHandle)> {
    let mut security = SECURITY_ATTRIBUTES {
        nLength: size_of::<SECURITY_ATTRIBUTES>() as u32,
        lpSecurityDescriptor: ptr::null_mut(),
        bInheritHandle: 1,
    };
    let mut read: HANDLE = ptr::null_mut();
    let mut write: HANDLE = ptr::null_mut();
    if unsafe { CreatePipe(&mut read, &mut write, &mut security, 0) } == 0 {
        return Err(io::Error::last_os_error());
    }
    let read = unsafe { OwnedHandle::from_raw_handle(read.cast()) };
    let write = unsafe { OwnedHandle::from_raw_handle(write.cast()) };
    Ok((read, write))
}

fn clear_inherit(handle: HANDLE) -> io::Result<()> {
    if unsafe { SetHandleInformation(handle, HANDLE_FLAG_INHERIT, 0) } == 0 {
        Err(io::Error::last_os_error())
    } else {
        Ok(())
    }
}

fn build_environment_block(begin: &BeginOperation) -> Vec<u16> {
    let mut entries: Vec<_> = begin.env.iter().collect();
    entries.sort_by(|(left, _), (right, _)| {
        left.to_uppercase()
            .cmp(&right.to_uppercase())
            .then_with(|| left.cmp(right))
    });
    let mut block = Vec::new();
    for (name, value) in entries {
        block.extend(name.encode_utf16());
        block.push('=' as u16);
        block.extend(value.encode_utf16());
        block.push(0);
    }
    block.push(0);
    if block.len() == 1 {
        block.push(0);
    }
    block
}

fn build_command_line(executable: &str, argv: &[String]) -> String {
    std::iter::once(executable)
        .chain(argv.iter().map(String::as_str))
        .map(quote_windows_arg)
        .collect::<Vec<_>>()
        .join(" ")
}

fn quote_windows_arg(arg: &str) -> String {
    if !arg.is_empty() && !arg.chars().any(|ch| ch.is_whitespace() || ch == '"') {
        return arg.to_owned();
    }

    let mut result = String::from("\"");
    let mut backslashes = 0_usize;
    for ch in arg.chars() {
        match ch {
            '\\' => backslashes += 1,
            '"' => {
                result.extend(std::iter::repeat_n('\\', backslashes * 2 + 1));
                result.push('"');
                backslashes = 0;
            }
            _ => {
                result.extend(std::iter::repeat_n('\\', backslashes));
                backslashes = 0;
                result.push(ch);
            }
        }
    }
    result.extend(std::iter::repeat_n('\\', backslashes * 2));
    result.push('"');
    result
}

#[derive(Debug)]
struct SpawnFailure {
    kind: SpawnFailureKind,
    error: io::Error,
}

#[derive(Clone, Copy, Debug)]
enum SpawnFailureKind {
    Spawn,
    Assignment,
    Resume,
}

impl SpawnFailure {
    fn spawn(error: io::Error) -> Self {
        Self {
            kind: SpawnFailureKind::Spawn,
            error,
        }
    }

    fn assignment(error: io::Error) -> Self {
        Self {
            kind: SpawnFailureKind::Assignment,
            error,
        }
    }

    #[allow(dead_code)]
    fn resume(error: io::Error) -> Self {
        Self {
            kind: SpawnFailureKind::Resume,
            error,
        }
    }
}

impl std::fmt::Display for SpawnFailure {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{:?}: {}", self.kind, self.error)
    }
}

enum OutputSignal {
    LimitExceeded,
    ReadFailed(String),
    WriteFailed(String),
}

struct OutputBudget {
    used: u64,
    limit: u64,
}

impl OutputBudget {
    fn consume(&mut self, bytes: usize) -> bool {
        let bytes = bytes as u64;
        match self.used.checked_add(bytes) {
            Some(next) if next <= self.limit => {
                self.used = next;
                true
            }
            _ => false,
        }
    }
}

struct StreamSummary {
    bytes: u64,
    sha256: String,
    complete: bool,
}

fn spawn_output_reader(
    stream: &'static str,
    mut file: File,
    budget: Arc<Mutex<OutputBudget>>,
    signal: mpsc::Sender<OutputSignal>,
    sink: EventSink,
) -> thread::JoinHandle<StreamSummary> {
    thread::spawn(move || {
        let mut sequence = 1_u64;
        let mut bytes = 0_u64;
        let mut hasher = Sha256::new();
        let mut buffer = vec![0_u8; MAX_RAW_OUTPUT_CHUNK];
        let mut complete = true;

        loop {
            let count = match file.read(&mut buffer) {
                Ok(0) => break,
                Ok(count) => count,
                Err(error) if error.kind() == io::ErrorKind::Interrupted => continue,
                Err(error) => {
                    complete = false;
                    let _ = signal.send(OutputSignal::ReadFailed(error.to_string()));
                    break;
                }
            };
            let allowed = match budget.lock() {
                Ok(mut budget) => budget.consume(count),
                Err(_) => false,
            };
            if !allowed {
                complete = false;
                let _ = signal.send(OutputSignal::LimitExceeded);
                break;
            }

            let chunk = &buffer[..count];
            hasher.update(chunk);
            bytes += count as u64;
            let encoded = BASE64_STANDARD.encode(chunk);
            if let Err(error) = sink.output_chunk(stream, sequence, &encoded, count) {
                complete = false;
                let _ = signal.send(OutputSignal::WriteFailed(error.to_string()));
                break;
            }
            sequence += 1;
        }

        StreamSummary {
            bytes,
            sha256: digest_hex(hasher.finalize().as_slice()),
            complete,
        }
    })
}

fn digest_hex(bytes: &[u8]) -> String {
    let mut output = String::with_capacity(bytes.len() * 2);
    for byte in bytes {
        use std::fmt::Write as _;
        let _ = write!(&mut output, "{byte:02x}");
    }
    output
}

fn empty_sha256() -> String {
    digest_hex(Sha256::digest([]).as_slice())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn quoting_round_trips_common_windows_arguments_shape() {
        assert_eq!(quote_windows_arg("simple"), "simple");
        assert_eq!(quote_windows_arg(""), "\"\"");
        assert_eq!(quote_windows_arg("a b"), "\"a b\"");
        assert_eq!(quote_windows_arg(r#"a"b"#), r#""a\"b""#);
    }

    #[test]
    fn environment_block_is_double_nul_terminated() {
        let mut begin = crate::protocol::tests_support::valid_begin_for_windows();
        begin.env.insert("B".into(), "2".into());
        begin.env.insert("A".into(), "1".into());
        let block = build_environment_block(&begin);
        assert_eq!(&block[block.len() - 2..], &[0, 0]);
    }
}
