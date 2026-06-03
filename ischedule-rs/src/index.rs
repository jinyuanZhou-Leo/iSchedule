use crate::{
    IScheduleError, Result,
    schedule::{CourseIndex, IndexSelector},
};

pub fn decode_course_index(
    index: &CourseIndex,
    cycle: u32,
    block_count: usize,
) -> Result<Vec<(u32, usize)>> {
    if cycle == 0 {
        return Err(IScheduleError::InvalidCycle(cycle));
    }

    match index {
        CourseIndex::Traditional(items) => decode_traditional(items, cycle, block_count),
        CourseIndex::PowerSchool(items) => decode_powerschool(items, cycle * 5, block_count),
    }
}

fn decode_traditional(
    items: &[(IndexSelector, IndexSelector)],
    cycle: u32,
    block_count: usize,
) -> Result<Vec<(u32, usize)>> {
    let max_day = cycle * 5;
    let mut decoded = Vec::new();
    for (day_selector, block_selector) in items {
        for day in expand_selector(day_selector, max_day)? {
            for block in expand_selector(block_selector, block_count as u32)? {
                decoded.push((day, (block - 1) as usize));
            }
        }
    }
    Ok(decoded)
}

fn decode_powerschool(
    items: &[String],
    max_day: u32,
    block_count: usize,
) -> Result<Vec<(u32, usize)>> {
    let mut decoded = Vec::new();
    for item in items {
        let text = item.trim().to_ascii_lowercase();
        let Some(rest) = text.strip_prefix('p') else {
            return Err(IScheduleError::InvalidIndex(item.clone()));
        };
        let Some(paren_start) = rest.find('(') else {
            return Err(IScheduleError::InvalidIndex(item.clone()));
        };
        let Some(paren_end) = rest.rfind(')') else {
            return Err(IScheduleError::InvalidIndex(item.clone()));
        };
        let block: u32 = rest[..paren_start]
            .trim()
            .parse()
            .map_err(|_| IScheduleError::InvalidIndex(item.clone()))?;
        if block == 0 || block as usize > block_count {
            return Err(IScheduleError::InvalidIndex(item.clone()));
        }
        let components = &rest[paren_start + 1..paren_end];
        for component in components.split(',') {
            for day in expand_powerschool_component(component.trim(), max_day)? {
                decoded.push((day, (block - 1) as usize));
            }
        }
    }
    Ok(decoded)
}

fn expand_selector(selector: &IndexSelector, maximum: u32) -> Result<Vec<u32>> {
    let values = match selector {
        IndexSelector::Odd => (1..=maximum).filter(|value| value % 2 == 1).collect(),
        IndexSelector::Even => (1..=maximum).filter(|value| value % 2 == 0).collect(),
        IndexSelector::Everyday => (1..=maximum).collect(),
        IndexSelector::Day(value) => vec![*value],
        IndexSelector::Days(values) => values.clone(),
    };

    if values.iter().any(|value| *value == 0 || *value > maximum) {
        return Err(IScheduleError::InvalidIndex(format!(
            "selector value out of range 1..={maximum}"
        )));
    }
    Ok(values)
}

fn expand_powerschool_component(component: &str, maximum: u32) -> Result<Vec<u32>> {
    match component {
        "odd" => Ok((1..=maximum).filter(|value| value % 2 == 1).collect()),
        "even" => Ok((1..=maximum).filter(|value| value % 2 == 0).collect()),
        "everyday" => Ok((1..=maximum).collect()),
        _ if component.contains('-') => {
            let (left, right) = component
                .split_once('-')
                .ok_or_else(|| IScheduleError::InvalidIndex(component.to_string()))?;
            let left: u32 = left
                .trim()
                .parse()
                .map_err(|_| IScheduleError::InvalidIndex(component.to_string()))?;
            let right: u32 = right
                .trim()
                .parse()
                .map_err(|_| IScheduleError::InvalidIndex(component.to_string()))?;
            if left == 0 || right > maximum || left > right {
                return Err(IScheduleError::InvalidIndex(component.to_string()));
            }
            Ok((left..=right).collect())
        }
        _ => {
            let value: u32 = component
                .parse()
                .map_err(|_| IScheduleError::InvalidIndex(component.to_string()))?;
            if value == 0 || value > maximum {
                return Err(IScheduleError::InvalidIndex(component.to_string()));
            }
            Ok(vec![value])
        }
    }
}
