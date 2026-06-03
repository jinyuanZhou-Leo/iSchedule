use std::{fmt, marker::PhantomData};

use serde::{
    Deserialize, Deserializer,
    de::{MapAccess, Visitor},
};
use serde_json::Value;

use crate::{IScheduleError, Result};

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Term {
    pub name: String,
    pub start: [i32; 3],
    pub end: [i32; 3],
    pub duration: i64,
    pub timetable: Vec<[u32; 2]>,
    pub cycle: u32,
    pub courses: Vec<Course>,
    pub holidays: Vec<Holiday>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Course {
    pub name: String,
    pub teacher: String,
    pub index: CourseIndex,
    pub location: Option<Location>,
    pub cycle: Option<u32>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum Location {
    Named(String),
    Coordinates {
        name: String,
        latitude: String,
        longitude: String,
    },
}

impl Location {
    pub fn name(&self) -> &str {
        match self {
            Location::Named(name) => name,
            Location::Coordinates { name, .. } => name,
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Holiday {
    pub name: String,
    pub kind: String,
    pub date: Vec<[i32; 3]>,
    pub compensation: Vec<([i32; 3], u32)>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum CourseIndex {
    Traditional(Vec<(IndexSelector, IndexSelector)>),
    PowerSchool(Vec<String>),
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum IndexSelector {
    Odd,
    Even,
    Everyday,
    Day(u32),
    Days(Vec<u32>),
}

#[derive(Debug, Deserialize)]
struct RawTerm {
    start: [i32; 3],
    end: [i32; 3],
    duration: i64,
    timetable: Vec<[u32; 2]>,
    cycle: u32,
    #[serde(deserialize_with = "deserialize_ordered_map")]
    courses: Vec<(String, RawCourse)>,
    #[serde(default, deserialize_with = "deserialize_ordered_map")]
    holidays: Vec<(String, RawHoliday)>,
}

#[derive(Debug, Deserialize)]
struct RawCourse {
    teacher: String,
    #[serde(deserialize_with = "deserialize_course_index")]
    index: CourseIndex,
    #[serde(default, deserialize_with = "deserialize_location")]
    location: Option<Location>,
    #[serde(default)]
    cycle: Option<u32>,
}

#[derive(Debug, Deserialize)]
struct RawHoliday {
    #[serde(rename = "type")]
    kind: String,
    date: Vec<[i32; 3]>,
    #[serde(default, rename = "compensation")]
    compensation: Vec<([i32; 3], u32)>,
}

pub fn parse_schedule_json(content: &str) -> std::result::Result<Vec<Term>, serde_json::Error> {
    let raw: OrderedMap<RawTerm> = serde_json::from_str(content)?;
    Ok(raw
        .0
        .into_iter()
        .map(|(name, term)| Term {
            name,
            start: term.start,
            end: term.end,
            duration: term.duration,
            timetable: term.timetable,
            cycle: term.cycle,
            courses: term
                .courses
                .into_iter()
                .map(|(name, course)| Course {
                    name,
                    teacher: course.teacher,
                    index: course.index,
                    location: course.location,
                    cycle: course.cycle,
                })
                .collect(),
            holidays: term
                .holidays
                .into_iter()
                .map(|(name, holiday)| Holiday {
                    name,
                    kind: holiday.kind,
                    date: holiday.date,
                    compensation: holiday.compensation,
                })
                .collect(),
        })
        .collect())
}

impl Term {
    pub fn validate(&self) -> Result<()> {
        if self.cycle == 0 {
            return Err(IScheduleError::InvalidCycle(self.cycle));
        }
        for course in &self.courses {
            if matches!(course.cycle, Some(0)) {
                return Err(IScheduleError::InvalidCycle(0));
            }
        }
        Ok(())
    }
}

fn deserialize_location<'de, D>(deserializer: D) -> std::result::Result<Option<Location>, D::Error>
where
    D: Deserializer<'de>,
{
    let value = Option::<Value>::deserialize(deserializer)?;
    let Some(value) = value else {
        return Ok(None);
    };

    match value {
        Value::String(name) => Ok(Some(Location::Named(name))),
        Value::Array(values) => {
            let name = values
                .first()
                .and_then(Value::as_str)
                .unwrap_or("")
                .to_string();
            let latitude = value_to_string(values.get(1)).unwrap_or_else(|| "0".to_string());
            let longitude = value_to_string(values.get(2)).unwrap_or_else(|| "0".to_string());
            Ok(Some(Location::Coordinates {
                name,
                latitude,
                longitude,
            }))
        }
        _ => Ok(None),
    }
}

struct OrderedMap<T>(Vec<(String, T)>);

impl<'de, T> Deserialize<'de> for OrderedMap<T>
where
    T: Deserialize<'de>,
{
    fn deserialize<D>(deserializer: D) -> std::result::Result<Self, D::Error>
    where
        D: Deserializer<'de>,
    {
        deserialize_ordered_map(deserializer).map(Self)
    }
}

fn deserialize_ordered_map<'de, D, T>(
    deserializer: D,
) -> std::result::Result<Vec<(String, T)>, D::Error>
where
    D: Deserializer<'de>,
    T: Deserialize<'de>,
{
    struct OrderedMapVisitor<T> {
        marker: PhantomData<T>,
    }

    impl<'de, T> Visitor<'de> for OrderedMapVisitor<T>
    where
        T: Deserialize<'de>,
    {
        type Value = Vec<(String, T)>;

        fn expecting(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
            formatter.write_str("a JSON object")
        }

        fn visit_map<A>(self, mut map: A) -> std::result::Result<Self::Value, A::Error>
        where
            A: MapAccess<'de>,
        {
            let mut items = Vec::with_capacity(map.size_hint().unwrap_or(0));
            while let Some((key, value)) = map.next_entry()? {
                items.push((key, value));
            }
            Ok(items)
        }
    }

    deserializer.deserialize_map(OrderedMapVisitor {
        marker: PhantomData,
    })
}

fn deserialize_course_index<'de, D>(deserializer: D) -> std::result::Result<CourseIndex, D::Error>
where
    D: Deserializer<'de>,
{
    let value = Value::deserialize(deserializer)?;
    let Value::Array(items) = value else {
        return Err(serde::de::Error::custom("course index must be an array"));
    };

    if items.iter().all(Value::is_string) {
        return Ok(CourseIndex::PowerSchool(
            items
                .into_iter()
                .filter_map(|item| item.as_str().map(ToOwned::to_owned))
                .collect(),
        ));
    }

    let mut decoded = Vec::new();
    for item in items {
        let Value::Array(pair) = item else {
            return Err(serde::de::Error::custom(
                "traditional index item must be an array",
            ));
        };
        if pair.len() != 2 {
            return Err(serde::de::Error::custom(
                "traditional index item must have two elements",
            ));
        }
        decoded.push((parse_selector(&pair[0])?, parse_selector(&pair[1])?));
    }
    Ok(CourseIndex::Traditional(decoded))
}

fn parse_selector<E: serde::de::Error>(value: &Value) -> std::result::Result<IndexSelector, E> {
    match value {
        Value::String(text) if text.eq_ignore_ascii_case("odd") => Ok(IndexSelector::Odd),
        Value::String(text) if text.eq_ignore_ascii_case("even") => Ok(IndexSelector::Even),
        Value::String(text) if text.eq_ignore_ascii_case("everyday") => Ok(IndexSelector::Everyday),
        Value::Number(number) => number
            .as_u64()
            .map(|value| IndexSelector::Day(value as u32))
            .ok_or_else(|| serde::de::Error::custom("index number must be positive")),
        Value::Array(values) => {
            let mut days = Vec::new();
            for value in values {
                match parse_selector(value)? {
                    IndexSelector::Day(day) => days.push(day),
                    IndexSelector::Odd | IndexSelector::Even | IndexSelector::Everyday => {
                        return Err(serde::de::Error::custom(
                            "nested selector keywords are not supported",
                        ));
                    }
                    IndexSelector::Days(nested) => days.extend(nested),
                }
            }
            Ok(IndexSelector::Days(days))
        }
        _ => Err(serde::de::Error::custom("unsupported index selector")),
    }
}

fn value_to_string(value: Option<&Value>) -> Option<String> {
    match value? {
        Value::String(text) => Some(text.clone()),
        Value::Number(number) => Some(number.to_string()),
        _ => None,
    }
}
