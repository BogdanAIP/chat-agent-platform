use std::collections::HashSet;
use std::fs;
use std::path::Path;
use std::sync::atomic::{AtomicI64, Ordering};
use std::sync::{Arc, Mutex, MutexGuard};
use std::time::Duration;

use rusqlite::{Connection, OptionalExtension, TransactionBehavior, params};
use serde_json::Value;
use thiserror::Error;

use crate::model::{AgentStatus, RelayResponse, RelayTask, StoredTask};

const RETENTION_MS: i64 = 24 * 60 * 60 * 1_000;
const CLEANUP_INTERVAL_MS: i64 = 60 * 60 * 1_000;

#[derive(Debug, Error)]
pub enum StoreError {
    #[error("relay state database error: {0}")]
    Sqlite(#[from] rusqlite::Error),
    #[error("relay state filesystem error: {0}")]
    Io(#[from] std::io::Error),
    #[error("relay state JSON error: {0}")]
    Json(#[from] serde_json::Error),
    #[error("relay state database lock is poisoned")]
    LockPoisoned,
    #[error("task does not exist")]
    TaskMissing,
    #[error("task deadline has expired")]
    TaskExpired,
    #[error("stored result differs from the previously accepted result")]
    ResultCollision,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum SaveResultOutcome {
    Stored,
    Duplicate,
}

#[derive(Debug, Clone)]
pub struct Store {
    connection: Arc<Mutex<Connection>>,
    last_cleanup_unix_ms: Arc<AtomicI64>,
}

impl Store {
    pub fn open(path: &Path) -> Result<Self, StoreError> {
        if let Some(parent) = path
            .parent()
            .filter(|parent| !parent.as_os_str().is_empty())
        {
            fs::create_dir_all(parent)?;
        }
        let connection = Connection::open(path)?;
        Self::initialize_connection(&connection)?;
        Ok(Self {
            connection: Arc::new(Mutex::new(connection)),
            last_cleanup_unix_ms: Arc::new(AtomicI64::new(0)),
        })
    }

    #[cfg(test)]
    pub fn open_in_memory() -> Result<Self, StoreError> {
        let connection = Connection::open_in_memory()?;
        Self::initialize_connection(&connection)?;
        Ok(Self {
            connection: Arc::new(Mutex::new(connection)),
            last_cleanup_unix_ms: Arc::new(AtomicI64::new(0)),
        })
    }

    fn initialize_connection(connection: &Connection) -> Result<(), StoreError> {
        connection.busy_timeout(Duration::from_secs(5))?;
        connection.execute_batch(
            "PRAGMA journal_mode=WAL;
             PRAGMA synchronous=NORMAL;
             PRAGMA foreign_keys=ON;
             CREATE TABLE IF NOT EXISTS tasks (
                 request_id TEXT PRIMARY KEY,
                 project_id TEXT NOT NULL,
                 operation TEXT NOT NULL,
                 parameters_json TEXT NOT NULL,
                 deadline_unix_ms INTEGER NOT NULL,
                 created_unix_ms INTEGER NOT NULL,
                 lease_until_unix_ms INTEGER NOT NULL DEFAULT 0
             );
             CREATE INDEX IF NOT EXISTS idx_tasks_pending
                 ON tasks(project_id, deadline_unix_ms, lease_until_unix_ms, created_unix_ms);
             CREATE TABLE IF NOT EXISTS results (
                 request_id TEXT PRIMARY KEY,
                 response_json TEXT NOT NULL,
                 created_unix_ms INTEGER NOT NULL,
                 FOREIGN KEY(request_id) REFERENCES tasks(request_id) ON DELETE CASCADE
             );
             CREATE TABLE IF NOT EXISTS agents (
                 project_id TEXT PRIMARY KEY,
                 last_seen_unix_ms INTEGER NOT NULL,
                 operations_json TEXT NOT NULL
             );",
        )?;
        Ok(())
    }

    fn connection(&self) -> Result<MutexGuard<'_, Connection>, StoreError> {
        self.connection.lock().map_err(|_| StoreError::LockPoisoned)
    }

    pub fn cleanup(&self, older_than_unix_ms: i64) -> Result<(), StoreError> {
        let connection = self.connection()?;
        connection.execute(
            "DELETE FROM tasks WHERE deadline_unix_ms < ?1",
            params![older_than_unix_ms],
        )?;
        connection.execute(
            "DELETE FROM agents WHERE last_seen_unix_ms > 0 AND last_seen_unix_ms < ?1",
            params![older_than_unix_ms],
        )?;
        Ok(())
    }

    fn maybe_cleanup(&self, now_unix_ms: i64) -> Result<(), StoreError> {
        let previous = self.last_cleanup_unix_ms.load(Ordering::Acquire);
        if previous > 0 && now_unix_ms.saturating_sub(previous) < CLEANUP_INTERVAL_MS {
            return Ok(());
        }
        if self
            .last_cleanup_unix_ms
            .compare_exchange(previous, now_unix_ms, Ordering::AcqRel, Ordering::Acquire)
            .is_err()
        {
            return Ok(());
        }
        if let Err(error) = self.cleanup(now_unix_ms.saturating_sub(RETENTION_MS)) {
            self.last_cleanup_unix_ms.store(previous, Ordering::Release);
            return Err(error);
        }
        Ok(())
    }

    pub fn upsert_heartbeat(
        &self,
        project_id: &str,
        operations: &[String],
        now_unix_ms: i64,
    ) -> Result<(), StoreError> {
        let operations_json = serde_json::to_string(operations)?;
        let connection = self.connection()?;
        connection.execute(
            "INSERT INTO agents(project_id, last_seen_unix_ms, operations_json)
             VALUES (?1, ?2, ?3)
             ON CONFLICT(project_id) DO UPDATE SET
                 last_seen_unix_ms=excluded.last_seen_unix_ms,
                 operations_json=excluded.operations_json",
            params![project_id, now_unix_ms, operations_json],
        )?;
        Ok(())
    }

    pub fn mark_offline(&self, project_id: &str) -> Result<(), StoreError> {
        let connection = self.connection()?;
        connection.execute(
            "INSERT INTO agents(project_id, last_seen_unix_ms, operations_json)
             VALUES (?1, 0, '[]')
             ON CONFLICT(project_id) DO UPDATE SET
                 last_seen_unix_ms=0,
                 operations_json='[]'",
            params![project_id],
        )?;
        Ok(())
    }

    pub fn agent_status(&self, project_id: &str) -> Result<Option<AgentStatus>, StoreError> {
        let connection = self.connection()?;
        let row = connection
            .query_row(
                "SELECT last_seen_unix_ms, operations_json FROM agents WHERE project_id=?1",
                params![project_id],
                |row| Ok((row.get::<_, i64>(0)?, row.get::<_, String>(1)?)),
            )
            .optional()?;
        drop(connection);
        let Some((last_seen_unix_ms, operations_json)) = row else {
            return Ok(None);
        };
        let operations = serde_json::from_str(&operations_json)?;
        Ok(Some(AgentStatus {
            last_seen_unix_ms,
            operations,
        }))
    }

    pub fn insert_task(&self, task: &StoredTask) -> Result<(), StoreError> {
        self.maybe_cleanup(task.created_unix_ms)?;
        let parameters_json = serde_json::to_string(&task.task.parameters)?;
        let connection = self.connection()?;
        connection.execute(
            "INSERT INTO tasks(
                 request_id, project_id, operation, parameters_json,
                 deadline_unix_ms, created_unix_ms, lease_until_unix_ms
             ) VALUES (?1, ?2, ?3, ?4, ?5, ?6, 0)",
            params![
                task.task.request_id,
                task.project_id,
                task.task.operation,
                parameters_json,
                task.task.deadline_unix_ms,
                task.created_unix_ms
            ],
        )?;
        Ok(())
    }

    pub fn lease_next_task(
        &self,
        project_id: &str,
        operations: &[String],
        now_unix_ms: i64,
        lease_until_unix_ms: i64,
    ) -> Result<Option<RelayTask>, StoreError> {
        let allowed: HashSet<&str> = operations.iter().map(String::as_str).collect();
        let mut connection = self.connection()?;
        let transaction = connection.transaction_with_behavior(TransactionBehavior::Immediate)?;
        let mut statement = transaction.prepare(
            "SELECT request_id, operation, parameters_json, deadline_unix_ms
             FROM tasks
             WHERE project_id=?1
               AND deadline_unix_ms >= ?2
               AND lease_until_unix_ms <= ?2
               AND NOT EXISTS(
                   SELECT 1 FROM results WHERE results.request_id=tasks.request_id
               )
             ORDER BY created_unix_ms, request_id
             LIMIT 32",
        )?;
        let rows = statement.query_map(params![project_id, now_unix_ms], |row| {
            Ok((
                row.get::<_, String>(0)?,
                row.get::<_, String>(1)?,
                row.get::<_, String>(2)?,
                row.get::<_, i64>(3)?,
            ))
        })?;
        let candidates = rows.collect::<Result<Vec<_>, _>>()?;
        drop(statement);

        for (request_id, operation, parameters_json, deadline_unix_ms) in candidates {
            if !allowed.contains(operation.as_str()) {
                continue;
            }
            let updated = transaction.execute(
                "UPDATE tasks
                 SET lease_until_unix_ms=?1
                 WHERE request_id=?2
                   AND lease_until_unix_ms <= ?3
                   AND deadline_unix_ms >= ?3
                   AND NOT EXISTS(
                       SELECT 1 FROM results WHERE results.request_id=tasks.request_id
                   )",
                params![lease_until_unix_ms, request_id, now_unix_ms],
            )?;
            if updated == 1 {
                let parameters: Value = serde_json::from_str(&parameters_json)?;
                transaction.commit()?;
                return Ok(Some(RelayTask {
                    contract_version: "relay-request-v1".to_owned(),
                    request_id,
                    operation,
                    parameters,
                    deadline_unix_ms,
                }));
            }
        }

        transaction.commit()?;
        Ok(None)
    }

    pub fn read_result(&self, request_id: &str) -> Result<Option<RelayResponse>, StoreError> {
        let connection = self.connection()?;
        let response_json = connection
            .query_row(
                "SELECT response_json FROM results WHERE request_id=?1",
                params![request_id],
                |row| row.get::<_, String>(0),
            )
            .optional()?;
        drop(connection);
        response_json
            .map(|value| serde_json::from_str(&value).map_err(StoreError::from))
            .transpose()
    }

    pub fn save_result(
        &self,
        request_id: &str,
        response: &RelayResponse,
        now_unix_ms: i64,
    ) -> Result<SaveResultOutcome, StoreError> {
        let response_json = serde_json::to_string(response)?;
        let mut connection = self.connection()?;
        let transaction = connection.transaction_with_behavior(TransactionBehavior::Immediate)?;
        let existing = transaction
            .query_row(
                "SELECT response_json FROM results WHERE request_id=?1",
                params![request_id],
                |row| row.get::<_, String>(0),
            )
            .optional()?;
        if let Some(existing_json) = existing {
            let existing_response: RelayResponse = serde_json::from_str(&existing_json)?;
            if existing_response == *response {
                transaction.commit()?;
                return Ok(SaveResultOutcome::Duplicate);
            }
            return Err(StoreError::ResultCollision);
        }

        let deadline = transaction
            .query_row(
                "SELECT deadline_unix_ms FROM tasks WHERE request_id=?1",
                params![request_id],
                |row| row.get::<_, i64>(0),
            )
            .optional()?;
        let Some(deadline_unix_ms) = deadline else {
            return Err(StoreError::TaskMissing);
        };
        if deadline_unix_ms < now_unix_ms {
            return Err(StoreError::TaskExpired);
        }
        transaction.execute(
            "INSERT INTO results(request_id, response_json, created_unix_ms)
             VALUES (?1, ?2, ?3)",
            params![request_id, response_json, now_unix_ms],
        )?;
        transaction.commit()?;
        Ok(SaveResultOutcome::Stored)
    }
}

#[cfg(test)]
mod tests {
    use serde_json::json;

    use super::*;

    fn task_at(id: &str, created: i64, deadline: i64) -> StoredTask {
        StoredTask {
            task: RelayTask {
                contract_version: "relay-request-v1".to_owned(),
                request_id: id.to_owned(),
                operation: "local_ping".to_owned(),
                parameters: json!({"message": "hello"}),
                deadline_unix_ms: deadline,
            },
            project_id: "project".to_owned(),
            created_unix_ms: created,
        }
    }

    fn task(id: &str, deadline: i64) -> StoredTask {
        task_at(id, 10, deadline)
    }

    #[test]
    fn heartbeat_round_trip_and_offline_state() {
        let store = Store::open_in_memory().expect("store");
        store
            .upsert_heartbeat("project", &["local_ping".to_owned()], 123)
            .expect("heartbeat");
        assert_eq!(
            store.agent_status("project").expect("status"),
            Some(AgentStatus {
                last_seen_unix_ms: 123,
                operations: vec!["local_ping".to_owned()]
            })
        );
        store.mark_offline("project").expect("offline");
        assert_eq!(
            store
                .agent_status("project")
                .expect("status")
                .expect("agent")
                .last_seen_unix_ms,
            0
        );
    }

    #[test]
    fn task_is_leased_once_until_lease_expires() {
        let store = Store::open_in_memory().expect("store");
        store
            .insert_task(&task("rly_0123456789abcdef0123456789abcdef", 1_000))
            .expect("insert");
        let operations = vec!["local_ping".to_owned()];
        let first = store
            .lease_next_task("project", &operations, 100, 500)
            .expect("lease");
        assert!(first.is_some());
        let second = store
            .lease_next_task("project", &operations, 200, 600)
            .expect("lease");
        assert!(second.is_none());
        let retry = store
            .lease_next_task("project", &operations, 501, 800)
            .expect("lease");
        assert!(retry.is_some());
    }

    #[test]
    fn duplicate_result_is_idempotent_but_collision_is_rejected() {
        let store = Store::open_in_memory().expect("store");
        let request_id = "rly_0123456789abcdef0123456789abcdef";
        store.insert_task(&task(request_id, 1_000)).expect("insert");
        let response = RelayResponse {
            contract_version: "relay-response-v1".to_owned(),
            request_id: request_id.to_owned(),
            status: "success".to_owned(),
            result: json!({"pong": true}),
            error: Value::Null,
        };
        assert_eq!(
            store.save_result(request_id, &response, 100).expect("save"),
            SaveResultOutcome::Stored
        );
        assert_eq!(
            store.save_result(request_id, &response, 101).expect("save"),
            SaveResultOutcome::Duplicate
        );
        let mut changed = response;
        changed.result = json!({"pong": false});
        assert!(matches!(
            store.save_result(request_id, &changed, 102),
            Err(StoreError::ResultCollision)
        ));
    }

    #[test]
    fn active_task_insertion_prunes_state_older_than_retention_window() {
        let store = Store::open_in_memory().expect("store");
        let old_request_id = "rly_aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa";
        store
            .insert_task(&task_at(old_request_id, 10, 1_000))
            .expect("old task");
        let response = RelayResponse {
            contract_version: "relay-response-v1".to_owned(),
            request_id: old_request_id.to_owned(),
            status: "success".to_owned(),
            result: json!({"pong": true}),
            error: Value::Null,
        };
        store
            .save_result(old_request_id, &response, 100)
            .expect("old result");
        store
            .upsert_heartbeat("stale-project", &["local_ping".to_owned()], 10)
            .expect("stale heartbeat");

        let now = RETENTION_MS + CLEANUP_INTERVAL_MS + 2_000;
        let new_request_id = "rly_bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb";
        store
            .insert_task(&task_at(new_request_id, now, now + 60_000))
            .expect("new task");

        assert!(
            store
                .read_result(old_request_id)
                .expect("old result lookup")
                .is_none()
        );
        assert!(
            store
                .agent_status("stale-project")
                .expect("stale status")
                .is_none()
        );
        assert!(
            store
                .lease_next_task("project", &["local_ping".to_owned()], now, now + 1_000,)
                .expect("new task lease")
                .is_some()
        );
    }
}
