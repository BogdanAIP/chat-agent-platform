use std::path::Path;

use serde::Serialize;
use serde_json::Value;
use uuid::Uuid;

use crate::config::load_json_yaml;
use crate::error::PlatformError;

#[derive(Debug, Clone, Serialize)]
pub struct PolicyDecision {
    pub decision_id: String,
    pub capability: String,
    pub effective_risk: String,
    pub enforced_by: String,
    pub reasons: Vec<String>,
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
        if parameters.get("external_destination").is_some() {
            return Err(PlatformError::PolicyDenied(
                "media.inspect does not permit external destinations".into(),
            ));
        }
        let mut reasons = vec![
            format!("configured_decision={configured}"),
            format!("data_class={data_class}"),
        ];
        if requested_risk_hint.is_some() {
            reasons.push("requested_risk_hint_ignored_for_enforcement".into());
        }
        Ok(PolicyDecision {
            decision_id: format!("pol_{}", Uuid::new_v4().simple()),
            capability: capability.into(),
            effective_risk: configured.into(),
            enforced_by: rule
                .get("enforced_by")
                .and_then(Value::as_str)
                .unwrap_or("unknown")
                .into(),
            reasons,
        })
    }
}
