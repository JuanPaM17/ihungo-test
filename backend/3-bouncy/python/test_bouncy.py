import pytest
from bouncy import is_bouncy, least_number_with_bouncy_ratio


# ---------------------------------------------------------------------------
# is_bouncy
# ---------------------------------------------------------------------------

class TestIsBouncy:
    def test_increasing_number_is_not_bouncy(self):
        # 134468: cada dígito >= anterior -> increasing
        assert is_bouncy(134468) is False

    def test_decreasing_number_is_not_bouncy(self):
        # 66420: cada dígito <= anterior -> decreasing
        assert is_bouncy(66420) is False

    def test_bouncy_example_from_problem(self):
        # 155349: ejemplo explícito del enunciado
        assert is_bouncy(155349) is True

    def test_numbers_below_100_are_not_bouncy(self):
        # El enunciado afirma que no existen bouncy numbers below 100
        for n in range(1, 100):
            assert is_bouncy(n) is False, f"{n} should not be bouncy"

    def test_single_digit_is_not_bouncy(self):
        for n in range(1, 10):
            assert is_bouncy(n) is False

    def test_all_same_digits_is_not_bouncy(self):
        assert is_bouncy(111) is False
        assert is_bouncy(999) is False

    def test_100_is_not_bouncy(self):
        # 100 -> 1,0,0 -> decreasing
        assert is_bouncy(100) is False

    def test_first_bouncy_number(self):
        # El primer bouncy number es 101: 1,0,1
        assert is_bouncy(101) is True


# ---------------------------------------------------------------------------
# least_number_with_bouncy_ratio
# ---------------------------------------------------------------------------

class TestLeastNumberWithBouncyRatio:
    def test_50_percent_returns_538(self):
        assert least_number_with_bouncy_ratio(50) == 538

    def test_90_percent_returns_21780(self):
        assert least_number_with_bouncy_ratio(90) == 21780

    def test_returns_integer(self):
        # Usamos 50 que ya sabemos que termina rápido
        result = least_number_with_bouncy_ratio(50)
        assert isinstance(result, int)

    def test_result_is_positive(self):
        assert least_number_with_bouncy_ratio(50) > 0

    def test_zero_percent_raises(self):
        with pytest.raises(ValueError):
            least_number_with_bouncy_ratio(0)

    def test_100_percent_raises(self):
        with pytest.raises(ValueError):
            least_number_with_bouncy_ratio(100)

    def test_negative_percent_raises(self):
        with pytest.raises(ValueError):
            least_number_with_bouncy_ratio(-1)

    def test_above_99_raises(self):
        with pytest.raises(ValueError):
            least_number_with_bouncy_ratio(101)
