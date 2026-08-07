use std::collections::HashMap;
use std::path::Path;

use serde::{Deserialize, Serialize};

use crate::config::load_json_yaml;
use crate::error::PlatformError;

#[derive(Debug, Clone, Deserialize)]
struct ToolManifest {
    capabilities: Vec<CapabilitySpec>,
}

#[derive(Debug, Clone, Deserialize)]
struct ToolLock {
    selected: HashMap<String, String>,
}

#[derive(Debug, Clone, Deserialize)]
struct CapabilitySpec {
    capability: String,
    executor: String,
    enabled: bool,
    quality: String,
    reliability: String,
    determinism: String,
    base_risk: String,
    cost: u64,
    #[serde(default)]
    fallbacks: Vec<String>,
}

#[derive(Debug, Clone, Serialize)]
pub struct CapabilitySelection {
    pub capability: String,
    pub executor: String,
    pub quality: String,
    pub reliability: String,
    pub determinism: String,
    pub base_risk: String,
    pub cost: u64,
    pub fallbacks: Vec<String>,
}

pub struct CapabilityRegistry {
    manifest: ToolManifest,
    lock: ToolLock,
}

impl CapabilityRegistry {
    pub fn load(repo_root: &Path) -> Result<Self, PlatformError> {
        let manifest: ToolManifest = serde_json::from_value(load_json_yaml(
            &repo_root.join("config/tools.yaml"),
        )?)
        .map_err(|error| PlatformError::Validation(format!("invalid tool manifest: {error}")))?;
        let lock: ToolLock =
            serde_json::from_value(load_json_yaml(&repo_root.join("config/tool-lock.yaml"))?)
                .map_err(|error| {
                    PlatformError::Validation(format!("invalid tool lock: {error}"))
                })?;
        Ok(Self { manifest, lock })
    }

    pub fn select(
        &self,
        capability: &str,
        required_quality: &str,
        cost_limit: u64,
    ) -> Result<CapabilitySelection, PlatformError> {
        let locked_executor = self.lock.selected.get(capability).ok_or_else(|| {
            PlatformError::Validation(format!("no locked executor for capability {capability}"))
        })?;
        let spec = self
            .manifest
            .capabilities
            .iter()
            .find(|item| item.capability == capability && item.executor == *locked_executor)
            .ok_or_else(|| {
                PlatformError::Validation(format!(
                    "locked executor {locked_executor} is absent from manifest for {capability}"
                ))
            })?;
        if !spec.enabled {
            return Err(PlatformError::Validation(format!(
                "locked executor {locked_executor} is disabled"
            )));
        }
        if quality_rank(&spec.quality)? < quality_rank(required_quality)? {
            return Err(PlatformError::Validation(format!(
                "executor {locked_executor} quality {} does not satisfy required {required_quality}",
                spec.quality
            )));
        }
        if spec.cost > cost_limit {
            return Err(PlatformError::PolicyDenied(format!(
                "executor {locked_executor} cost {} exceeds request limit {cost_limit}",
                spec.cost
            )));
        }
        Ok(CapabilitySelection {
            capability: spec.capability.clone(),
            executor: spec.executor.clone(),
            quality: spec.quality.clone(),
            reliability: spec.reliability.clone(),
            determinism: spec.determinism.clone(),
            base_risk: spec.base_risk.clone(),
            cost: spec.cost,
            fallbacks: spec.fallbacks.clone(),
        })
    }
}

pub fn required_quality(repo_root: &Path, capability: &str) -> Result<String, PlatformError> {
    let config = load_json_yaml(&repo_root.join("config/capability-requirements.yaml"))?;
    let requirements = config
        .get("requirements")
        .and_then(|value| value.as_array())
        .ok_or_else(|| PlatformError::Validation("requirements must be an array".into()))?;
    let requirement = requirements
        .iter()
        .find(|item| item.get("capability").and_then(|value| value.as_str()) == Some(capability))
        .ok_or_else(|| {
            PlatformError::Validation(format!(
                "no project requirement for capability {capability}"
            ))
        })?;
    requirement
        .get("required_quality")
        .and_then(|value| value.as_str())
        .map(ToOwned::to_owned)
        .ok_or_else(|| {
            PlatformError::Validation(format!(
                "capability requirement {capability} has no required_quality"
            ))
        })
}

fn quality_rank(value: &str) -> Result<u8, PlatformError> {
    match value {
        "basic" => Ok(0),
        "standard" => Ok(1),
        "professional" => Ok(2),
        other => Err(PlatformError::Validation(format!(
            "unknown quality level: {other}"
        ))),
    }
}
