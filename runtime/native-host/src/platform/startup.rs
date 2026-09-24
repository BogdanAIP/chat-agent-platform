use super::ControlSignal;
use crate::events::TerminalReason;
use crate::protocol::BeginOperation;
use std::fmt::Display;
use std::sync::mpsc;
use std::sync::mpsc::Receiver;

#[derive(Debug)]
pub struct StartupFailure<E> {
    pub reason: TerminalReason,
    pub error: Option<E>,
    pub detail: Option<String>,
    pub tree_quiescent: bool,
}

pub trait NativeStartupBackend {
    type Job;
    type Prepared;
    type Suspended;
    type Started;
    type Error: Display;

    fn create_job(&mut self) -> Result<Self::Job, Self::Error>;
    fn configure_job(&mut self, job: &Self::Job) -> Result<(), Self::Error>;
    fn prepare_io(&mut self, job: Self::Job) -> Result<Self::Prepared, Self::Error>;
    fn create_process_suspended(
        &mut self,
        prepared: Self::Prepared,
        begin: &BeginOperation,
    ) -> Result<Self::Suspended, Self::Error>;
    fn assign_process_to_job(&mut self, child: &mut Self::Suspended) -> Result<(), Self::Error>;
    fn terminate_and_reap(&mut self, child: &mut Self::Suspended) -> bool;
    fn resume_primary_thread(&mut self, child: &mut Self::Suspended) -> Result<(), Self::Error>;
    fn into_started(&mut self, child: Self::Suspended) -> Self::Started;
}

pub fn prepare_native_startup<B: NativeStartupBackend>(
    backend: &mut B,
) -> Result<B::Prepared, StartupFailure<B::Error>> {
    let job = backend
        .create_job()
        .map_err(|error| failure(TerminalReason::JobCreateFailed, Some(error), true))?;
    backend
        .configure_job(&job)
        .map_err(|error| failure(TerminalReason::JobCreateFailed, Some(error), true))?;
    backend
        .prepare_io(job)
        .map_err(|error| failure(TerminalReason::HostInternalFailure, Some(error), true))
}

pub fn start_native_startup<B: NativeStartupBackend>(
    backend: &mut B,
    prepared: B::Prepared,
    begin: &BeginOperation,
    control: &Receiver<ControlSignal>,
) -> Result<B::Started, StartupFailure<B::Error>> {
    let mut child = backend
        .create_process_suspended(prepared, begin)
        .map_err(|error| failure(TerminalReason::ProcessCreateFailed, Some(error), true))?;

    if let Err(error) = backend.assign_process_to_job(&mut child) {
        let tree_quiescent = backend.terminate_and_reap(&mut child);
        return Err(failure(
            TerminalReason::JobAssignFailed,
            Some(error),
            tree_quiescent,
        ));
    }

    if let Some((reason, detail)) = pre_resume_terminal_reason(control) {
        let tree_quiescent = backend.terminate_and_reap(&mut child);
        return Err(StartupFailure {
            reason,
            error: None,
            detail,
            tree_quiescent,
        });
    }

    if let Err(error) = backend.resume_primary_thread(&mut child) {
        let tree_quiescent = backend.terminate_and_reap(&mut child);
        return Err(failure(
            TerminalReason::ProcessResumeFailed,
            Some(error),
            tree_quiescent,
        ));
    }

    Ok(backend.into_started(child))
}

fn failure<E>(
    reason: TerminalReason,
    error: Option<E>,
    tree_quiescent: bool,
) -> StartupFailure<E> {
    StartupFailure {
        reason,
        error,
        detail: None,
        tree_quiescent,
    }
}

