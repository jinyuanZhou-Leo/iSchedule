use chrono::{DateTime, Datelike, Duration, NaiveDate, NaiveTime, Timelike, Utc};

use crate::{
    IScheduleError, Result,
    config::Config,
    index::decode_course_index,
    schedule::{Course, Holiday, Term},
    time::{combine, date_range, is_workday, parse_date, parse_time, rrule_day, week_info},
};

struct EventContext<'a> {
    term: &'a Term,
    course: &'a Course,
    timetable: Vec<NaiveTime>,
    dtstamp: String,
    description: String,
    alarm_trigger: Option<String>,
    uid_prefix: String,
}

struct DateRangeContext<'a> {
    start: NaiveDate,
    end: NaiveDate,
    holiday_ranges: &'a [(NaiveDate, NaiveDate)],
}

pub fn generate_calendar(term: &Term, config: &Config) -> Result<String> {
    term.validate()?;

    let mut calendar = String::with_capacity(64 * 1024);
    push_line(&mut calendar, "BEGIN:VCALENDAR");
    push_line(&mut calendar, "VERSION:2.0");
    push_line(&mut calendar, "PRODID:iScheduler by @Jinyuan");
    push_line(&mut calendar, "CALSCALE:GREGORIAN");
    push_property(
        &mut calendar,
        "X-APPLE-CALENDAR-COLOR",
        &config.normalized_color(),
    );
    push_property(
        &mut calendar,
        "X-WR-CALNAME",
        &config.calendar_name(&term.name),
    );
    push_line(&mut calendar, "X-WR-TIMEZONE:Asia/Shanghai");

    if use_date_range_strategy(term, config) {
        add_date_range_events(&mut calendar, term, config, Utc::now())?;
    } else {
        add_rrule_events(&mut calendar, term, config, Utc::now())?;
    }

    push_line(&mut calendar, "END:VCALENDAR");
    Ok(calendar)
}

fn use_date_range_strategy(term: &Term, config: &Config) -> bool {
    !term.holidays.is_empty() || !config.reduce_file_size
}

fn add_date_range_events(
    calendar: &mut String,
    term: &Term,
    config: &Config,
    timestamp: DateTime<Utc>,
) -> Result<()> {
    let start = parse_date(term.start)?;
    let end = parse_date(term.end)?;
    let holiday_ranges = holiday_ranges(&term.holidays)?;
    let range = DateRangeContext {
        start,
        end,
        holiday_ranges: &holiday_ranges,
    };

    for course in &term.courses {
        add_date_range_course_events(calendar, term, config, course, &range, timestamp)?;
    }
    Ok(())
}

fn add_rrule_events(
    calendar: &mut String,
    term: &Term,
    config: &Config,
    timestamp: DateTime<Utc>,
) -> Result<()> {
    let start = parse_date(term.start)?;
    let init_day = if is_workday(start) {
        start - Duration::days((start.weekday().number_from_monday() - 1) as i64)
    } else {
        start + Duration::days((8 - start.weekday().number_from_monday()) as i64)
    };

    for course in &term.courses {
        add_rrule_course_events(calendar, term, config, course, init_day, timestamp)?;
    }
    Ok(())
}

fn add_date_range_course_events(
    calendar: &mut String,
    term: &Term,
    config: &Config,
    course: &Course,
    range: &DateRangeContext<'_>,
    timestamp: DateTime<Utc>,
) -> Result<()> {
    let course_cycle = course.cycle.unwrap_or(term.cycle);
    let blocks_by_day = blocks_by_cycle_day(&course.index, course_cycle, term.timetable.len())?;
    let context = EventContext::new(term, config, course, timestamp)?;
    let mut cycle_counter = 0_u32;
    let mut uid_sequence = 0_u32;

    for date in date_range(range.start, range.end) {
        if !is_workday(date) {
            continue;
        }
        if cycle_counter >= course_cycle * 5 {
            cycle_counter = 0;
        }

        if !is_holiday(date, range.holiday_ranges) {
            add_events_for_cycle_day(
                calendar,
                &context,
                &blocks_by_day,
                cycle_counter + 1,
                date,
                &mut uid_sequence,
            )?;
            cycle_counter += 1;
        } else if config.count_day_in_holiday {
            cycle_counter += 1;
        }
    }

    for holiday in &term.holidays {
        add_compensation_events(
            calendar,
            &context,
            &blocks_by_day,
            holiday,
            &mut uid_sequence,
        )?;
    }

    Ok(())
}

