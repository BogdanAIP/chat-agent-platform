use std::collections::{HashMap, HashSet};
use std::path::Path;

use serde::{Deserialize, Serialize};

use crate::config::load_json_yaml;
use crate::error::PlatformError;

const TOOLS_CONTRACT: &str = "tools-v1";
const TOOL_LOCK_CONTRACT: &str = "tool-lock-v1";
const REQUIREMENTS_CONTRACT: &str = "capability-requirements-v1";

#[derive(Debug, Clone, Deserialize)]
#[serde(deny_unknown_fields)]
struct ToolManifest {
    contract_version: String,
    capabilities: Vec<CapabilitySpec>,
}

#[derive(Debug, Clone, Deserialize)]
#[serde(deny_unknown_fields)]
struct ToolLock {
    contract_version: String,
    selected: HashMap<String, String>,
}

#[derive(Debug, Clone, Deserialize)]
#[serde(deny_unknown_fields)]
struct ArtifactConstraints {
    #[serde(default)]
    allowed_data_classes: Vec<String>,
    #[serde(default)]
    requires_registered_artifact_for_reuse: Option<bool>,
}

#[derive(Debug, Clone, Deserialize)]
#[serde(deny_unknown_fields)]
struct CapabilityHealth {
    runtime_capability: String,
    required_status: String,
}

#[derive(Debug, Clone, Deserialize)]
#[serde(deny_unknown_fields)]
struct CapabilitySpec {
    capability: String,
    executor: String,
    #[serde(default)]
    execution_path: Option<String>,
    enabled: bool,
    quality: String,
    reliability: String,
    determinism: String,
    base_risk: String,
    cost: u64,
    #[serde(default)]
    artifact_constraints: Option<ArtifactConstraints>,
    #[serde(default)]
    fallbacks: Vec<String>,
    #[serde(default)]
    required_skill: Option<String>,
    #[serde(default)]
    required_qc: Vec<String>,
    #[serde(default)]
    health: Option<CapabilityHealth>,
}

#[derive(Debug, Clone, Deserialize)]
#[serde(deny_unknown_fields)]
struct CapabilityRequirements {
    contract_version: String,
    requirements: Vec<CapabilityRequirement>,
}

#[derive(Debug, Clone, Deserialize)]
#[serde(deny_unknown_fields)]
struct CapabilityRequirement {
    capability: String,
    required: bool,
    required_quality: String,
    execution_paths: Vec<String>,
    #[serde(default)]
    fallbacks: Vec<String>,
    #[serde(default)]
    acceptance: Vec<String>,
}

#[derive(Debug, Clone, Serialize)]
#[non_exhaustive]
pub struct CapabilitySelection {
    capability: String,
    executor: String,
    execution_path: Option<String>,
    quality: String,
    reliability: String,
    determinism: String,
    base_risk: String,
    cost: u64,
    fallbacks: Vec<String>,
}

impl CapabilitySelection {
    #[must_use]
    pub fn capability(&self) -> &str {
        &self.capability
    }

    #[must_use]
    pub fn executor(&self) -> &str {
        &self.executor
    }

    #[must_use]
    pub fn execution_path(&self) -> Option<&str> {
        self.execution_path.as_deref()
    }

    #[must_use]
    pub fn quality(&self) -> &str {
        &self.quality
    }

    #[must_use]
    pub fn reliability(&self) -> &str {
        &self.reliability
    }

    #[must_use]
    pub fn determinism(&self) -> &str {
        &self.determinism
    }

    #[must_use]
    pub fn base_risk(&self) -> &str {
        &self.base_risk
    }

    #[must_use]
    pub const fn cost(&self) -> u64 {
        self.cost
    }

    #[must_use]
    pub fn fallbacks(&self) -> &[String] {
        &self.fallbacks
    }
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
        validate_manifest_and_lock(&manifest, &lock)?;

        let requirements_path = repo_root.join("config/capability-requirements.yaml");
        if requirements_path.is_file() {
            let requirements = load_requirements(repo_root)?;
            validate_requirements_against_registry(&manifest, &lock, &requirements)?;
        }

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
        let spec = selected_spec(&self.manifest, capability, locked_executor)?;
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
            execution_path: spec.execution_path.clone(),
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
    let config = load_requirements(repo_root)?;
    config
        .requirements
        .iter()
        .find(|item| item.capability == capability)
        .map(|item| item.required_quality.clone())
        .ok_or_else(|| {
            PlatformError::Validation(format!(
                "no project requirement for capability {capability}"
            ))
        })
}

