use serde::{Deserialize, Serialize};
use serde_json::Value;

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct RelayTask {
    pub contract_version: String,
    pub request_id: String,
    pub operation: String,
    pub parameters: Value,
    pub deadline_unix_ms: i64,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct RelayResponse {
    pub contract_version: String,
    pub request_id: String,
    pub status: String,
    pub result: Value,
    pub error: Value,
}

#[derive(Debug, Clone)]
pub struct StoredTask {
    pub task: RelayTask,
    pub project_id: String,
    pub created_unix_ms: i64,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct AgentStatus {
    pub last_seen_unix_ms: i64,
    pub operations: Vec<String>,
}
