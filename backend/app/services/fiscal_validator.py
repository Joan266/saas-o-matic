"""
Spanish fiscal ID validator: DNI, NIE, CIF.

Sources:
- DNI/NIE: Ministerio del Interior
  https://www.interior.gob.es/opencms/es/servicios-al-ciudadano/tramites-y-gestiones/dni/calculo-del-digito-de-control-del-nif-nie/
- CIF: Agencia Tributaria + proyectoa.com/el-cif-codigo-de-identificacion-fiscal/
"""

import re

# Official letter table for DNI/NIE control digit
_DNI_LETTERS = "TRWAGMYFPDXBNJZSQVHLCKE"

# NIE first-letter substitution
_NIE_PREFIX = {"X": "0", "Y": "1", "Z": "2"}

# CIF control letter table: index = control digit (0→J, 1→A, ... 9→I)
_CIF_LETTERS = "JABCDEFGHI"

# CIF org types that MUST use a letter as control
_CIF_MUST_LETTER = set("PQRSNW")

# CIF org types that MUST use a digit as control
_CIF_MUST_DIGIT = set("ABEH")

# All other CIF types accept either letter or digit


def validate_spanish_fiscal_id(fiscal_id: str) -> str:
    """
    Validate a Spanish DNI, NIE or CIF.
    Returns the detected type: 'DNI' | 'NIE' | 'CIF'
    Raises ValueError with a descriptive message if invalid.
    """
    fid = fiscal_id.strip().upper()

    if not fid:
        raise ValueError("El identificador fiscal no puede estar vacío.")

    if re.fullmatch(r"\d{8}[A-Z]", fid):
        return _validate_dni(fid)

    if re.fullmatch(r"[XYZ]\d{7}[A-Z]", fid):
        return _validate_nie(fid)

    if re.fullmatch(r"[A-Z]\d{7}[A-Z0-9]", fid):
        return _validate_cif(fid)

    raise ValueError(
        f"'{fiscal_id}' no tiene un formato válido de DNI, NIE o CIF."
    )


# ── DNI ───────────────────────────────────────────────────────────────────────

def _validate_dni(fid: str) -> str:
    number = int(fid[:8])
    expected = _DNI_LETTERS[number % 23]
    if fid[8] != expected:
        raise ValueError(
            f"DNI '{fid}' inválido: la letra de control debe ser '{expected}'."
        )
    return "DNI"


# ── NIE ───────────────────────────────────────────────────────────────────────

def _validate_nie(fid: str) -> str:
    number_str = _NIE_PREFIX[fid[0]] + fid[1:8]
    expected = _DNI_LETTERS[int(number_str) % 23]
    if fid[8] != expected:
        raise ValueError(
            f"NIE '{fid}' inválido: la letra de control debe ser '{expected}'."
        )
    return "NIE"


# ── CIF ───────────────────────────────────────────────────────────────────────

def _validate_cif(fid: str) -> str:
    org_type = fid[0]
    digits = fid[1:8]
    control = fid[8]

    control_digit, control_letter = _cif_control(digits)

    if org_type in _CIF_MUST_LETTER:
        if control != control_letter:
            raise ValueError(
                f"CIF '{fid}' inválido: el dígito de control debe ser la letra '{control_letter}'."
            )
    elif org_type in _CIF_MUST_DIGIT:
        if control != str(control_digit):
            raise ValueError(
                f"CIF '{fid}' inválido: el dígito de control debe ser el número '{control_digit}'."
            )
    else:
        if control not in (str(control_digit), control_letter):
            raise ValueError(
                f"CIF '{fid}' inválido: el dígito de control debe ser "
                f"'{control_digit}' o '{control_letter}'."
            )
    return "CIF"


def _cif_control(digits: str) -> tuple[int, str]:
    """
    Compute CIF control digit and letter from the 7 central digits.

    Odd positions (1,3,5,7 → indices 0,2,4,6): multiply by 2, sum resulting digits.
    Even positions (2,4,6 → indices 1,3,5): sum directly.
    control_digit = (10 - (total % 10)) % 10
    control_letter = _CIF_LETTERS[control_digit]
    """
    odd_sum = 0
    for i in (0, 2, 4, 6):  # positions 1, 3, 5, 7
        doubled = int(digits[i]) * 2
        odd_sum += doubled // 10 + doubled % 10

    even_sum = sum(int(digits[i]) for i in (1, 3, 5))  # positions 2, 4, 6

    control_digit = (10 - (odd_sum + even_sum) % 10) % 10
    return control_digit, _CIF_LETTERS[control_digit]