fn validate_manifest_and_lock(
    manifest: &ToolManifest,
    lock: &ToolLock,
) -> Result<(), PlatformError> {
    require_contract("tool manifest", &manifest.contract_version, TOOLS_CONTRACT)?;
    require_contract("tool lock", &lock.contract_version, TOOL_LOCK_CONTRACT)?;

    let mut identities = HashSet::new();
    for spec in &manifest.capabilities {
        require_nonempty("capability", &spec.capability)?;
        require_nonempty("executor", &spec.executor)?;
        quality_rank(&spec.quality)?;
        validate_rank_label("reliability", &spec.reliability, &["low", "standard", "high"])?;
        validate_rank_label(
            "determinism",
            &spec.determinism,
            &["low", "standard", "high"],
        )?;
        validate_rank_label(
            "base risk",
            &spec.base_risk,
            &["low", "medium", "high", "critical"],
        )?;
        if let Some(path) = &spec.execution_path {
            require_nonempty("execution path", path)?;
        }
        if let Some(constraints) = &spec.artifact_constraints {
            for data_class in &constraints.allowed_data_classes {
                validate_rank_label(
                    "artifact data class",
                    data_class,
                    &["public", "project", "private", "sensitive"],
                )?;
            }
            let _ = constraints.requires_registered_artifact_for_reuse;
        }
        if let Some(skill) = &spec.required_skill {
            require_nonempty("required skill", skill)?;
        }
        for qc in &spec.required_qc {
            require_nonempty("required QC evidence", qc)?;
        }
        if let Some(health) = &spec.health {
            require_nonempty("health runtime capability", &health.runtime_capability)?;
            require_nonempty("health required status", &health.required_status)?;
        }
        let identity = (spec.capability.clone(), spec.executor.clone());
        if !identities.insert(identity) {
            return Err(PlatformError::Validation(format!(
                "duplicate tool manifest entry for capability {} executor {}",
                spec.capability, spec.executor
            )));
        }
    }

    for (capability, executor) in &lock.selected {
        require_nonempty("locked capability", capability)?;
        require_nonempty("locked executor", executor)?;
        selected_spec(manifest, capability, executor)?;
    }
    Ok(())
}

fn validate_requirements_against_registry(
    manifest: &ToolManifest,
    lock: &ToolLock,
    requirements: &CapabilityRequirements,
) -> Result<(), PlatformError> {
    let mut capabilities = HashSet::new();
    for requirement in &requirements.requirements {
        require_nonempty("required capability", &requirement.capability)?;
        quality_rank(&requirement.required_quality)?;
        if requirement.execution_paths.is_empty() {
            return Err(PlatformError::Validation(format!(
                "capability requirement {} has no execution paths",
                requirement.capability
            )));
        }
        for path in &requirement.execution_paths {
            require_nonempty("required execution path", path)?;
        }
        for fallback in &requirement.fallbacks {
            require_nonempty("requirement fallback", fallback)?;
        }
        for acceptance in &requirement.acceptance {
            require_nonempty("acceptance evidence", acceptance)?;
        }
        if !capabilities.insert(requirement.capability.clone()) {
            return Err(PlatformError::Validation(format!(
                "duplicate capability requirement: {}",
                requirement.capability
            )));
        }

        let Some(locked_executor) = lock.selected.get(&requirement.capability) else {
            if requirement.required {
                return Err(PlatformError::Validation(format!(
                    "required capability {} has no locked executor",
                    requirement.capability
                )));
            }
            continue;
        };
        let spec = selected_spec(manifest, &requirement.capability, locked_executor)?;
        let execution_path = spec.execution_path.as_deref().ok_or_else(|| {
            PlatformError::Validation(format!(
                "selected capability {} has no explicit execution_path",
                requirement.capability
            ))
        })?;
        if !requirement
            .execution_paths
            .iter()
            .any(|allowed| allowed == execution_path)
        {
            return Err(PlatformError::Validation(format!(
                "selected capability {} execution path {execution_path} is not allowed by project requirements",
                requirement.capability
            )));
        }
    }
    Ok(())
}

fn load_requirements(repo_root: &Path) -> Result<CapabilityRequirements, PlatformError> {
    let config: CapabilityRequirements = serde_json::from_value(load_json_yaml(
        &repo_root.join("config/capability-requirements.yaml"),
    )?)
    .map_err(|error| {
        PlatformError::Validation(format!("invalid capability requirements: {error}"))
    })?;
    require_contract(
        "capability requirements",
        &config.contract_version,
        REQUIREMENTS_CONTRACT,
    )?;
    Ok(config)
}

fn selected_spec<'a>(
    manifest: &'a ToolManifest,
    capability: &str,
    executor: &str,
) -> Result<&'a CapabilitySpec, PlatformError> {
    manifest
        .capabilities
        .iter()
        .find(|item| item.capability == capability && item.executor == executor)
        .ok_or_else(|| {
            PlatformError::Validation(format!(
                "locked executor {executor} is absent from manifest for {capability}"
            ))
        })
}

fn require_contract(label: &str, actual: &str, expected: &str) -> Result<(), PlatformError> {
    if actual == expected {
        Ok(())
    } else {
        Err(PlatformError::Validation(format!(
            "unsupported {label} contract {actual}; expected {expected}"
        )))
    }
}

fn require_nonempty(label: &str, value: &str) -> Result<(), PlatformError> {
    if value.trim().is_empty() {
        Err(PlatformError::Validation(format!(
            "{label} must not be empty"
        )))
    } else {
        Ok(())
    }
}

fn validate_rank_label(label: &str, value: &str, allowed: &[&str]) -> Result<(), PlatformError> {
    if allowed.contains(&value) {
        Ok(())
    } else {
        Err(PlatformError::Validation(format!(
            "unknown {label}: {value}"
        )))
    }
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
