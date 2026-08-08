use std::collections::{HashMap, HashSet};
use std::path::Path;

use serde::{Deserialize, Serialize};

use crate::config::load_json_yaml;
use crate::error::PlatformError;

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
struct RequirementManifest {
    contract_version: String,
    requirements: Vec<CapabilityRequirement>,
}

#[derive(Debug, Clone, Deserialize)]
#[serde(deny_unknown_fields)]
struct CapabilitySpec {
    capability: String,
    executor: String,
    execution_path: String,
    enabled: bool,
    quality: String,
    reliability: String,
    determinism: String,
    base_risk: String,
    cost: u64,
    #[serde(default)]
    fallbacks: Vec<String>,
    #[serde(default)]
    evidence: CapabilityEvidence,
}

#[derive(Debug, Clone, Default, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub struct CapabilityEvidence {
    #[serde(default)]
    required_skill: Option<String>,
    #[serde(default)]
    qc: Vec<String>,
    #[serde(default)]
    health: Option<HealthEvidence>,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub struct HealthEvidence {
    runtime_capability: String,
    required_status: String,
}

#[derive(Debug, Clone, Deserialize)]
#[serde(deny_unknown_fields)]
struct CapabilityRequirement {
    capability: String,
    required: bool,
    required_quality: String,
    required_reliability: String,
    required_determinism: String,
    execution_paths: Vec<String>,
    #[serde(default)]
    fallbacks: Vec<String>,
    #[serde(default)]
    acceptance_evidence: Vec<String>,
}

#[derive(Debug, Clone, Serialize)]
#[non_exhaustive]
pub struct CapabilitySelection {
    capability: String,
    executor: String,
    execution_path: String,
    quality: String,
    reliability: String,
    determinism: String,
    base_risk: String,
    cost: u64,
    fallbacks: Vec<String>,
    evidence: CapabilityEvidence,
    required: bool,
    acceptance_evidence: Vec<String>,
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
    pub fn execution_path(&self) -> &str {
        &self.execution_path
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

    #[must_use]
    pub const fn required(&self) -> bool {
        self.required
    }

    #[must_use]
    pub const fn evidence(&self) -> &CapabilityEvidence {
        &self.evidence
    }

    #[must_use]
    pub fn acceptance_evidence(&self) -> &[String] {
        &self.acceptance_evidence
    }
}

pub struct CapabilityRegistry {
    manifest: ToolManifest,
    lock: ToolLock,
    requirements: RequirementManifest,
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
        let requirements: RequirementManifest = serde_json::from_value(load_json_yaml(
            &repo_root.join("config/capability-requirements.yaml"),
        )?)
        .map_err(|error| {
            PlatformError::Validation(format!("invalid capability requirements: {error}"))
        })?;
        let registry = Self {
            manifest,
            lock,
            requirements,
        };
        registry.validate()?;
        Ok(registry)
    }

    pub fn select(
        &self,
        capability: &str,
        required_quality: &str,
        cost_limit: u64,
    ) -> Result<CapabilitySelection, PlatformError> {
        let requirement = self.requirement(capability)?;
        if required_quality != requirement.required_quality {
            return Err(PlatformError::Validation(format!(
                "caller quality {required_quality} does not match project requirement {} for {capability}",
                requirement.required_quality
            )));
        }
        let spec = self.locked_spec(capability)?;
        self.validate_runtime_selection(capability, spec, requirement)?;
        if spec.cost > cost_limit {
            return Err(PlatformError::PolicyDenied(format!(
                "executor {} cost {} exceeds request limit {cost_limit}",
                spec.executor, spec.cost
            )));
        }
        Ok(selection(spec, requirement))
    }

