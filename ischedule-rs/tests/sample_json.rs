use ischedule_rs::{config::Config, generator::generate_calendar, schedule::parse_schedule_json};

#[test]
fn loads_existing_repository_sample_json() {
    let config: Config = serde_json::from_str(include_str!("../../config.json")).unwrap();
    let terms = parse_schedule_json(include_str!("../../schedule.json")).unwrap();

    assert_eq!(config.name, "BCA25");
    assert_eq!(terms.len(), 1);

    let calendar = generate_calendar(&terms[0], &config).unwrap();
    assert!(calendar.contains("X-WR-CALNAME:BCA25 - Term 2"));
    assert!(calendar.contains("SUMMARY:Calculus 12"));
    assert!(calendar.contains("DESCRIPTION:Charles Zhang\\nA205"));
}
