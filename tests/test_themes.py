from app.themes import tag_text


def test_detects_expected_themes():
    t = tag_text("A ransomware attack could trigger regulatory fines.")
    assert {"cyber", "regulatory", "litigation"} <= set(t)


def test_word_boundaries_avoid_false_matches():
    assert "commodity" not in tag_text("We boil water for the royal tea.")  # 'oil' inside 'boil'


def test_no_theme_for_neutral_text():
    assert tag_text("The quick brown fox.") == []
