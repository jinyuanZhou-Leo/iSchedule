use colored::{ColoredString, Colorize};

#[derive(Debug, Clone, Copy)]
pub struct Logger {
    quiet: bool,
}

impl Logger {
    pub fn new(quiet: bool) -> Self {
        colored::control::set_override(true);
        Self { quiet }
    }

    pub fn info(&self, message: impl AsRef<str>) {
        self.write(LogLevel::Info, message);
    }

    pub fn success(&self, message: impl AsRef<str>) {
        self.write(LogLevel::Success, message);
    }

    pub fn warning(&self, message: impl AsRef<str>) {
        self.write(LogLevel::Warning, message);
    }

    pub fn error(&self, message: impl AsRef<str>) {
        eprintln!("{} {}", LogLevel::Error.format_label(), message.as_ref());
    }

    fn write(&self, level: LogLevel, message: impl AsRef<str>) {
        if !self.quiet {
            println!("{} {}", level.format_label(), message.as_ref());
        }
    }
}

#[derive(Debug, Clone, Copy)]
enum LogLevel {
    Info,
    Success,
    Warning,
    Error,
}

impl LogLevel {
    fn format_label(self) -> ColoredString {
        match self {
            LogLevel::Info => "INFO".blue().bold(),
            LogLevel::Success => "SUCCESS".green().bold(),
            LogLevel::Warning => "WARNING".yellow().bold(),
            LogLevel::Error => "ERROR".red().bold(),
        }
    }
}
