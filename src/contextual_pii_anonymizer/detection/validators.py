"""Validators for Ecuadorian structured identifiers."""

from __future__ import annotations


def only_digits(value: str) -> str:
    return "".join(char for char in value if char.isdigit())


def is_valid_ec_cedula(value: str) -> bool:
    digits = only_digits(value)
    if len(digits) != 10 or not digits.isdigit():
        return False

    province = int(digits[:2])
    third_digit = int(digits[2])
    if province < 1 or province > 24 or third_digit >= 6:
        return False

    coefficients = [2, 1, 2, 1, 2, 1, 2, 1, 2]
    total = 0
    for digit, coefficient in zip(digits[:9], coefficients):
        product = int(digit) * coefficient
        total += product - 9 if product >= 10 else product

    verifier = (10 - (total % 10)) % 10
    return verifier == int(digits[9])


def is_valid_ec_ruc(value: str) -> bool:
    digits = only_digits(value)
    if len(digits) != 13 or not digits.endswith("001"):
        return False

    # TODO: pending research - add full validation for public and private legal entities.
    return is_valid_ec_cedula(digits[:10])
