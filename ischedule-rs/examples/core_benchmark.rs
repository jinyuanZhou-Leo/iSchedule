use std::{env, fs, process, time::Instant};

use ischedule_rs::{config::Config, generator::generate_calendar, schedule::parse_schedule_json};

fn main() {
    if let Err(error) = run() {
        eprintln!("{error}");
        process::exit(1);
    }
}

fn run() -> Result<(), Box<dyn std::error::Error>> {
    let args = Args::parse()?;
    let config_content = fs::read_to_string(&args.config_path)?;
    let schedule_content = fs::read_to_string(&args.schedule_path)?;
    let config: Config = serde_json::from_str(&config_content)?;
    let terms = parse_schedule_json(&schedule_content)?;

    for _ in 0..args.warmup {
        for term in &terms {
            std::hint::black_box(generate_calendar(term, &config)?);
        }
    }

    let start = Instant::now();
    let mut bytes = 0usize;
    for _ in 0..args.iterations {
        for term in &terms {
            let calendar = generate_calendar(term, &config)?;
            bytes += std::hint::black_box(calendar.len());
        }
    }
    let elapsed = start.elapsed();
    let calls = args.iterations * terms.len();
    let mean = elapsed.as_secs_f64() / calls as f64;

    println!("iterations={}", args.iterations);
    println!("terms={}", terms.len());
    println!("calls={calls}");
    println!("bytes={bytes}");
    println!("elapsed_ms={:.3}", elapsed.as_secs_f64() * 1000.0);
    println!("mean_us={:.3}", mean * 1_000_000.0);

    Ok(())
}

struct Args {
    config_path: String,
    schedule_path: String,
    iterations: usize,
    warmup: usize,
}

impl Args {
    fn parse() -> Result<Self, String> {
        let mut config_path = "../config.json".to_string();
        let mut schedule_path = "../schedule.json".to_string();
        let mut iterations = 10_000usize;
        let mut warmup = 100usize;

        let mut args = env::args().skip(1);
        while let Some(arg) = args.next() {
            match arg.as_str() {
                "--config" => {
                    config_path = args
                        .next()
                        .ok_or_else(|| "--config requires a path".to_string())?;
                }
                "--schedule" => {
                    schedule_path = args
                        .next()
                        .ok_or_else(|| "--schedule requires a path".to_string())?;
                }
                "-n" | "--iterations" => {
                    iterations = parse_positive_usize(&arg, args.next())?;
                }
                "-w" | "--warmup" => {
                    warmup = parse_usize(&arg, args.next())?;
                }
                "-h" | "--help" => {
                    print_help();
                    process::exit(0);
                }
                _ => return Err(format!("unknown argument: {arg}")),
            }
        }

        Ok(Self {
            config_path,
            schedule_path,
            iterations,
            warmup,
        })
    }
}

fn parse_positive_usize(flag: &str, value: Option<String>) -> Result<usize, String> {
    let value = parse_usize(flag, value)?;
    if value == 0 {
        Err(format!("{flag} must be positive"))
    } else {
        Ok(value)
    }
}

fn parse_usize(flag: &str, value: Option<String>) -> Result<usize, String> {
    value
        .ok_or_else(|| format!("{flag} requires a value"))?
        .parse()
        .map_err(|_| format!("{flag} must be an integer"))
}

fn print_help() {
    println!(
        "Usage: cargo run --release --example core_benchmark -- [--config PATH] [--schedule PATH] [-n ITERATIONS] [-w WARMUP]"
    );
}