fn add_rrule_course_events(
    calendar: &mut String,
    term: &Term,
    config: &Config,
    course: &Course,
    init_day: NaiveDate,
    timestamp: DateTime<Utc>,
) -> Result<()> {
    let course_cycle = course.cycle.unwrap_or(term.cycle);
    let timetable = decode_course_index(&course.index, course_cycle, term.timetable.len())?;
    let term_end = parse_date(term.end)?;
    let context = EventContext::new(term, config, course, timestamp)?;
    let mut uid_sequence = 0_u32;

    for (cycle_day, block) in timetable {
        let (weekday, week_offset) = week_info(cycle_day);
        let date =
            init_day + Duration::weeks(week_offset as i64) + Duration::days((weekday - 1) as i64);
        push_event(
            calendar,
            &context,
            date,
            block,
            Some(&format!(
                "FREQ=WEEKLY;INTERVAL={};BYDAY={};UNTIL={}",
                course_cycle,
                rrule_day(weekday)?,
                term_end.format("%Y%m%d")
            )),
            &mut uid_sequence,
        )?;
    }

    Ok(())
}

fn add_events_for_cycle_day(
    calendar: &mut String,
    context: &EventContext<'_>,
    blocks_by_day: &[Vec<usize>],
    cycle_day: u32,
    date: NaiveDate,
    uid_sequence: &mut u32,
) -> Result<()> {
    let Some(blocks) = blocks_by_day.get(cycle_day as usize) else {
        return Ok(());
    };

    for block in blocks {
        push_event(calendar, context, date, *block, None, uid_sequence)?;
    }

    Ok(())
}

fn add_compensation_events(
    calendar: &mut String,
    context: &EventContext<'_>,
    blocks_by_day: &[Vec<usize>],
    holiday: &Holiday,
    uid_sequence: &mut u32,
) -> Result<()> {
    for (date_value, cycle_day) in &holiday.compensation {
        let date = parse_date(*date_value)?;
        add_events_for_cycle_day(
            calendar,
            context,
            blocks_by_day,
            *cycle_day,
            date,
            uid_sequence,
        )?;
    }
    Ok(())
}

fn push_event(
    calendar: &mut String,
    context: &EventContext<'_>,
    date: NaiveDate,
    block: usize,
    rrule: Option<&str>,
    uid_sequence: &mut u32,
) -> Result<()> {
    let start_time = *context
        .timetable
        .get(block)
        .ok_or_else(|| IScheduleError::InvalidIndex(format!("block {block} is out of range")))?;
    let starts = combine(date, start_time);
    let ends = starts + Duration::minutes(context.term.duration);

    push_line(calendar, "BEGIN:VEVENT");
    push_property(calendar, "SUMMARY", &context.course.name);
    push_property(calendar, "DTSTART", &format_local_datetime(starts));
    push_property(calendar, "DTEND", &format_local_datetime(ends));
    push_property(calendar, "DTSTAMP", &context.dtstamp);
    push_uid(calendar, context, uid_sequence);
    push_property(calendar, "DESCRIPTION", &context.description);
    if let Some(rrule) = rrule {
        push_property(calendar, "RRULE", rrule);
    }

    if let Some(trigger) = &context.alarm_trigger {
        push_alarm(calendar, trigger);
    }

    push_line(calendar, "END:VEVENT");
    Ok(())
}

fn holiday_ranges(holidays: &[Holiday]) -> Result<Vec<(NaiveDate, NaiveDate)>> {
    let mut ranges = Vec::new();
    for holiday in holidays {
        if !holiday.kind.eq_ignore_ascii_case("fixed") {
            return Err(IScheduleError::UnsupportedHoliday(holiday.kind.clone()));
        }
        let start = holiday.date.first().ok_or_else(|| {
            IScheduleError::InvalidIndex(format!("holiday {} has no date", holiday.name))
        })?;
        let end = holiday.date.get(1).unwrap_or(start);
        ranges.push((parse_date(*start)?, parse_date(*end)?));
    }
    Ok(ranges)
}

fn is_holiday(date: NaiveDate, holiday_ranges: &[(NaiveDate, NaiveDate)]) -> bool {
    holiday_ranges
        .iter()
        .any(|(start, end)| *start <= date && date <= *end)
}

