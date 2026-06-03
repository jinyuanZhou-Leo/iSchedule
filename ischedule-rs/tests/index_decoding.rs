use ischedule_rs::{
    index::decode_course_index,
    schedule::{CourseIndex, IndexSelector},
};

#[test]
fn decodes_odd_even_everyday_and_explicit_days() {
    let index = CourseIndex::Traditional(vec![
        (IndexSelector::Odd, IndexSelector::Day(1)),
        (IndexSelector::Even, IndexSelector::Day(2)),
        (IndexSelector::Days(vec![1, 6]), IndexSelector::Day(3)),
    ]);

    let decoded = decode_course_index(&index, 2, 3).unwrap();

    assert!(decoded.contains(&(1, 0)));
    assert!(decoded.contains(&(3, 0)));
    assert!(decoded.contains(&(5, 0)));
    assert!(decoded.contains(&(7, 0)));
    assert!(decoded.contains(&(9, 0)));
    assert!(decoded.contains(&(2, 1)));
    assert!(decoded.contains(&(4, 1)));
    assert!(decoded.contains(&(6, 2)));
}

#[test]
fn decodes_powerschool_style_indexes() {
    let index = CourseIndex::PowerSchool(vec!["P2(1-2, even)".to_string()]);

    let decoded = decode_course_index(&index, 2, 5).unwrap();

    assert!(decoded.contains(&(1, 1)));
    assert!(decoded.contains(&(2, 1)));
    assert!(decoded.contains(&(4, 1)));
    assert!(decoded.contains(&(6, 1)));
    assert!(decoded.contains(&(8, 1)));
    assert!(decoded.contains(&(10, 1)));
}
