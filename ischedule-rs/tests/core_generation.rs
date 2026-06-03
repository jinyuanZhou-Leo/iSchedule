use ischedule_rs::{
    config::{AlarmConfig, Config},
    generator::generate_calendar,
    schedule::{Course, CourseIndex, Holiday, IndexSelector, Location, Term},
};
use std::collections::HashSet;

fn sample_config() -> Config {
    Config {
        name: "BCA25".to_string(),
        color: "#67e4fa".to_string(),
        alarm: AlarmConfig {
            enabled: true,
            before: [0, 7],
        },
        count_day_in_holiday: false,
        reduce_file_size: false,
    }
}

fn sample_term() -> Term {
    Term {
        name: "Term 2".to_string(),
        start: [2024, 11, 10],
        end: [2024, 11, 15],
        duration: 70,
        timetable: vec![[8, 0], [9, 15], [10, 30]],
        cycle: 2,
        courses: vec![Course {
            name: "English Studies 12".to_string(),
            teacher: "Lucy Liu".to_string(),
            index: CourseIndex::Traditional(vec![(IndexSelector::Everyday, IndexSelector::Day(2))]),
            location: Some(Location::Named("A311".to_string())),
            cycle: None,
        }],
        holidays: vec![],
    }
}

#[test]
fn generates_events_with_alarm_and_calendar_metadata() {
    let calendar = generate_calendar(&sample_term(), &sample_config()).unwrap();

    assert!(calendar.contains("BEGIN:VCALENDAR"));
    assert!(calendar.contains("X-WR-CALNAME:BCA25 - Term 2"));
    assert!(calendar.contains("X-APPLE-CALENDAR-COLOR:#67e4fa"));
    assert!(calendar.contains("SUMMARY:English Studies 12"));
    assert!(calendar.contains("DESCRIPTION:Lucy Liu\\nA311"));
    assert!(calendar.contains("DTSTART:20241111T091500"));
    assert!(calendar.contains("DTEND:20241111T102500"));
    assert!(calendar.contains("BEGIN:VALARM"));
    assert!(calendar.contains("TRIGGER:-PT7M"));
}

#[test]
fn skips_fixed_holidays_and_adds_compensation_day() {
    let mut term = sample_term();
    term.holidays = vec![Holiday {
        name: "Single Day".to_string(),
        kind: "fixed".to_string(),
        date: vec![[2024, 11, 11]],
        compensation: vec![([2024, 11, 16], 1)],
    }];

    let calendar = generate_calendar(&term, &sample_config()).unwrap();

    assert!(!calendar.contains("DTSTART:20241111T091500"));
    assert!(calendar.contains("DTSTART:20241112T091500"));
    assert!(calendar.contains("DTSTART:20241116T091500"));
}

#[test]
fn generated_uids_are_unique_across_courses() {
    let mut term = sample_term();
    term.courses.push(Course {
        name: "Physics 12".to_string(),
        teacher: "Grace Huang".to_string(),
        index: CourseIndex::Traditional(vec![(IndexSelector::Everyday, IndexSelector::Day(1))]),
        location: Some(Location::Named("B201".to_string())),
        cycle: None,
    });

    let calendar = generate_calendar(&term, &sample_config()).unwrap();
    let uids: Vec<&str> = calendar
        .lines()
        .filter_map(|line| line.strip_prefix("UID:"))
        .collect();
    let unique_uids: HashSet<&str> = uids.iter().copied().collect();

    assert!(uids.len() > 1);
    assert_eq!(uids.len(), unique_uids.len());
}
