"""
Tests de fecha/hora — caso H.

Verifica que get_current_timestamp() usa America/Bogota
y devuelve los campos requeridos.
"""

from utils.date_time import get_current_timestamp


class TestGetCurrentTimestamp:

    def test_returns_dict(self):
        """H1 — devuelve un dict."""
        result = get_current_timestamp()
        assert isinstance(result, dict)

    def test_required_fields(self):
        """H2 — contiene todos los campos requeridos."""
        result = get_current_timestamp()
        for field in ("timezone", "datetime", "date", "time", "day_of_week", "utc_offset"):
            assert field in result, f"Campo faltante: {field}"

    def test_timezone_bogota(self):
        """H3 — timezone siempre es America/Bogota."""
        result = get_current_timestamp()
        assert result["timezone"] == "America/Bogota"

    def test_utc_offset_bogota(self):
        """H4 — utc_offset es -05:00 (Colombia no tiene DST)."""
        result = get_current_timestamp()
        assert result["utc_offset"] == "-05:00"

    def test_datetime_contains_offset(self):
        """H5 — datetime ISO 8601 incluye el offset -05:00."""
        result = get_current_timestamp()
        assert "-05:00" in result["datetime"]

    def test_date_format(self):
        """H6 — date tiene formato YYYY-MM-DD."""
        result = get_current_timestamp()
        parts = result["date"].split("-")
        assert len(parts) == 3
        assert len(parts[0]) == 4  # year
        assert len(parts[1]) == 2  # month
        assert len(parts[2]) == 2  # day

    def test_day_of_week_is_string(self):
        """H7 — day_of_week es un string no vacío."""
        result = get_current_timestamp()
        assert isinstance(result["day_of_week"], str)
        assert len(result["day_of_week"]) > 0
