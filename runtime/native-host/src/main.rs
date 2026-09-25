#![forbid(unsafe_op_in_unsafe_fn)]

mod events;
mod platform;
mod protocol;

use events::HostHello;
use events::ProtocolOutput;
use platform::ControlSignal;
use protocol::ClientMessage;
use protocol::OperationIdentity;
use protocol::parse_client_message;
use protocol::read_frame;
use std::io;
use std::sync::mpsc;
use std::thread;
use std::time::SystemTime;
use std::time::UNIX_EPOCH;

fn main() {
    if let Err(error) = run() {
        eprintln!("cap-native-host: {error}");
        std::process::exit(1);
    }
}

fn run() -> Result<(), String> {
    let host_instance_id = host_instance_id();
    let output = ProtocolOutput::new(io::stdout());
    output
        .write_hello(&HostHello::new(host_instance_id.clone()))
        .map_err(|error| error.to_string())?;

    let mut input = io::stdin();
    let first = read_frame(&mut input)
        .map_err(|error| error.to_string())?
        .ok_or_else(|| "owner closed stdin before BeginOperation".to_owned())?;
    let begin = match parse_client_message(&first).map_err(|error| error.to_string())? {
        ClientMessage::Begin(begin) => begin,
        ClientMessage::Cancel(_) => {
            return Err("CancelOperation received before BeginOperation".into());
        }
    };
    begin.validate().map_err(|error| error.to_string())?;

    let identity = OperationIdentity::from(&begin);
    let sink = output.sink(identity.clone(), host_instance_id);
    let (control_tx, control_rx) = mpsc::channel();
    spawn_control_reader(input, identity, control_tx);

    platform::run_operation(&begin, &sink, control_rx)
}

fn spawn_control_reader(
    mut input: io::Stdin,
    identity: OperationIdentity,
    sender: mpsc::Sender<ControlSignal>,
) {
    thread::spawn(move || {
        loop {
            let payload = match read_frame(&mut input) {
                Ok(Some(payload)) => payload,
                Ok(None) => {
                    let _ = sender.send(ControlSignal::OwnerLost);
                    return;
                }
                Err(error) => {
                    let _ = sender.send(ControlSignal::ProtocolViolation(error.to_string()));
                    return;
                }
            };

            match parse_client_message(&payload) {
                Ok(ClientMessage::Cancel(cancel)) => {
                    if let Err(error) = cancel.validate_for(&identity) {
                        let _ = sender.send(ControlSignal::ProtocolViolation(error.to_string()));
                        return;
                    }
                    let _ = sender.send(ControlSignal::Cancel);
                }
                Ok(ClientMessage::Begin(_)) => {
                    let _ = sender.send(ControlSignal::ProtocolViolation(
                        "second BeginOperation is forbidden".into(),
                    ));
                    return;
                }
                Err(error) => {
                    let _ = sender.send(ControlSignal::ProtocolViolation(error.to_string()));
                    return;
                }
            }
        }
    });
}

fn host_instance_id() -> String {
    let nanos = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_nanos();
    format!("host-{}-{nanos:x}", std::process::id())
}