fn pre_resume_terminal_reason(
    control: &Receiver<ControlSignal>,
) -> Option<(TerminalReason, Option<String>)> {
    match control.try_recv() {
        Ok(ControlSignal::Cancel) => Some((TerminalReason::Cancelled, None)),
        Ok(ControlSignal::OwnerLost) => Some((TerminalReason::OwnerLost, None)),
        Ok(ControlSignal::ProtocolViolation(message)) => {
            Some((TerminalReason::ProtocolRejected, Some(message)))
        }
        Err(mpsc::TryRecvError::Empty) => None,
        Err(mpsc::TryRecvError::Disconnected) => Some((TerminalReason::OwnerLost, None)),
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::sync::mpsc;

    #[derive(Clone, Copy, Debug, Eq, PartialEq)]
    enum FailAt {
        CreateJob,
        ConfigureJob,
        PrepareIo,
        CreateProcess,
        Assign,
        Resume,
    }

    #[derive(Default)]
    struct FakeBackend {
        fail_at: Option<FailAt>,
        trace: Vec<&'static str>,
    }

    impl FakeBackend {
        fn with_failure(fail_at: FailAt) -> Self {
            Self {
                fail_at: Some(fail_at),
                trace: Vec::new(),
            }
        }

        fn step(&mut self, name: &'static str, fail_at: FailAt) -> Result<(), &'static str> {
            self.trace.push(name);
            if self.fail_at == Some(fail_at) {
                Err(name)
            } else {
                Ok(())
            }
        }
    }

    impl NativeStartupBackend for FakeBackend {
        type Job = ();
        type Prepared = ();
        type Suspended = ();
        type Started = ();
        type Error = &'static str;

        fn create_job(&mut self) -> Result<Self::Job, Self::Error> {
            self.step("create_job", FailAt::CreateJob)
        }

        fn configure_job(&mut self, _job: &Self::Job) -> Result<(), Self::Error> {
            self.step("configure_job", FailAt::ConfigureJob)
        }

        fn prepare_io(&mut self, _job: Self::Job) -> Result<Self::Prepared, Self::Error> {
            self.step("prepare_io", FailAt::PrepareIo)
        }

        fn create_process_suspended(
            &mut self,
            _prepared: Self::Prepared,
            _begin: &BeginOperation,
        ) -> Result<Self::Suspended, Self::Error> {
            self.step("create_process_suspended", FailAt::CreateProcess)
        }

        fn assign_process_to_job(
            &mut self,
            _child: &mut Self::Suspended,
        ) -> Result<(), Self::Error> {
            self.step("assign_process_to_job", FailAt::Assign)
        }

        fn terminate_and_reap(&mut self, _child: &mut Self::Suspended) -> bool {
            self.trace.push("terminate_and_reap");
            true
        }

        fn resume_primary_thread(
            &mut self,
            _child: &mut Self::Suspended,
        ) -> Result<(), Self::Error> {
            self.step("resume_primary_thread", FailAt::Resume)
        }

        fn into_started(&mut self, _child: Self::Suspended) -> Self::Started {
            self.trace.push("into_started");
        }
    }

    fn begin() -> BeginOperation {
        crate::protocol::tests_support::valid_begin_for_windows()
    }

    fn empty_control() -> (mpsc::Sender<ControlSignal>, Receiver<ControlSignal>) {
        mpsc::channel()
    }

    #[test]
    fn job_create_failure_stops_before_configuration() {
        let mut backend = FakeBackend::with_failure(FailAt::CreateJob);
        let failure = prepare_native_startup(&mut backend).unwrap_err();
        assert_eq!(failure.reason, TerminalReason::JobCreateFailed);
        assert_eq!(backend.trace, ["create_job"]);
    }

    #[test]
    fn job_configuration_failure_stops_before_process_preparation() {
        let mut backend = FakeBackend::with_failure(FailAt::ConfigureJob);
        let failure = prepare_native_startup(&mut backend).unwrap_err();
        assert_eq!(failure.reason, TerminalReason::JobCreateFailed);
        assert_eq!(backend.trace, ["create_job", "configure_job"]);
    }

    #[test]
    fn process_create_failure_never_assigns_or_resumes() {
        let mut backend = FakeBackend::with_failure(FailAt::CreateProcess);
        let prepared = prepare_native_startup(&mut backend).unwrap();
        let (_tx, rx) = empty_control();
        let failure = start_native_startup(&mut backend, prepared, &begin(), &rx).unwrap_err();
        assert_eq!(failure.reason, TerminalReason::ProcessCreateFailed);
        assert_eq!(
            backend.trace,
            [
                "create_job",
                "configure_job",
                "prepare_io",
                "create_process_suspended"
            ]
        );
    }

    #[test]
    fn assignment_failure_terminates_and_never_resumes() {
        let mut backend = FakeBackend::with_failure(FailAt::Assign);
        let prepared = prepare_native_startup(&mut backend).unwrap();
        let (_tx, rx) = empty_control();
        let failure = start_native_startup(&mut backend, prepared, &begin(), &rx).unwrap_err();
        assert_eq!(failure.reason, TerminalReason::JobAssignFailed);
        assert_eq!(
            backend.trace,
            [
                "create_job",
                "configure_job",
                "prepare_io",
                "create_process_suspended",
                "assign_process_to_job",
                "terminate_and_reap"
            ]
        );
    }

    #[test]
    fn resume_failure_terminates_and_never_reports_started() {
        let mut backend = FakeBackend::with_failure(FailAt::Resume);
        let prepared = prepare_native_startup(&mut backend).unwrap();
        let (_tx, rx) = empty_control();
        let failure = start_native_startup(&mut backend, prepared, &begin(), &rx).unwrap_err();
        assert_eq!(failure.reason, TerminalReason::ProcessResumeFailed);
        assert_eq!(
            backend.trace,
            [
                "create_job",
                "configure_job",
                "prepare_io",
                "create_process_suspended",
                "assign_process_to_job",
                "resume_primary_thread",
                "terminate_and_reap"
            ]
        );
    }

    #[test]
    fn cancel_at_prepared_boundary_prevents_resume() {
        let mut backend = FakeBackend::default();
        let prepared = prepare_native_startup(&mut backend).unwrap();
        let (tx, rx) = mpsc::channel();
        tx.send(ControlSignal::Cancel).unwrap();
        let failure = start_native_startup(&mut backend, prepared, &begin(), &rx).unwrap_err();
        assert_eq!(failure.reason, TerminalReason::Cancelled);
        assert!(!backend.trace.contains(&"resume_primary_thread"));
        assert_eq!(backend.trace.last(), Some(&"terminate_and_reap"));
    }

    #[test]
    fn owner_loss_at_prepared_boundary_prevents_resume() {
        let mut backend = FakeBackend::default();
        let prepared = prepare_native_startup(&mut backend).unwrap();
        let (tx, rx) = mpsc::channel::<ControlSignal>();
        drop(tx);
        let failure = start_native_startup(&mut backend, prepared, &begin(), &rx).unwrap_err();
        assert_eq!(failure.reason, TerminalReason::OwnerLost);
        assert!(!backend.trace.contains(&"resume_primary_thread"));
        assert_eq!(backend.trace.last(), Some(&"terminate_and_reap"));
    }

    #[test]
    fn success_order_is_fixed() {
        let mut backend = FakeBackend::default();
        let prepared = prepare_native_startup(&mut backend).unwrap();
        let (_tx, rx) = empty_control();
        start_native_startup(&mut backend, prepared, &begin(), &rx).unwrap();
        assert_eq!(
            backend.trace,
            [
                "create_job",
                "configure_job",
                "prepare_io",
                "create_process_suspended",
                "assign_process_to_job",
                "resume_primary_thread",
                "into_started"
            ]
        );
    }
}
