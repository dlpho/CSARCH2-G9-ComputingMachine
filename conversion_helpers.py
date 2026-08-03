
from decimal import Decimal, InvalidOperation, localcontext
from typing import Optional
import struct
import sys

SMALLEST_MAG = sys.float_info.min # 1.0x2^-1022 = 2.23x10^-308
LARGEST_MAG = sys.float_info.max # 1.1...1x2^1023 = 1.18x10^
MAX_FRAC_BITS = 1200 # how many frac bits to generate 

def format_bin(binary: str, sign_extend: bool = False, pad: bool = True):
    """Formats binary by groups of 4 separated by spaces.

    This function optionally pads the binary string to the next multiple of
    4 bits using either zero-extension or sign-extension, then groups the
    bits into nibbles separated by spaces. If padding is disabled, grouping
    is performed from right to left without modifying the input length.

    Args:
        binary (str): A string of binary digits, for example "1001011".
        sign_extend (bool): Whether to use sign-extension instead of
            zero-extension when padding. Defaults to False.
        pad (bool): Whether to pad the binary string to a multiple of
            4 bits before grouping. Defaults to True.

    Returns:
        str: The formatted binary string, for example `"0100 1011"`.
    """
    if not binary:
        return ""

    if pad:
        target_len = ((len(binary) + 3) // 4) * 4

        if sign_extend:
            binary = binary.rjust(target_len, binary[0])
        else:
            binary = binary.zfill(target_len)

        return " ".join(binary[i:i+4] for i in range(0, len(binary), 4))

    groups = []
    while binary:
        groups.append(binary[-4:])
        binary = binary[:-4]

    return " ".join(reversed(groups))


def format_hex(hexadecimal: str, upper: bool = False,
               sign_extend: bool = False, pad: bool = True) -> str:
    """Formats hexadecimal by groups of 4 separated by spaces.

    This function optionally pads the hexadecimal string to the next multiple
    of 4 hexadecimal digits using either zero-extension or sign-extension,
    then groups the digits into sets of four separated by spaces. If padding
    is disabled, grouping is performed from right to left without modifying
    the input length.

    Args:
        hexadecimal (str): A string of hexadecimal digits, for example
            `"123cafe"`.
        upper (bool): Whether to return uppercase hexadecimal letters.
            Defaults to False.
        sign_extend (bool): Whether to use sign-extension instead of
            zero-extension when padding. Defaults to False.
        pad (bool): Whether to pad the hexadecimal string to a multiple
            of 4 digits before grouping. Defaults to True.

    Returns:
        str: The formatted hexadecimal string, for example `"0123 cafe"`.
    """
    if not hexadecimal:
        return ""

    if pad:
        target_len = ((len(hexadecimal) + 3) // 4) * 4

        if sign_extend:
            msn = hexadecimal[0].upper()
            pad_char = "F" if msn in "89ABCDEF" else "0"
            hexadecimal = hexadecimal.rjust(target_len, pad_char)
        else:
            hexadecimal = hexadecimal.zfill(target_len)

        formatted = " ".join(
            hexadecimal[i:i+4]
            for i in range(0, len(hexadecimal), 4)
        )
    else:
        groups = []
        while hexadecimal:
            groups.append(hexadecimal[-4:])
            hexadecimal = hexadecimal[:-4]

        formatted = " ".join(reversed(groups))

    return formatted.upper() if upper else formatted.lower()

def format_dp(binary: str):
    """Formats an IEEE 754 double-precision binary representation.

    This function separates a 64-bit IEEE 754 binary string into its sign,
    exponent, and fraction fields for easier reading. The exponent and
    fraction are grouped into sets of 4 bits without altering their lengths.

    Args:
        binary (str): A 64-bit IEEE 754 binary string.

    Returns:
        str: A formatted multi-line string showing the sign, exponent,
            and fraction fields.
    """
    sign = binary[0]
    exponent = format_bin(binary[1:12], pad=False)
    fraction = format_bin(binary[12:], pad=False)

    return (
        f"Sign     : {sign}\n"
        f"Exponent : {exponent}\n"
        f"Fraction : {fraction}"
    )


def bin_to_hex(binary: str, zero_extend: bool = False, upper: bool = False):
    """Converts binary to hexadecimal.

    Args:
        binary (str): A binary string.
        zero_extend (bool): Whether to zero-pad the result to 16 hexadecimal
            digits. Defaults to False.
        upper (bool): Whether to return uppercase hexadecimal letters.
            Defaults to False.

    Returns:
        str: The hexadecimal representation without the ``0x`` prefix.
    """
    result =  hex(int(binary, 2)).replace("0x", "")
    if zero_extend:
        result = result.zfill(16)
    if upper:
            result = result.upper()
    return result

def hex_to_bin(hexadecimal: str, zero_extend: bool = False):
    """Converts hexadecimal to binary.
    
    Args:
        hexadecimal (str): A hexadecimal string.
        zero_extend (bool): Whether to zero-pad the result to 64 binary
            digits. Defaults to False.

    Returns:
        str: The binary representation without the ``0b`` prefix.
    """
    result = bin(int(hexadecimal, 16)).replace("0b","")
    if zero_extend:
        result = result.zfill(64)
    return result

def is_special_case(input: str | float):
    """Identifies the special case based on IEEE-754 double precision representation.

    Args:
        input (str or float): The value to test special case. 

    Returns:
        str or None: "NaN" (not a number), "Overflow" (too large to represent properly), "Underflow" (too small to represent properly), or None if it is a valid representable value. 
    """
    try: 
        input = Decimal(input)
        
        if input.is_nan():
            return "NaN"
        if input == 0.0:
            return None
        if abs(input) > LARGEST_MAG:
            return "Overflow"
        if abs(input) < SMALLEST_MAG:
            return "Underflow"
    except (InvalidOperation, ValueError, TypeError):
        return "NaN"
    
    # representable 
    return None

def dec_to_bin(decimal: Decimal):
    """Converts a non-negative Decimal to binary with a radix point."""

    # divide decimal to whole and frac
    whole = int(decimal)
    frac = decimal - whole

    # if already scaled (0.xxx or 1.xxx), keep whole as-is
    if whole <= 1:
        binary = f"{whole}."
    else:
        # general case: convert whole part to binary with bin()
        binary = bin(whole)[2:] + "."

    # convert fractional part
    i = 0
    while i < MAX_FRAC_BITS and frac != 0:
        frac *= 2

        bit = int(frac)
        binary += str(bit)

        frac -= bit
        i += 1

    binary += "0" * (MAX_FRAC_BITS - i)

    return binary

def find_binary_exp(decimal: Decimal) -> int:
    """Returns the unbiased binary exponent of a positive Decimal."""

    # disregard zero
    if decimal == 0:
        return 0

    # manually convert to binary
    with localcontext() as ctx:
        ctx.prec = 2000

        exp = 0
        value = decimal

        while value >= 2:
            value /= 2
            exp += 1

        while value < 1:
            value *= 2
            exp -= 1

    return exp


# def normalize_bin(binary: str):
#     """Normalizes a binary value into IEEE 754 normalized form.

#     This function shifts the binary radix point to produce a normalized
#     significand of the form 1.xxxx and computes the corresponding unbiased
#     exponent.

#     Args:
#         binary (str): A binary string containing a radix point.

#     Returns:
#         tuple[int, str]: The unbiased exponent and the normalized binary
#             significand.
#     """
#     whole, frac = binary.split(".")

#     if whole == "0":
#         # handle 0 case
#         if "1" not in frac:
#             return 0, "0.0"

#         # move right, normalize and count moves -> exponent
#         first_one = frac.index("1")
#         exponent = -(first_one + 1)
#         normalized = "1." + frac[first_one + 1:]

#     # move left, normalize and count moves -> exponent
#     else:
#         exponent = len(whole) - 1
#         normalized = "1." + whole[1:] + frac[:52]

#     return exponent, normalized

# def denormalize_bin(binary: str, exp: int):
#     """Denormalizes a normalized binary significand for subnormal numbers.

#     This function shifts the significand to produce the denormalized form
#     used by IEEE-754 subnormal numbers while pegging the exponent at -1022.

#     Assumes the input has no sign bit and is already normalized.

#     Args:
#         binary (str): The normalized binary significand.
#         exp (int): The unbiased exponent of the normalized value.

#     Returns:
#         str: The denormalized binary significand with a radix point.
#     """

#     # compute how many shifts til -1022
#     shift = -1022 - exp
    
#     # shift left and add zeros if need
#     frac = binary.split(".")[1] 
#     signif = "1" + frac
#     shifted = "0" * shift + signif
    
#     # result should be 0.signif where signif may be zero padded
#     denormalized = "0." + shifted
#     return denormalized
    
def round_fraction(frac: str, bits: int = 52):
    """Rounds binary fraction using IEEE-754 round-to-nearest-even."""

    if len(frac) <= bits:
        return frac.ljust(bits, "0"), False

    kept = frac[:bits]
    guard = frac[bits]
    remaining = frac[bits + 1:]

    if guard == "1" and ("1" in remaining or kept[-1] == "1"):
        value = int(kept, 2) + 1

        if value >= (1 << bits):
            return "0" * bits, True

        kept = bin(value)[2:].zfill(bits)

    return kept, False

def dec_to_dp(input: str) -> tuple[str, Optional[str]]:
    """Converts a decimal value to its IEEE-754 double-precision representation.

    This function converts a decimal string into its 64-bit IEEE-754
    double-precision binary representation. It also detects special cases
    such as NaN, overflow, and underflow, and returns the corresponding
    representation.

    Args:
        input (str): The decimal value to convert.

    Returns:
        ans_bin (str): The 64-bit IEEE-754 binary representation.
        special_case (str or None): The detected special case ("NaN", "Overflow", "Underflow"), or None if the value is representable.
    """
    
    # check for special case / validity
    special_case = is_special_case(input)
    
    # return a qNaN result
    if special_case == "NaN":
        ans_bin = "0" + "1" * 63
        # print(f"qNaN: {ans_bin[0]} {ans_bin[1:12] } {ans_bin[12:] }")
        return ans_bin, special_case
    
    # convert input to decimal, get sign
    decimal = Decimal(input)
    sign = str(int(decimal.is_signed()))
    
    # return if infinity / overflow
    if special_case == "Overflow":
        ans_bin = frac = sign + "1" * 11 +  "0" * 52
        # print(f"Infinity: {ans_bin[0]} {ans_bin[1:12] } {ans_bin[12:] }")
        return ans_bin, special_case
    
    # get magnitude only
    magnitude = abs(decimal)

    # check for zero case, return result
    if magnitude == 0:
        ans_bin = sign + "0" * 63
        # print(f"Zero: {ans_bin[0]} {(ans_bin[1:12])} {ans_bin[12:] }")
        return ans_bin, special_case

    # find binary exponent
    exp = find_binary_exp(magnitude)

    with localcontext() as ctx:
        ctx.prec = 2000

        # normal number
        if exp >= -1022:
            # scale mag to make rep -> 1.xxx * 2^exp
            scaled = magnitude / (Decimal(2) ** exp)
            exponent_bits = exp + 1023 # get exp prime

        # denormalized number
        else:
            # peg to -1022 and exponent = 0
            # scale mag to 0.xxx * 2^-1022
            scaled = magnitude / (Decimal(2) ** -1022)
            exponent_bits = 0

    binary = dec_to_bin(scaled)

    # normal numbers -> remove the implicit leading 1 (1.xxx * 2^exp).
    # subnormal numbers -> no implicit leading 1 (0.xxx * 2^exp).
    frac = binary.split(".")[1]
    normalized = binary

    # print(f"Normalized: {'-' if sign == '1' else ''}{normalized}")

    # # Handle overflow after exponent computation
    # if special_case == "Overflow":
    #     exponent_bits = 2047
    #     frac = "0" * 52
    #     print(f"Infinity: {'-' if sign == '1' else ''}1.{'0'*52}")

    # Convert exponent to binary
    exp_p = bin(exponent_bits)[2:].zfill(11)

    # IEEE fraction field is exactly 52 bits
    frac, carry = round_fraction(frac, 52)

    # rounding overflow
    if carry:
        exponent_bits += 1
        frac = "0" * 52 # TODO: check whether rtn-tte rounding is needed
    frac = frac[:52].ljust(52, "0")

    # print(f"Breakdown: {sign} {exp_p} {frac}")

    # assemblage
    ans_bin = sign + exp_p + frac
    return ans_bin, special_case
    

#### checkers, dont use for calc just for testing    
    

def test_dp(decimal: str):
    """Returns the IEEE-754 double-precision representation produced by Python."""

    special_case = is_special_case(decimal)

    try:
        value = float(Decimal(decimal))

        packed = struct.pack("!d", value)
        integer_representation = struct.unpack("!Q", packed)[0]
        binary = f"{integer_representation:064b}"

        return binary, special_case

    except OverflowError:
        # Match Python's IEEE-754 infinity representation
        sign = "1" if Decimal(decimal).is_signed() else "0"
        binary = sign + "1" * 11 + "0" * 52
        return binary, "Overflow"

    except (InvalidOperation, ValueError, TypeError):
        # Quiet NaN fixed return
        return "0" + "1" * 11 + "1" + "1" * 51, "NaN"

def test_case_dp(fail_only: bool = False):
    cases = [
        "0",
        "-0",
        "8",
        "65.50",
        "0.0005",
        "1024",
        "12.825e-1",
        "3.141592654",
        "2.718281828",
        "30432.3432",
        "123456789.987654321",
        "0.3",
        "2.23e-308",
        "-2.23e-308",
        "1.18e+308",
        "-1.18e+308",
        "0.02e-310",
        "-4.23e-319",
        "6.23e+310",
        "-1.28e+310",
        "abcdefg",
        "0x123caf",
        ""
    ]
    
    passed_cases = 0
    for inp in cases:
        
        # manual conversion
        my_bin, my_sp = dec_to_dp(inp)
        my_hex = bin_to_hex(my_bin, zero_extend=True)

        # unpack with python struct
        ref_bin, ref_sp = test_dp(inp)
        ref_hex = bin_to_hex(ref_bin, zero_extend=True)
        
        # all output match expected
        passes = my_bin == ref_bin and my_hex.lower() == ref_hex.lower() and my_sp == ref_sp
        
        # add count if passed case
        if passes:
            passed_cases += 1
        
        # if show only failures, skip printing
        if fail_only and passes:
            continue
        
        print("=" * 80)
        print(f"Input: {inp}")
        print(f"Actual Special Case  : {my_sp}")
        print(f"Expected Special Case: {ref_sp}")

        print(f"Actual Bin  : {my_bin}")
        print(f"Expected Bin: {ref_bin}")

        print(f"Actual Hex   : {my_hex}")
        print(f"Expected Hex : {ref_hex}")
        print(f"Pass: {passes}")
    
    # total statistics
    print("=" * 80)
    print(f"TOTAL CASES : {len(cases)}")
    print(f"TOTAL PASSED: {passed_cases}")
    print(f"TOTAL FAILED: {len(cases) - passed_cases}")
    print("=" * 80)
    
    