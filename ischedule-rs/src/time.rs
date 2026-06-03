use chrono::{Datelike, Days, NaiveDate, NaiveDateTime, NaiveTime};

use crate::{IScheduleError, Result};

pub fn parse_date(value: [i32; 3]) -> Result<NaiveDate> {
    NaiveDate::from_ymd_opt(value[0], value[1] as u32, value[2] as u32)
        .ok_or(IScheduleError::InvalidDate(value))
}

pub fn parse_time(value: [u32; 2]) -> Result<NaiveTime> {
    NaiveTime::from_hms_opt(value[0], value[1], 0).ok_or(IScheduleError::InvalidTime(value))
}

pub fn date_range(start: NaiveDate, end: NaiveDate) -> impl Iterator<Item = NaiveDate> {
    let days = (end - start).num_days().max(0) as u64;
    (0..=days).filter_map(move |offset| start.checked_add_days(Days::new(offset)))
}

pub fn is_workday(date: NaiveDate) -> bool {
    date.weekday().number_from_monday() <= 5
}

pub fn week_info(cycle_day: u32) -> (u32, u32) {
    let full_week = if cycle_day.is_multiple_of(5) {
        cycle_day / 5 - 1
    } else {
        cycle_day / 5
    };
    let day = cycle_day - full_week * 5;
    (day, full_week)
}

pub fn rrule_day(day: u32) -> Result<&'static str> {
    match day {
        1 => Ok("MO"),
        2 => Ok("TU"),
        3 => Ok("WE"),
        4 => Ok("TH"),
        5 => Ok("FR"),
        _ => Err(IScheduleError::InvalidIndex(format!(
            "invalid weekday {day}"
        ))),
    }
}

pub fn combine(date: NaiveDate, time: NaiveTime) -> NaiveDateTime {
    NaiveDateTime::new(date, time)
}