fn blocks_by_cycle_day(
    index: &crate::schedule::CourseIndex,
    cycle: u32,
    block_count: usize,
) -> Result<Vec<Vec<usize>>> {
    let decoded = decode_course_index(index, cycle, block_count)?;
    let mut blocks_by_day = vec![Vec::new(); (cycle * 5 + 1) as usize];
    for (cycle_day, block) in decoded {
        if let Some(blocks) = blocks_by_day.get_mut(cycle_day as usize) {
            blocks.push(block);
        }
    }
    Ok(blocks_by_day)
}

impl<'a> EventContext<'a> {
    fn new(
        term: &'a Term,
        config: &'a Config,
        course: &'a Course,
        timestamp: DateTime<Utc>,
    ) -> Result<Self> {
        let timetable = term
            .timetable
            .iter()
            .map(|time| parse_time(*time))
            .collect::<Result<Vec<_>>>()?;
        let location = course
            .location
            .as_ref()
            .map(|location| location.name())
            .unwrap_or("");
        let mut description = String::with_capacity(course.teacher.len() + location.len() + 1);
        description.push_str(&course.teacher);
        description.push('\n');
        description.push_str(location);
        let alarm_trigger = config
            .alarm
            .enabled
            .then(|| format_alarm_trigger(config.alarm.before[0], config.alarm.before[1]));
        let uid_timestamp = timestamp
            .timestamp_nanos_opt()
            .map(|value| value.to_string())
            .unwrap_or_else(|| timestamp.timestamp_micros().to_string());

        Ok(Self {
            term,
            course,
            timetable,
            dtstamp: format_utc_datetime(timestamp),
            description,
            alarm_trigger,
            uid_prefix: format!(
                "{uid_timestamp}-{}-{}",
                sanitize_uid_component(&term.name),
                sanitize_uid_component(&course.name)
            ),
        })
    }
}

fn push_uid(calendar: &mut String, context: &EventContext<'_>, uid_sequence: &mut u32) {
    *uid_sequence += 1;
    calendar.push_str("UID:");
    calendar.push_str(&context.uid_prefix);
    calendar.push('-');
    calendar.push_str(&uid_sequence.to_string());
    calendar.push_str("@ischedule-rs\r\n");
}

fn push_alarm(calendar: &mut String, trigger: &str) {
    push_line(calendar, "BEGIN:VALARM");
    push_line(calendar, "ACTION:DISPLAY");
    push_property(calendar, "DESCRIPTION", "提醒事项");
    push_property(calendar, "TRIGGER", trigger);
    push_line(calendar, "END:VALARM");
}

fn format_alarm_trigger(hours: i64, minutes: i64) -> String {
    let total_minutes = hours * 60 + minutes;
    if total_minutes == 0 {
        "-PT0S".to_string()
    } else if total_minutes % 60 == 0 {
        format!("-PT{}H", total_minutes / 60)
    } else if total_minutes > 60 {
        format!("-PT{}H{}M", total_minutes / 60, total_minutes % 60)
    } else {
        format!("-PT{total_minutes}M")
    }
}

fn push_line(output: &mut String, line: &str) {
    output.push_str(line);
    output.push_str("\r\n");
}

fn push_property(output: &mut String, key: &str, value: &str) {
    output.push_str(key);
    output.push(':');
    push_escaped_value(output, value);
    output.push_str("\r\n");
}

fn push_escaped_value(output: &mut String, value: &str) {
    if !value
        .as_bytes()
        .iter()
        .any(|byte| matches!(byte, b'\\' | b'\n' | b'\r' | b';' | b','))
    {
        output.push_str(value);
        return;
    }

    for ch in value.chars() {
        match ch {
            '\\' => output.push_str("\\\\"),
            '\n' => output.push_str("\\n"),
            '\r' => {}
            ';' => output.push_str("\\;"),
            ',' => output.push_str("\\,"),
            _ => output.push(ch),
        }
    }
}

fn sanitize_uid_component(value: &str) -> String {
    value
        .chars()
        .map(|ch| {
            if ch.is_ascii_alphanumeric() || matches!(ch, '-' | '_') {
                ch
            } else {
                '_'
            }
        })
        .collect()
}

fn format_local_datetime(value: chrono::NaiveDateTime) -> String {
    format!(
        "{:04}{:02}{:02}T{:02}{:02}{:02}",
        value.year(),
        value.month(),
        value.day(),
        value.hour(),
        value.minute(),
        value.second()
    )
}

fn format_utc_datetime(value: DateTime<Utc>) -> String {
    format!(
        "{:04}{:02}{:02}T{:02}{:02}{:02}Z",
        value.year(),
        value.month(),
        value.day(),
        value.hour(),
        value.minute(),
        value.second()
    )
}
