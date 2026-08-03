# logic file for rounding

"""
1. Write rounding logic in rounding_helpers.py
2. Connect it to rounding_tab() in app.py
3. Test in Streamlit
4. Prepare screenshots/test cases
5. Add your README explanation later
"""

from decimal import Decimal, InvalidOperation
from typing import Any

MAX_SIGNIFICANT_DIGITS = 16 # max significant digits for decimal precision of IEEE-754 double-precision values

# ----------- SHARED ROUNDING PIPELINE -----------
""" 
func: round a number using all four rounding methods and return a dictionary containing the results for each method along with input details and any errors encountered during parsing
return (dict): dictionary containing input details, target digits, and results for each rounding method

number: str - input number to round (decimal or binary)
digits: int - target number of significant digits to round to
input_format: str - format of the input number ("Decimal" or "Binary")

! call func -> results = rnd.round_all_methods(number, digits, input_format)
eg: round_all_methods("123.456", 4, "Decimal") -> {"error": None, "input": "123.456", "normalized_input": "123.456", "input_format": "Decimal", "base": 10, "digits": 4, "results": {...}}
"""
def round_all_methods(number: str, digits: int, input_format: str) -> dict:
    try:
        parsed_digits = _parse_digits(digits)
        sign, whole, frac, base = _parse_number(number, input_format)

        return {
            "error": None,
            "input": str(number),
            "normalized_input": _normalized_text(sign, whole, frac),
            "input_format": input_format,
            "base": base,
            "digits": parsed_digits,
            "results": {
                "Chopping": _round_parsed(sign, whole, frac, base, parsed_digits, "chop"),
                "Round Up": _round_parsed(sign, whole, frac, base, parsed_digits, "up"),
                "Round Down": _round_parsed(sign, whole, frac, base, parsed_digits, "down"),
                "Round to Nearest (Ties to Even)": _round_parsed(
                    sign, whole, frac, base, parsed_digits, "nearest_even"
                ),
            },
        }

    except ValueError as exc:
        return {
            "error": str(exc),
            "input": str(number),
            "input_format": input_format,
            "digits": digits,
            "results": None,
        }

""" 
main func: round a parsed number based on specified rounding mode, base, and target significant digits
return (dict): dictionary containing rounded value, whether it changed, discarded digits, whether incremented, and explanation of the rounding process

sign: str - sign of the number ("-" or "")
whole: str - whole part of the number (digits before the decimal point)
frac: str - fractional part of the number (digits after the decimal point)
base: int - base in which the digits are represented (e.g., 10 for decimal, 2 for binary)
digits: int - target number of significant digits to round to
mode: str - rounding mode ("chop", "up", "down", "nearest_even")

eg: _round_parsed("-", "123", "45", 10, 3, "nearest_even") -> {"value": "-123.5", "changed": True, "discarded": "0", "incremented": True, "explanation": "..."}
"""
def _round_parsed(
    sign: str,
    whole: str,
    frac: str,
    base: int,
    digits: int,
    mode: str,
) -> dict:
    # extra guard for direct calls (even though public APIs validate digits)
    if digits < 1:
        raise ValueError("Significant digits must be at least 1")

    is_negative = sign == "-"
    original = _normalized_text(sign, whole, frac)

    # Zero short-circuit.
    if whole == "0" and not _has_nonzero_digits(frac):
        zero_value = "-0" if is_negative else "0"
        return {
            "value": zero_value,
            "changed": False,
            "discarded": "",
            "incremented": False,
            "explanation": "Zero stays zero for all four methods.",
        }

    exponent, significant = _extract_significant_digits(whole, frac)

    # Keep requested significant digits, pad if needed.
    kept = significant[:digits].ljust(digits, "0")
    discarded = significant[digits:]

    incremented = _should_increment(
        mode=mode,
        discarded=discarded,
        last_kept_digit=kept[-1],
        base=base,
        is_negative=is_negative,
    )

    rounded = kept

    if incremented:
        rounded = _add_one_in_base(rounded, base)

        # Overflow of kept width: shift exponent and trim one trailing digit.
        if len(rounded) > digits:
            exponent += 1
            rounded = rounded[:-1]

    value = _build_from_significant(sign, rounded, exponent)

    return {
        "value": value,
        "changed": value != original,
        "discarded": discarded,
        "incremented": incremented,
        "explanation": _build_explanation(mode, discarded, incremented, is_negative),
    }


# ----------- ROUNDING METHODS -----------

