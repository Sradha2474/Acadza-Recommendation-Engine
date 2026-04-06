from services.marks import marks_to_percentage, parse_marks


def test_parse_marks_plain_int() -> None:
    assert parse_marks(49) == 49.0


def test_parse_marks_fraction() -> None:
    assert parse_marks("39/100") == 39.0


def test_parse_marks_plus_minus() -> None:
    assert parse_marks("+48 -8") == 40.0


def test_marks_to_percentage_fraction() -> None:
    assert marks_to_percentage("39/100", {"total_questions": 25}) == 39.0


def test_marks_to_percentage_plus_minus() -> None:
    assert marks_to_percentage("+48 -8", {"total_questions": 25}) == 40.0

