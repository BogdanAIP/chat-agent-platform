use std::path::Path;

use serde::Serialize;
use serde_json::Value;
use sha2::{Digest, Sha256};
use uuid::Uuid;

use crate::config::load_json_yaml;
use crate::error::PlatformError;

#[derive(Debug, Clone, Serialize)]
pub struct PolicyDecision {
    pub decision_id: String,
    pub capability: String,
    pub decision: String,
    pub effective_risk: String,
    pub enforced_by: String,
    pub reasons: Vec<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub confirmation_binding: Option<String>,
}

pub struct PolicyEnforcementPoint {
    rules: Value,
}

impl PolicyEnforcementPoint {
    pub fn load(path: &Path) -> Result<Self, PlatformError> {
        let config = load_json_yaml(path)?;
        Ok(Self {
            rules: config.get("rules").cloned().unwrap_or(Value::Null),
        })
    }

    pub fn evaluate(
        &self,
        capability: &str,
        parameters: &Value,
        data_class: &str,
        requested_risk_hint: Option<&str>,
        base_risk: &str,
    ) -> Result<PolicyDecision, PlatformError> {
        let rule = self.rules.get(capability).ok_or_else(|| {
            PlatformError::PolicyDenied(format!("no policy rule for {capability}"))
        })?;
        let configured = rule
            .get("decision")
            .and_then(Value::as_str)
            .unwrap_or("deny");
        if configured == "deny" {
            return Err(PlatformError::PolicyDenied(format!(
                "capability denied by policy: {capability}"
            )));
        }
        if !matches!(configured, "allow" | "guarded") {
            return Err(PlatformError::Validation(format!(
                "unknown policy decision: {configured}"
            )));
        }
        let allowed = rule
            .get("allowed_data_classes")
            .and_then(Value::as_array)
            .is_some_and(|items| items.iter().any(|item| item.as_str() == Some(data_class)));
        if !allowed {
            return Err(PlatformError::PolicyDenied(format!(
                "data class {data_class:?} is not allowed for {capability}"
            )));
        }
        if parameters.get("external_destination").is_some()
            && !rule
                .get("external_side_effect")
                .and_then(Value::as_bool)
                .unwrap_or(false)
        {
            return Err(PlatformError::PolicyDenied(format!(
                "{capability} does not permit external destinations"
            )));
        }
        let mut effective_risk = validate_risk(base_risk)?.to_owned();
        if parameters.get("external_destination").is_some() {
            effective_risk = escalate_risk(&effective_risk).to_owned();
        }
        let mut reasons = vec![
            format!("configured_decision={configured}"),
            format!("base_risk={base_risk}"),
            format!("effective_risk={effective_risk}"),
            format!("data_class={data_class}"),
        ];
        if requested_risk_hint.is_some() {
            reasons.push("requested_risk_hint_ignored_for_enforcement".into());
        }
        let confirmation_binding = if configured == "guarded" {
            Some(build_confirmation_binding(
                capability,
                parameters,
                data_class,
                &effective_risk,
            )?)
        } else {
            None
        };
        Ok(PolicyDecision {
            decision_id: format!("pol_{}", Uuid::new_v4().simple()),
            capability: capability.into(),
            decision: configured.into(),
            effective_risk,
            enforced_by: rule
                .get("enforced_by")
                .and_then(Value::as_str)
                .unwrap_or("unknown")
                .into(),
            reasons,
            confirmation_binding,
        })
    }
}

fn validate_risk(value: &str) -> Result<&str, PlatformError> {
    match value {
        "low" | "medium" | "high" | "critical" => Ok(value),
        other => Err(PlatformError::Validation(format!(
            "unknown base risk: {other}"
        ))),
    }
}

fn escalate_risk(value: &str) -> &'static str {
    match value {
        "low" => "medium",
        "medium" => "high",
        "high" | "critical" => "critical",
        _ => "critical",
    }
}

fn build_confirmation_binding(
    capability: &str,
    parameters: &Value,
    data_class: &str,
    effective_risk: &str,
) -> Result<String, PlatformError> {
    let payload = serde_json::to_vec(&(capability, parameters, data_class, effective_risk))
        .map_err(|error| {
            PlatformError::Validation(format!("cannot serialize guarded preview: {error}"))
        })?;
    let mut hasher = Sha256::new();
    hasher.update(payload);
    Ok(format!("confirm_{:x}", hasher.finalize()))
}