""" 
func: round a number using truncation (chopping) method and return a dictionary containing the rounded value, whether it changed, discarded digits, whether incremented, and explanation of the rounding process

truncation example:
123.456 -> 123.4 (truncate after 4 significant digits)
"""
def round_chop(number: str, digits: int, input_format: str = "Decimal") -> dict:
    parsed_digits = _parse_digits(digits)
    sign, whole, frac, base = _parse_number(number, input_format)
    return _round_parsed(sign, whole, frac, base, parsed_digits, "chop")

""" 
func: round a number using the rounding up method and return a dictionary containing the rounded value, whether it changed, discarded digits, whether incremented, and explanation of the rounding process

rounding up example:
123.456 -> 123.5 (round up after 4 significant digits)
"""
def round_up(number: str, digits: int, input_format: str = "Decimal") -> dict:
    parsed_digits = _parse_digits(digits)
    sign, whole, frac, base = _parse_number(number, input_format)
    return _round_parsed(sign, whole, frac, base, parsed_digits, "up")

""" 
func: round a number using the rounding down method and return a dictionary containing the rounded value, whether it changed, discarded digits, whether incremented, and explanation of the rounding process

rounding down example:
123.456 -> 123.4 (round down after 4 significant digits)
"""
def round_down(number: str, digits: int, input_format: str = "Decimal") -> dict:
    parsed_digits = _parse_digits(digits)
    sign, whole, frac, base = _parse_number(number, input_format)
    return _round_parsed(sign, whole, frac, base, parsed_digits, "down")

""" 
func: round a number using the rounding to nearest, ties to even method and return a dictionary containing the rounded value, whether it changed, discarded digits, whether incremented, and explanation of the rounding process

rounding to nearest, ties to even example:
123.456 -> 123.5 (round to nearest, ties to even after 4 significant digits)
"""
def round_nearest_ties_even(number: str, digits: int, input_format: str = "Decimal") -> dict:
    parsed_digits = _parse_digits(digits)
    sign, whole, frac, base = _parse_number(number, input_format)
    return _round_parsed(sign, whole, frac, base, parsed_digits, "nearest_even")


# ----------- ROUNDING HELPER FUNC -----------
""" 
helper func: add one to a string of digits in a specified base (for rounding purposes)
return (str): string of digits after adding one

digits: str - string of digits to which one will be added
base: int - base in which the digits are represented (e.g., 10 for decimal, 2 for binary)

eg: _add_one_in_base("999", 10) -> "1000"
eg: _add_one_in_base("111", 2) -> "1000"
"""
def _add_one_in_base(digits: str, base: int) -> str:
    # convert string to list for mutability
    result = list(digits)
    carry = 1

    # iterate from the last digit to the first, adding carry and handling overflow
    for i in range(len(result) - 1, -1, -1):
        value = _digit_to_value(result[i]) + carry
        if value >= base:
            result[i] = "0"
            carry = 1
        else:
            result[i] = str(value)
            carry = 0
            break
    # if there's still a carry after processing all digits, prepend "1" to the result
    if carry:
        result.insert(0, "1")

    return "".join(result)

""" 
func: determine if rounding should increment the last kept digit based on the specified rounding mode, discarded digits, last kept digit, base, and sign of the number
return (bool): True if the last kept digit should be incremented, False otherwise

mode: str - rounding mode ("chop", "up", "down", "nearest_even")
discarded: str - string of discarded digits after the last kept digit
last_kept_digit: str - the last digit that is kept after rounding
base: int - base in which the digits are represented (e.g., 10 for decimal, 2 for binary)
is_negative: bool - True if the number is negative, False otherwise

eg: _should_increment("nearest_even", "500", "4", 10, False) -> True
eg: _should_increment("chop", "123", "4", 10, False) -> False
"""
def _should_increment(
    mode: str,
    discarded: str,
    last_kept_digit: str,
    base: int,
    is_negative: bool,
) -> bool: 
    # if discarded tail is effectively zero = no increment.
    if not discarded or not _has_nonzero_digits(discarded):
        return False

    if mode == "chop":
        return False

    # toward +infinity.
    if mode == "up":
        return not is_negative

    # toward -infinity.
    if mode == "down":
        return is_negative

    # round to nearest, ties to even.
    if mode == "nearest_even":
        half = base // 2
        first = _digit_to_value(discarded[0])

        if first > half:
            return True
        if first < half:
            return False

        # exact half with remaining tail.
        if _has_nonzero_digits(discarded[1:]):
            return True

        # exact tie: increment only if kept last digit is odd.
        return _digit_to_value(last_kept_digit) % 2 == 1

    raise ValueError("Unknown rounding mode.")