    pub fn locked_selections(&self) -> Result<Vec<CapabilitySelection>, PlatformError> {
        let mut capabilities = self.lock.selected.keys().cloned().collect::<Vec<_>>();
        capabilities.sort();
        capabilities
            .into_iter()
            .map(|capability| {
                let spec = self.locked_spec(&capability)?;
                let requirement = self.requirement(&capability)?;
                self.validate_runtime_selection(&capability, spec, requirement)?;
                Ok(selection(spec, requirement))
            })
            .collect()
    }

    fn validate(&self) -> Result<(), PlatformError> {
        if self.manifest.contract_version != "tools-v1" {
            return Err(PlatformError::Validation(format!(
                "unsupported tools contract: {}",
                self.manifest.contract_version
            )));
        }
        if self.lock.contract_version != "tool-lock-v1" {
            return Err(PlatformError::Validation(format!(
                "unsupported tool-lock contract: {}",
                self.lock.contract_version
            )));
        }
        if self.requirements.contract_version != "capability-requirements-v1" {
            return Err(PlatformError::Validation(format!(
                "unsupported capability requirements contract: {}",
                self.requirements.contract_version
            )));
        }

        let mut manifest_keys = HashSet::new();
        for spec in &self.manifest.capabilities {
            validate_nonempty("capability", &spec.capability)?;
            validate_nonempty("executor", &spec.executor)?;
            validate_nonempty("execution_path", &spec.execution_path)?;
            quality_rank(&spec.quality)?;
            reliability_rank(&spec.reliability)?;
            determinism_rank(&spec.determinism)?;
            risk_rank(&spec.base_risk)?;
            if !manifest_keys.insert((spec.capability.clone(), spec.executor.clone())) {
                return Err(PlatformError::Validation(format!(
                    "duplicate manifest entry for {} / {}",
                    spec.capability, spec.executor
                )));
            }
        }

        let mut requirement_names = HashSet::new();
        for requirement in &self.requirements.requirements {
            validate_nonempty("requirement capability", &requirement.capability)?;
            quality_rank(&requirement.required_quality)?;
            reliability_rank(&requirement.required_reliability)?;
            determinism_rank(&requirement.required_determinism)?;
            if requirement.execution_paths.is_empty() {
                return Err(PlatformError::Validation(format!(
                    "capability requirement {} has no execution paths",
                    requirement.capability
                )));
            }
            if !requirement_names.insert(requirement.capability.clone()) {
                return Err(PlatformError::Validation(format!(
                    "duplicate capability requirement: {}",
                    requirement.capability
                )));
            }
            if requirement.required && !self.lock.selected.contains_key(&requirement.capability) {
                return Err(PlatformError::Validation(format!(
                    "required capability {} has no locked executor",
                    requirement.capability
                )));
            }
        }

        for (capability, executor) in &self.lock.selected {
            let requirement = self.requirement(capability).map_err(|_| {
                PlatformError::Validation(format!(
                    "locked capability {capability} has no project requirement"
                ))
            })?;
            if !manifest_keys.contains(&(capability.clone(), executor.clone())) {
                return Err(PlatformError::Validation(format!(
                    "locked executor {executor} is absent from manifest for {capability}"
                )));
            }
            let spec = self.locked_spec(capability)?;
            self.validate_runtime_selection(capability, spec, requirement)?;
        }
        Ok(())
    }

