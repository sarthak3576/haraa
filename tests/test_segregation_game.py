from unittest.mock import MagicMock, patch

from app.services.segregation_game_data import GAME_BINS, GAME_ITEMS
from app.services.segregation_game_service import get_best_score, submit_score


def test_game_has_items_for_every_bin():
    bins_present = {item["bin"] for item in GAME_ITEMS}
    assert bins_present == set(GAME_BINS)
    assert len(GAME_ITEMS) >= 20


def test_submit_score_updates_when_higher(monkeypatch):
    fake_table = MagicMock()
    fake_table.get_item.return_value = {"Item": {"best_score": 5}}

    with patch("app.services.segregation_game_service._table", return_value=fake_table):
        result = submit_score("player@example.com", 10)

    assert result == 10
    fake_table.put_item.assert_called_once()


def test_submit_score_keeps_existing_when_lower(monkeypatch):
    fake_table = MagicMock()
    fake_table.get_item.return_value = {"Item": {"best_score": 12}}

    with patch("app.services.segregation_game_service._table", return_value=fake_table):
        result = submit_score("player@example.com", 7)

    assert result == 12
    fake_table.put_item.assert_not_called()


def test_get_best_score_defaults_to_zero(monkeypatch):
    fake_table = MagicMock()
    fake_table.get_item.return_value = {}

    with patch("app.services.segregation_game_service._table", return_value=fake_table):
        assert get_best_score("new-player@example.com") == 0
