from src.models import DialogueLine, CharacterStats, CastExtractionResult


def test_dialogue_line_creation():
    line = DialogueLine(
        speaker="SAL",
        text="Hallettim.",
        timecode="02.45",
        page=1,
        paragraph_index=10
    )
    assert line.speaker == "SAL"
    assert line.text == "Hallettim."
    assert line.timecode == "02.45"
    assert line.page == 1
    assert line.paragraph_index == 10


def test_dialogue_line_defaults():
    line = DialogueLine(speaker="ANNA", text="Merhaba.")
    assert line.speaker == "ANNA"
    assert line.text == "Merhaba."
    assert line.timecode is None
    assert line.page == 1
    assert line.paragraph_index == 0


def test_character_stats_aggregation():
    stats = CharacterStats(name="SAL", first_seen_order=2)
    stats.add_line(page=1)
    stats.add_line(page=2)
    stats.add_line(page=1)

    assert stats.line_count == 3
    assert stats.pages == {1, 2}
    assert stats.formatted_pages == "1, 2"


def test_character_stats_formatted_pages_empty():
    stats = CharacterStats(name="GHOST", first_seen_order=99)
    assert stats.line_count == 0
    assert stats.pages == set()
    assert stats.formatted_pages == ""
    assert stats.notes == ""


def test_cast_extraction_result_creation():
    char1 = CharacterStats(name="SAL", first_seen_order=1)
    char1.add_line(page=1)
    result = CastExtractionResult(
        characters=[char1],
        metadata={"title": "Test Movie"},
        total_lines=1,
        total_pages=1
    )
    assert len(result.characters) == 1
    assert result.characters[0].name == "SAL"
    assert result.metadata == {"title": "Test Movie"}
    assert result.total_lines == 1
    assert result.total_pages == 1


def test_cast_extraction_result_defaults():
    result = CastExtractionResult(characters=[])
    assert result.characters == []
    assert result.metadata == {}
    assert result.total_lines == 0
    assert result.total_pages == 0