    fn validate_runtime_selection(
        &self,
        capability: &str,
        spec: &CapabilitySpec,
        requirement: &CapabilityRequirement,
    ) -> Result<(), PlatformError> {
        if !spec.enabled {
            return Err(PlatformError::Validation(format!(
                "locked executor {} is disabled",
                spec.executor
            )));
        }
        if quality_rank(&spec.quality)? < quality_rank(&requirement.required_quality)? {
            return Err(PlatformError::Validation(format!(
                "executor {} quality {} does not satisfy required {}",
                spec.executor, spec.quality, requirement.required_quality
            )));
        }
        if reliability_rank(&spec.reliability)? < reliability_rank(&requirement.required_reliability)?
        {
            return Err(PlatformError::Validation(format!(
                "executor {} reliability {} does not satisfy required {}",
                spec.executor, spec.reliability, requirement.required_reliability
            )));
        }
        if determinism_rank(&spec.determinism)?
            < determinism_rank(&requirement.required_determinism)?
        {
            return Err(PlatformError::Validation(format!(
                "executor {} determinism {} does not satisfy required {}",
                spec.executor, spec.determinism, requirement.required_determinism
            )));
        }
        if !requirement
            .execution_paths
            .iter()
            .any(|path| path == &spec.execution_path)
        {
            return Err(PlatformError::Validation(format!(
                "locked executor {} uses execution path {}, which is not allowed for {capability}",
                spec.executor, spec.execution_path
            )));
        }
        if spec.fallbacks != requirement.fallbacks {
            return Err(PlatformError::Validation(format!(
                "manifest/requirement fallback mismatch for {capability}"
            )));
        }
        Ok(())
    }

    fn requirement(&self, capability: &str) -> Result<&CapabilityRequirement, PlatformError> {
        self.requirements
            .requirements
            .iter()
            .find(|item| item.capability == capability)
            .ok_or_else(|| {
                PlatformError::Validation(format!(
                    "no project requirement for capability {capability}"
                ))
            })
    }

    fn locked_spec(&self, capability: &str) -> Result<&CapabilitySpec, PlatformError> {
        let locked_executor = self.lock.selected.get(capability).ok_or_else(|| {
            PlatformError::Validation(format!("no locked executor for capability {capability}"))
        })?;
        self.manifest
            .capabilities
            .iter()
            .find(|item| item.capability == capability && item.executor == *locked_executor)
            .ok_or_else(|| {
                PlatformError::Validation(format!(
                    "locked executor {locked_executor} is absent from manifest for {capability}"
                ))
            })
    }
}

pub fn required_quality(repo_root: &Path, capability: &str) -> Result<String, PlatformError> {
    let registry = CapabilityRegistry::load(repo_root)?;
    Ok(registry.requirement(capability)?.required_quality.clone())
}

fn selection(spec: &CapabilitySpec, requirement: &CapabilityRequirement) -> CapabilitySelection {
    CapabilitySelection {
        capability: spec.capability.clone(),
        executor: spec.executor.clone(),
        execution_path: spec.execution_path.clone(),
        quality: spec.quality.clone(),
        reliability: spec.reliability.clone(),
        determinism: spec.determinism.clone(),
        base_risk: spec.base_risk.clone(),
        cost: spec.cost,
        fallbacks: spec.fallbacks.clone(),
        evidence: spec.evidence.clone(),
        required: requirement.required,
        acceptance_evidence: requirement.acceptance_evidence.clone(),
    }
}

fn validate_nonempty(label: &str, value: &str) -> Result<(), PlatformError> {
    if value.trim().is_empty() {
        Err(PlatformError::Validation(format!(
            "{label} must not be empty"
        )))
    } else {
        Ok(())
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

fn reliability_rank(value: &str) -> Result<u8, PlatformError> {
    match value {
        "low" => Ok(0),
        "standard" => Ok(1),
        "high" => Ok(2),
        other => Err(PlatformError::Validation(format!(
            "unknown reliability level: {other}"
        ))),
    }
}

fn determinism_rank(value: &str) -> Result<u8, PlatformError> {
    match value {
        "low" => Ok(0),
        "standard" => Ok(1),
        "high" => Ok(2),
        other => Err(PlatformError::Validation(format!(
            "unknown determinism level: {other}"
        ))),
    }
}

fn risk_rank(value: &str) -> Result<u8, PlatformError> {
    match value {
        "low" => Ok(0),
        "medium" => Ok(1),
        "high" => Ok(2),
        "critical" => Ok(3),
        other => Err(PlatformError::Validation(format!(
            "unknown base risk level: {other}"
        ))),
    }
}
