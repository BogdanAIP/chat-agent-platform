use std::fs;
use std::path::Path;

use serde_json::Value;

use crate::error::{PlatformError, io_error};

pub fn load_json_yaml(path: &Path) -> Result<Value, PlatformError> {
    let text = fs::read_to_string(path)
        .map_err(|error| io_error(format!("cannot read config {}", path.display()), error))?;
    let value: Value = serde_json::from_str(&text).map_err(|error| {
        PlatformError::Validation(format!("cannot parse config {}: {error}", path.display()))
    })?;
    if !value.is_object() {
        return Err(PlatformError::Validation(format!(
            "config root must be an object: {}",
            path.display()
        )));
    }
    Ok(value)
}