# ----------- PARSING FUNC -----------

""" 
func: validate and parse significant digits input
return (int): validated significant digits as an integer

digits: Any - input significant digits to validate and parse (can be str, int, etc.)

eg: _parse_digits("5") -> 5
eg: _parse_digits(10) -> 10
eg: _parse_digits(0) -> raises ValueError
eg: _parse_digits(17) -> raises ValueError
"""
def _parse_digits(digits: Any) -> int:
    # if boolean = not valid
    if isinstance(digits, bool):
        raise TypeError("Significant digits must be an integer from 1 to 16")

    # avoid silent truncation like int(3.7) -> 3
    if isinstance(digits, float) and not digits.is_integer():
        raise ValueError("Significant digits must be a whole integer from 1 to 16")

    try:
        parsed = int(digits)
    except (ValueError, TypeError) as exc:
        raise TypeError("Significant digits must be an integer from 1 to 16") from exc

    # check if parsed digits are within valid range (1 to MAX_SIGNIFICANT_DIGITS)
    if parsed < 1:
        raise ValueError("Significant digits must be at least 1")

    if parsed > MAX_SIGNIFICANT_DIGITS:
        raise ValueError(f"Significant digits must be at most {MAX_SIGNIFICANT_DIGITS}")

    # normalized digit count for all rounding methods
    return parsed

""" 
helper func: parse a decimal number input and return its components (sign, whole part, fractional part, and radix base)
return (tuple): tuple -> returns sign, whole part, fractional part, and base (10 for decimal)

number: str - input decimal number to parse

eg: _parse_decimal("123.45") -> ("", "123", "45", 10)
eg: _parse_decimal("-0.001") -> ("-", "0", "001", 10)
"""
def _parse_decimal(number: str) -> tuple[str, str, str, int]:  # int = radix base
    sign, _ = _split_sign(number)

    text = str(number).strip()

    try:
        value = Decimal(text)
    except InvalidOperation as exc:
        raise ValueError("Invalid decimal input.") from exc

    # invalid for special cases (NaN, Infinity)
    if not value.is_finite():
        raise ValueError("NaN and Infinity are not supported in rounding.")

    # split -> fixed-point decimal 
    magnitude = format(abs(value), "f")
    whole, _, frac = magnitude.partition(".")

    whole = whole.lstrip("0") or "0"

    # normalize 0
    if value == 0:
        frac = ""

    # base 10 = decimal parsing
    return sign, whole, frac, 10

""" 
helper func: parse a binary number input and return its components (sign, whole part, fractional part, and radix base)
return (tuple): tuple -> returns sign, whole part, fractional part, and base (2 for binary)

number: str - input binary number to parse

eg: _parse_binary("110.101") -> ("", "110", "101", 2)
eg: _parse_binary("-0.001") -> ("-", "0", "001", 2)
"""
def _parse_binary(number: str) -> tuple[str, str, str, int]:  # int = radix base
    sign, body = _split_sign(number)

    # check for multiple radix points or invalid characters
    if not body or body == ".":
        raise ValueError("Invalid binary input.")
    if body.count(".") > 1:
        raise ValueError("Binary input must contain at most one radix point.")
    if any(char not in "01." for char in body):
        raise ValueError("Binary input must use only 0, 1, and one radix point.")

    # split into whole and fractional parts
    whole, _, frac = body.partition(".")
    whole = (whole or "0").lstrip("0") or "0"

    # normalize 0
    if whole == "0" and not _has_nonzero_digits(frac):
        frac = ""

    # Base 2 = binary parsing.
    return sign, whole, frac, 2

""" 
func: parse input number based on specified format (decimal or binary) and return its components (sign, whole part, fractional part, and radix base)

return (tuple): tuple -> returns sign, whole part, fractional part, and base
"""
def _parse_number(number: str, input_format: str) -> tuple[str, str, str, int]:
    if input_format == "Decimal":
        return _parse_decimal(number)
    if input_format == "Binary":
        return _parse_binary(number)
    raise ValueError("Input format must be Decimal or Binary.")

""" 
func: split input sign from number text
return (tuple): tuple -> containing sign and unsigned number body

number: str - input number to validate and parse (decimal or binary)

eg: _split_sign("+123.45") -> ("", "123.45")
eg: _split_sign("-0.001") -> ("-", "0.001")
"""
def _split_sign(number: str) -> tuple[str, str]:
    raw = str(number).strip()

    if not raw:
        raise ValueError("Input number is empty.")

    if raw[0] == "-":
        return "-", raw[1:]

    if raw[0] == "+":
        return "", raw[1:]

    return "", raw

