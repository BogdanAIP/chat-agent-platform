use jsonschema::Validator;
use serde_json::Value;

use crate::error::PlatformError;

pub fn validate(instance: &Value, contract: &str) -> Result<(), PlatformError> {
    let schema_text = schema(contract).ok_or_else(|| {
        PlatformError::Validation(format!("unknown embedded contract: {contract}"))
    })?;
    let schema_value: Value = serde_json::from_str(schema_text)
        .map_err(|error| PlatformError::Validation(format!("invalid embedded schema: {error}")))?;
    let validator: Validator = jsonschema::validator_for(&schema_value).map_err(|error| {
        PlatformError::Validation(format!("invalid contract {contract}: {error}"))
    })?;
    let mut errors = validator.iter_errors(instance);
    if let Some(error) = errors.next() {
        return Err(PlatformError::Validation(format!(
            "contract {contract} failed at {}: {error}",
            error.instance_path()
        )));
    }
    Ok(())
}

fn schema(name: &str) -> Option<&'static str> {
    match name {
        "tool-request-v1.schema.json" => Some(include_str!(
            "../../../contracts/tool-request-v1.schema.json"
        )),
        "tool-v1.schema.json" => Some(include_str!("../../../contracts/tool-v1.schema.json")),
        "artifact-v1.schema.json" => {
            Some(include_str!("../../../contracts/artifact-v1.schema.json"))
        }
        "policy-decision-v1.schema.json" => Some(include_str!(
            "../../../contracts/policy-decision-v1.schema.json"
        )),
        "confirmation-v1.schema.json" => Some(include_str!(
            "../../../contracts/confirmation-v1.schema.json"
        )),
        "secret-ref-v1.schema.json" => {
            Some(include_str!("../../../contracts/secret-ref-v1.schema.json"))
        }
        "job-v1.schema.json" => Some(include_str!("../../../contracts/job-v1.schema.json")),
        "relay-request-v1.schema.json" => Some(include_str!(
            "../../../contracts/relay-request-v1.schema.json"
        )),
        "relay-response-v1.schema.json" => Some(include_str!(
            "../../../contracts/relay-response-v1.schema.json"
        )),
        _ => None,
    }
}
