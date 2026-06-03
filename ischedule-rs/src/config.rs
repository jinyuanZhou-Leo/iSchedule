use serde::Deserialize;

#[derive(Debug, Clone, Deserialize, PartialEq, Eq)]
pub struct Config {
    pub name: String,
    pub color: String,
    pub alarm: AlarmConfig,
    #[serde(rename = "countDayInHoliday")]
    pub count_day_in_holiday: bool,
    #[serde(rename = "reduceFileSize", default)]
    pub reduce_file_size: bool,
}

#[derive(Debug, Clone, Deserialize, PartialEq, Eq)]
pub struct AlarmConfig {
    pub enabled: bool,
    pub before: [i64; 2],
}

impl Config {
    pub fn calendar_name(&self, term_name: &str) -> String {
        format!("{} - {term_name}", self.name)
    }

    pub fn normalized_color(&self) -> String {
        let color = self.color.trim();
        if color.eq_ignore_ascii_case("random") || !is_hex_color(color) {
            "#67e4fa".to_string()
        } else if color.len() == 9 {
            color[..7].to_string()
        } else {
            color.to_string()
        }
    }
}

fn is_hex_color(value: &str) -> bool {
    let hex = value.strip_prefix('#').unwrap_or_default();
    (hex.len() == 6 || hex.len() == 8) && hex.chars().all(|ch| ch.is_ascii_hexdigit())
}
