from collections.abc import Callable


def validate_ecuador_national_id(value: str) -> bool:
    digits = "".join(character for character in value if character.isdigit())
    if len(digits) != 10 or len(set(digits)) == 1:
        return False
    province = int(digits[:2])
    third_digit = int(digits[2])
    if province < 1 or province > 24 or third_digit >= 6:
        return False

    total = 0
    for index, character in enumerate(digits[:9]):
        value_at_index = int(character) * (2 if index % 2 == 0 else 1)
        total += value_at_index - 9 if value_at_index > 9 else value_at_index
    check_digit = (10 - total % 10) % 10
    return check_digit == int(digits[9])


VALIDATORS: dict[str, Callable[[str], bool]] = {
    "ecuador_national_id": validate_ecuador_national_id,
}
