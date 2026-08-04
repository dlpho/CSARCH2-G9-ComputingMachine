"""
arithmetic_helpers.py
Handles arithmetic operations (Division and Subtraction) using the GRS method.
"""
from decimal import Decimal
import conversion_helpers as conv

def divide_grs(op1: str, op2: str, is_hex: bool) -> dict:
    """
    Performs division using the Guard, Round, and Sticky (GRS) bits method.
    
    Args:
        op1 (str): The dividend (first operand).
        op2 (str): The divisor (second operand).
        is_hex (bool): True if inputs are IEEE Hexadecimal, False if Decimal.
        
    Returns:
        dict: A dictionary containing:
            - "steps": list of str detailing the step-by-step GRS process
            - "final_dec": str representing the final decimal value
            - "final_bin": str representing the 64-bit IEEE binary
            - "final_hex": str representing the 16-character IEEE hex
            - "special_case": str or None (e.g., "Divide by Zero", "NaN")
    """
    steps = []
    
    # STEP 1: Parse Inputs
    steps.append(f" STEP 1: PARSE INPUTS ")
    
    # Helper function to convert either format to a 64-bit binary string
    def get_binary(op_str: str, is_hex_input: bool):
        if is_hex_input:
            # Convert hex to binary and pad to 64 bits
            return conv.hex_to_bin(op_str, zero_extend=True)
        else:
            # Convert decimal to binary double precision
            bin_str, _ = conv.dec_to_dp(op_str)
            return bin_str

    # Convert both operands to 64-bit binary
    bin1 = get_binary(op1, is_hex)
    bin2 = get_binary(op2, is_hex)

    # Extract Sign, Exponent, and Fraction for Operand 1
    sign1, exp1, frac1 = bin1[0], bin1[1:12], bin1[12:]
    steps.append(f"Operand 1 (Dividend): Sign={sign1}, Exp={exp1}, Frac={frac1}")
    
    # Extract Sign, Exponent, and Fraction for Operand 2
    sign2, exp2, frac2 = bin2[0], bin2[1:12], bin2[12:]
    steps.append(f"Operand 2 (Divisor) : Sign={sign2}, Exp={exp2}, Frac={frac2}")

        
    # STEP 2: Handle Special Cases
    # TODO: Check for Divide by Zero, NaN, Infinity, and Subnormals
    # Example: if op2 == 0: return early with special_case = "Divide by Zero"
    steps.append(" STEP 2: HANDLE SPECIAL CASES ")
    
    # Calculate the final sign bit early (Sign is always Op1 XOR Op2)
    final_sign = str(int(sign1) ^ int(sign2))
    steps.append(f"Final Sign bit computed: {sign1} XOR {sign2} = {final_sign}")
    
    # Helper to identify IEEE-754 special types based on bits
    def get_type(exp, frac):
        if exp == "1" * 11:
            return "NaN" if "1" in frac else "Infinity"
        if exp == "0" * 11:
            return "Zero" if frac == "0" * 52 else "Denormal"
        return "Normal"

    type1 = get_type(exp1, frac1)
    type2 = get_type(exp2, frac2)
    steps.append(f"Operand 1 Type: {type1} | Operand 2 Type: {type2}")
    
    # Standard 64-bit binary representations for special returns
    qnan_bin = "0" + "1" * 11 + "1" + "0" * 51  # Quiet NaN
    inf_bin = final_sign + "1" * 11 + "0" * 52  # Infinity
    zero_bin = final_sign + "0" * 11 + "0" * 52 # Zero
    
    # Helper to pack the early return dictionary
    def pack_special(bin_val, special_msg):
        steps.append(f"Triggered Special Case: {special_msg}")
        hex_val = conv.bin_to_hex(bin_val, zero_extend=True, upper=True)
        return {
            "steps": steps,
            "final_dec": special_msg,
            "final_bin": bin_val,
            "final_hex": hex_val,
            "special_case": special_msg
        }

    # Evaluate IEEE-754 Special Division Rules
    if type1 == "NaN" or type2 == "NaN":
        return pack_special(qnan_bin, "NaN")
    
    if type1 == "Zero" and type2 == "Zero":
        return pack_special(qnan_bin, "NaN (0 / 0)")
        
    if type1 == "Infinity" and type2 == "Infinity":
        return pack_special(qnan_bin, "NaN (Infinity / Infinity)")
        
    if type2 == "Zero": # Divide by zero handling
        return pack_special(inf_bin, "Divide by Zero (Infinity)")
        
    if type1 == "Infinity":
        return pack_special(inf_bin, "Infinity")
        
    if type1 == "Zero" or type2 == "Infinity":
        return pack_special(zero_bin, "Zero")

    # STEP 3: Compute Sign and Exponent
    # TODO: New Sign = Sign1 XOR Sign2
    # TODO: New Exponent = Exp1 - Exp2 + Bias (1023)
    # STEP 3: Compute Exponent
    steps.append(" STEP 3: COMPUTE EXPONENT ")
    
    # Calculate unbiased exponents
    unbiased_exp1 = int(exp1, 2) - 1023 if type1 == "Normal" else -1022
    unbiased_exp2 = int(exp2, 2) - 1023 if type2 == "Normal" else -1022
    
    # Calculate new tentative unbiased exponent
    new_unbiased_exp = unbiased_exp1 - unbiased_exp2
    steps.append(f"Unbiased Exp 1: {unbiased_exp1} | Unbiased Exp 2: {unbiased_exp2}")
    steps.append(f"Tentative New Unbiased Exp: {unbiased_exp1} - ({unbiased_exp2}) = {new_unbiased_exp}")

    # STEP 4: Divide Significands & Calculate GRS Bits
    steps.append(" STEP 4: DIVIDE SIGNIFICANDS & GET GRS BITS ")
    
    # Append the implicit bit (1 for Normal, 0 for Denormal)
    m1_str = ("1" if type1 == "Normal" else "0") + frac1
    m2_str = ("1" if type2 == "Normal" else "0") + frac2
    
    m1_val = int(m1_str, 2)
    m2_val = int(m2_str, 2)
    
    # To get 55 bits for the quotient (1 implicit + 52 fraction + Guard + Round),
    # we shift the dividend left by 54 bits before doing integer division.
    shift_amount = 54
    shifted_m1 = m1_val << shift_amount
    
    quotient = shifted_m1 // m2_val
    remainder = shifted_m1 % m2_val
    
    q_bin = bin(quotient)[2:]
    s_bit = 1 if remainder != 0 else 0
    
    steps.append(f"Dividend shifted left by {shift_amount} bits.")
    steps.append(f"Raw Binary Quotient: {q_bin}")

    # STEP 5: Normalize the Result
    steps.append(" STEP 5: NORMALIZE RESULT ")
    
    if len(q_bin) == 55:
        # m1 >= m2, quotient already has 55 bits, no shift needed
        norm_q = q_bin
    else:
        # m1 < m2, quotient has 54 bits. Shift left by 1 and adjust exponent.
        norm_q = q_bin + "0"
        new_unbiased_exp -= 1
        steps.append("Quotient MSB was 0. Shifted left by 1 and decremented exponent.")
        
    steps.append(f"Normalized Quotient: {norm_q}")
    steps.append(f"Adjusted Unbiased Exp: {new_unbiased_exp}")
    
    implicit_bit = norm_q[0]
    frac_bits = norm_q[1:53]
    g_bit = norm_q[53]
    r_bit = norm_q[54]
    
    steps.append(f"Implicit Bit: {implicit_bit}")
    steps.append(f"Fraction (52 bits): {frac_bits}")
    steps.append(f"Guard (G): {g_bit}, Round (R): {r_bit}, Sticky (S): {s_bit}")

    # STEP 6: Apply Rounding (Round-to-Nearest, Ties-to-Even)
    steps.append(" STEP 6: APPLY ROUNDING ")
    round_up = False
    
    if g_bit == "1":
        if r_bit == "1" or str(s_bit) == "1":
            round_up = True
            steps.append("G=1 and (R=1 or S=1). Rounding UP.")
        else:
            # Tie case: G=1, R=0, S=0. Check the Least Significant Bit (LSB)
            if frac_bits[-1] == "1":
                round_up = True
                steps.append("Tie! LSB is 1. Rounding UP to make it even.")
            else:
                steps.append("Tie! LSB is 0. Rounding DOWN to keep it even.")
    else:
        steps.append("G=0. Rounding DOWN.")
        
    if round_up:
        frac_val = int(frac_bits, 2) + 1
        # Check if rounding caused the fraction to overflow (e.g., all 1s turning to 0s)
        if frac_val >= (1 << 52):
            frac_bits = "0" * 52
            new_unbiased_exp += 1
            steps.append("Fraction overflowed during rounding. Exponent incremented.")
        else:
            frac_bits = bin(frac_val)[2:].zfill(52)

    # STEP 7: Pack Final Result
    steps.append(" STEP 7: PACK FINAL RESULT ")
    
    # Compute Final Biased Exponent
    biased_exp = new_unbiased_exp + 1023
    
    # Check for Overflow/Underflow limits after rounding
    if biased_exp >= 2047:
        steps.append("Exponent overflow! Result is Infinity.")
        return pack_special(final_sign + "1"*11 + "0"*52, "Overflow")
    elif biased_exp <= 0:
        steps.append("Exponent underflow! Handling as subnormal/zero.")
        # Denormalize the fraction based on how far below 1 the biased exp is
        shift = 1 - biased_exp
        biased_exp = 0
        if shift > 53:
            frac_bits = "0" * 52
        else:
            denorm_val = int("1" + frac_bits, 2) >> shift
            frac_bits = bin(denorm_val)[2:].zfill(52)
    
    final_exp = bin(biased_exp)[2:].zfill(11)
    final_bin = final_sign + final_exp + frac_bits
    final_hex = conv.bin_to_hex(final_bin, zero_extend=True, upper=True)
    
    # Convert final binary back to decimal float for the UI using struct
    import struct
    try:
        final_dec = str(struct.unpack('!d', struct.pack('!Q', int(final_bin, 2)))[0])
    except OverflowError:
        final_dec = "Infinity"
        
    steps.append(f"Final Assembled Binary: {final_bin}")
    
    return {
        "steps": steps,
        "final_dec": final_dec,
        "final_bin": final_bin,
        "final_hex": final_hex,
        "special_case": None
    }