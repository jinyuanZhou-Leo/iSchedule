use thiserror::Error;

pub type Result<T> = std::result::Result<T, IScheduleError>;

#[derive(Debug, Error)]
pub enum IScheduleError {
    #[error("invalid date: {0:?}")]
    InvalidDate([i32; 3]),
    #[error("invalid time: {0:?}")]
    InvalidTime([u32; 2]),
    #[error("invalid cycle {0}; cycle must be positive")]
    InvalidCycle(u32),
    #[error("invalid schedule index: {0}")]
    InvalidIndex(String),
    #[error("unsupported holiday type: {0}")]
    UnsupportedHoliday(String),
    #[error("failed to read {path}: {source}")]
    ReadFile {
        path: String,
        source: std::io::Error,
    },
    #[error("failed to write {path}: {source}")]
    WriteFile {
        path: String,
        source: std::io::Error,
    },
    #[error("failed to parse JSON from {path}: {source}")]
    ParseJson {
        path: String,
        source: serde_json::Error,
    },
}
