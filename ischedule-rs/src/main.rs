use std::{fs, path::PathBuf, time::Instant};

use clap::Parser;
use ischedule_rs::{
    IScheduleError, Result, config::Config, generator::generate_calendar, logger::Logger,
    schedule::parse_schedule_json,
};

const VERSION: &str = env!("CARGO_PKG_VERSION");

#[derive(Debug, Parser)]
#[command(name = "ischedule-rs", version = VERSION, about = "Generate ICS calendars from iSchedule JSON")]
struct Cli {
    #[arg(short = 'n', long = "nolog", help = "Suppress informational output")]
    nolog: bool,
    #[arg(short, long, help = "Path to config.json")]
    config: Option<PathBuf>,
    #[arg(short, long, help = "Path to schedule.json")]
    schedule: Option<PathBuf>,
    #[arg(short, long, help = "Output directory")]
    output: Option<PathBuf>,
}

fn main() {
    if let Err(error) = run() {
        Logger::new(false).error(error.to_string());
        std::process::exit(1);
    }
}

fn run() -> Result<()> {
    let cli = Cli::parse();
    let logger = Logger::new(cli.nolog);
    logger.info(format!("iSchedule {VERSION}"));

    let cwd = std::env::current_dir().map_err(|source| IScheduleError::ReadFile {
        path: ".".to_string(),
        source,
    })?;

    let config_path = cli.config.unwrap_or_else(|| cwd.join("config.json"));
    let schedule_path = cli.schedule.unwrap_or_else(|| cwd.join("schedule.json"));
    let output_path = cli.output.unwrap_or(cwd);
    logger.info(format!("Using config file: {}", config_path.display()));
    logger.info(format!("Using schedule file: {}", schedule_path.display()));
    logger.info(format!("Using output directory: {}", output_path.display()));

    let config_content = read_to_string(&config_path)?;
    logger.success(format!("{} is successfully parsed", config_path.display()));
    let schedule_content = read_to_string(&schedule_path)?;
    logger.success(format!(
        "{} is successfully parsed",
        schedule_path.display()
    ));
    let mut config: Config =
        serde_json::from_str(&config_content).map_err(|source| IScheduleError::ParseJson {
            path: config_path.display().to_string(),
            source,
        })?;
    if config.name.is_empty() {
        config.name = format!(
            "Schedule-{}",
            chrono::Local::now().format("%H:%M:%S-%Y.%m.%d")
        );
    }
    if config.reduce_file_size {
        logger.warning("Tips - Reduce file size mode is enabled, some features may not supported");
    }

    let terms =
        parse_schedule_json(&schedule_content).map_err(|source| IScheduleError::ParseJson {
            path: schedule_path.display().to_string(),
            source,
        })?;

    fs::create_dir_all(&output_path).map_err(|source| IScheduleError::WriteFile {
        path: output_path.display().to_string(),
        source,
    })?;

    for (index, term) in terms.iter().enumerate() {
        let timer = Instant::now();
        let calendar = match generate_calendar(term, &config) {
            Ok(calendar) => calendar,
            Err(error) => {
                logger.error(format!(
                    "[{} of {}] Failed to generate ICS file - {} - {}.ics: {}",
                    index + 1,
                    terms.len(),
                    config.name,
                    term.name,
                    error
                ));
                return Err(error);
            }
        };
        logger.info(format!(
            "'generate_calendar' called, Time consumed {:.6}s",
            timer.elapsed().as_secs_f64()
        ));
        let file_path = output_path.join(format!("{} - {}.ics", config.name, term.name));
        fs::write(&file_path, calendar).map_err(|source| IScheduleError::WriteFile {
            path: file_path.display().to_string(),
            source,
        })?;
        logger.success(format!(
            "[{} of {}] Successfully generated ICS file - {} - {}.ics",
            index + 1,
            terms.len(),
            config.name,
            term.name
        ));
    }

    logger.info("To import the ICS file, drag the generated ICS file into your calendar app");
    Ok(())
}

fn read_to_string(path: &PathBuf) -> Result<String> {
    fs::read_to_string(path).map_err(|source| IScheduleError::ReadFile {
        path: path.display().to_string(),
        source,
    })
}
