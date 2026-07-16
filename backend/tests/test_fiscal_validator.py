"""
Tests for Spanish fiscal ID validator (DNI, NIE, CIF).
Test cases from ai-workspace/specs/03-mock-data.md
Verified manually against the official algorithm.
"""

import pytest

from app.services.fiscal_validator import validate_spanish_fiscal_id


# ── DNI ───────────────────────────────────────────────────────────────────────

class TestDNI:
    def test_valid_12345678z(self):
        # 12345678 % 23 = 14 → 'Z'
        assert validate_spanish_fiscal_id("12345678Z") == "DNI"

    def test_valid_00000000t(self):
        # 0 % 23 = 0 → 'T'
        assert validate_spanish_fiscal_id("00000000T") == "DNI"

    def test_valid_99999999r(self):
        # 99999999 % 23 = 1 → 'R'
        assert validate_spanish_fiscal_id("99999999R") == "DNI"

    def test_lowercase_input_accepted(self):
        assert validate_spanish_fiscal_id("12345678z") == "DNI"

    def test_wrong_letter_raises(self):
        with pytest.raises(ValueError, match="letra de control debe ser 'Z'"):
            validate_spanish_fiscal_id("12345678A")

    def test_too_few_digits_raises(self):
        with pytest.raises(ValueError, match="formato válido"):
            validate_spanish_fiscal_id("1234567Z")

    def test_too_many_digits_raises(self):
        with pytest.raises(ValueError, match="formato válido"):
            validate_spanish_fiscal_id("123456789Z")

    def test_letters_instead_of_digits_raises(self):
        with pytest.raises(ValueError, match="formato válido"):
            validate_spanish_fiscal_id("ABCDEFGHZ")


# ── NIE ───────────────────────────────────────────────────────────────────────

class TestNIE:
    def test_valid_x_prefix(self):
        # X→0: 01234567 % 23 = 14 → 'Z' ... let's use a known valid one
        # X0000000: 00000000 % 23 = 0 → 'T'
        assert validate_spanish_fiscal_id("X0000000T") == "NIE"

    def test_valid_y_prefix(self):
        # Y→1: 10000000 % 23 = 10000000 % 23
        # 23 * 434782 = 9999986, 10000000 - 9999986 = 14 → 'Z'
        assert validate_spanish_fiscal_id("Y0000000Z") == "NIE"

    def test_valid_z_prefix(self):
        # Z→2: 20000000 % 23
        # 23 * 869565 = 19999995, 20000000 - 19999995 = 5 → 'M' ... wait
        # Let me recalculate: 20000000 / 23 = 869565.21..., 23*869565 = 19999995
        # 20000000 - 19999995 = 5 → _DNI_LETTERS[5] = 'M'
        assert validate_spanish_fiscal_id("Z0000000M") == "NIE"

    def test_wrong_letter_raises(self):
        with pytest.raises(ValueError, match="letra de control"):
            validate_spanish_fiscal_id("X0000000A")

    def test_invalid_format_raises(self):
        with pytest.raises(ValueError, match="formato válido"):
            validate_spanish_fiscal_id("X123456Z")


# ── CIF ───────────────────────────────────────────────────────────────────────

class TestCIF:
    def test_valid_a28000727(self):
        # Verified manually: odd=8, even=15, total=23, ctrl=7, letter='G'
        # Type A → accepts digit or letter → '7' is valid
        assert validate_spanish_fiscal_id("A28000727") == "CIF"

    def test_valid_b83584466(self):
        # Verified manually: odd=19, even=15, total=34, ctrl=6
        # Type B (must digit) → '6' is valid
        assert validate_spanish_fiscal_id("B83584466") == "CIF"

    def test_invalid_b83584469(self):
        # Control should be 6, not 9
        with pytest.raises(ValueError, match="'6'"):
            validate_spanish_fiscal_id("B83584469")

    def test_invalid_control_digit_raises(self):
        with pytest.raises(ValueError, match="dígito de control"):
            validate_spanish_fiscal_id("A28000720")

    def test_invalid_format_raises(self):
        with pytest.raises(ValueError, match="formato válido"):
            validate_spanish_fiscal_id("B8358446")

    def test_random_string_raises(self):
        with pytest.raises(ValueError, match="formato válido"):
            validate_spanish_fiscal_id("INVALID123")

    def test_empty_raises(self):
        with pytest.raises(ValueError, match="vacío"):
            validate_spanish_fiscal_id("")

    def test_whitespace_only_raises(self):
        with pytest.raises(ValueError, match="vacío"):
            validate_spanish_fiscal_id("   ")


# ── Cross-type ────────────────────────────────────────────────────────────────

class TestCrossType:
    def test_dni_not_confused_with_cif(self):
        # DNI starts with digit, CIF starts with letter — no confusion possible
        assert validate_spanish_fiscal_id("12345678Z") == "DNI"

    def test_nie_not_confused_with_cif(self):
        assert validate_spanish_fiscal_id("X0000000T") == "NIE"