# ----------- BUILDING FUNC -----------

""" 
func: normalize the text representation of a number based on its sign, whole part, and fractional part
return (str): normalized text representation of the number

sign: str - sign of the number ("-" or "")
whole: str - whole part of the number (digits before the decimal point)
frac: str - fractional part of the number (digits after the decimal point)

eg: _normalized_text("-", "123", "45") -> "-123.45"
eg: _normalized_text("", "0", "") -> "0"
"""
def _normalized_text(sign: str, whole: str, frac: str) -> str:
    return f"{sign}{whole}" + (f".{frac}" if frac else "")


""" 
func: build a normalized text representation of a number from its sign, significant digits, and exponent
return (str): normalized text representation of the number

eg: _build_from_significant("-", "12345", 2) -> "-123.45"
"""
def _build_from_significant(sign: str, significant: str, exponent: int) -> str:
    # determine the index of the decimal point based on the exponent
    point_index = exponent + 1

    if point_index >= len(significant):
        # if decimal point = beyond length of significant digits -> pad with zeros
        whole = significant + ("0" * (point_index - len(significant)))
        frac = ""
    elif point_index > 0:
        # if decimal point = within significant digits -> split to whole & frac parts
        whole = significant[:point_index]
        frac = significant[point_index:]
    else:
        # if decimal point = before significant digits -> pad with zeros in frac part
        whole = "0"
        frac = ("0" * (-point_index)) + significant

    return _normalized_text(sign, whole, frac)

""" 
func: build an explanation of the rounding process based on the specified rounding mode, discarded digits, whether incremented, and sign of the number
return (str): explanation of the rounding process

mode: str - rounding mode ("chop", "up", "down", "nearest_even")
discarded: str - string of discarded digits after the last kept digit
incremented: bool - True if the last kept digit was incremented, False otherwise
is_negative: bool - True if the number is negative, False otherwise

eg: _build_explanation("nearest_even", "500", True, False) -> "Round-to-nearest selected the closer value; exact ties go to even."
"""
def _build_explanation(mode: str, discarded: str, incremented: bool, is_negative: bool) -> str:
    if not discarded:
        return "Input already fits the target significant digits."

    if mode == "chop":
        return "Chopping keeps the first significant digits and discards the rest."

    if mode == "up":
        if is_negative:
            return "Round up is toward +infinity, so negative values usually match chopping."
        return (
            "Round up is toward +infinity; non-zero discarded digits cause increment."
            if incremented
            else "No non-zero discarded digits, so value is unchanged."
        )

    if mode == "down":
        if not is_negative:
            return "Round down is toward -infinity, so positive values usually match chopping."
        return (
            "Round down is toward -infinity; negative values with discarded tail increase magnitude."
            if incremented
            else "No non-zero discarded digits, so value is unchanged."
        )

    if mode == "nearest_even":
        return (
            "Round-to-nearest selected the closer value; exact ties go to even."
            if incremented
            else "Kept digits were already nearest, or tie resolved to even without increment."
        )

    return ""

# ----------- HELPER FUNC -----------

"""
func: to check if discarded digits contain any non-zero digits
return (bool): true if any character in str is non-zero, false otherwise

text: str - input string to check for non-zero digits

eg: _has_nonzero_digits("0000") -> False
eg: _has_nonzero_digits("0001") -> True
"""
def _has_nonzero_digits(text: str) -> bool:
    return any(char != '0' for char in text)

"""
func: convert a character to its integer value
return (int): integer value of the character if valid (0-9), raises ValueError otherwise

char: str - input character to convert to integer

eg: _digit_to_value("5") -> 5
eg: _digit_to_value("a") -> raises ValueError
"""
def _digit_to_value(char: str) -> int:
    if "0" <= char <= "9":
        return ord(char) - ord("0")
    raise ValueError(f"Invalid digit character: {char}")

""" 
helper func: extract significant digits from whole and fractional parts
return (tuple): tuple -> returns exponent of first significant digit and the significant digits as a string

eg: _extract_significant_digits("123", "45") -> (2, "12345")
eg: _extract_significant_digits("0", "00123") -> (-3, "123")
"""
def _extract_significant_digits(whole: str, frac: str) -> tuple[int, str]:
    # if whole = non-zero, first significant digit starts in whole
    if whole != "0":
        return len(whole) - 1, whole + frac

    # for values < 1 -> find first non-zero fractional digit
    for idx, digit in enumerate(frac):
        if digit != "0":
            return -(idx + 1), frac[idx:]

    # 0 fallback
    return 0, "0"

