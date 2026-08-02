"""
CSARCH2 S03 Case Study 1: Decimal 64-bit Floating-Point Machine
Group 9
"""

import streamlit as st
import conversion_helpers as conv
import arithmetic_helpers as ar
import rounding_helpers as rnd

# SCENARIO 1: DECIMAL TO DECIMAL-BASED DOUBLE-PRECISION REPRESENTATION
def decimal_to_dp_tab():
    """Render Decimal -> Double Precision tab."""

    st.header("Convert Decimal to Double Precision")

    st.markdown(
        """
        Converts input into an **IEEE-754 double-precision floating-point representation**. 
        """
    )

    with st.expander("More insights"):
        st.markdown(
            """
            #### Representable Range

            This follows the IEEE-754 double-precision format, which uses:

            - **1 sign bit**
            - **11 exponent bits**
            - **52 fraction bits**

            The range boundaries were enforced using Python's `sys.float_info` values:

            - `sys.float_info.max` is the **largest magnitude representable**
              (`~1.8e+308`). Values beyond this are represented as a 
              fixed finite binary representing signed **Infinity**.

            - `sys.float_info.min` is the **smallest magnitude representable**
              (`~2.23e-308`). Values below this are denormalized, where the exponent
              field becomes zero and the fraction stores the remaining precision.

            #### Decimal to Binary Process

            1. Determine the sign bit
            2. Convert the decimal magnitude into binary:
                - Whole portion is converted directly via `int()`.
                - Fraction portion is computed thru manual multiplication by 2.
            3. Normalize binary into: `1.xxxxx × 2^exponent`
            4. Compute the biased exponent (e'): `exponent + 1023`
            5. Generate the fraction field:
                - Up to 1200 fractional bits are computed to make sure enough bits can be generated for smaller values
                - Only the first 52 bits are stored
                - Remaining bits are used for rounding

            6. Combine the sign (1 bit) + exponent (11 bits) + fraction (52 bits) -> binary result
            
            #### Special Cases
            
            ##### Signed Zeroes
            This calculator supports positive zero (`+0`) and negative zero (`-0`).

            Although both values have the same numerical value, they are stored with
            different sign bits:
            
            ```
            +0 -> 0 00000000000 0000000000000000000000000000000000000000000000000000
            -0 -> 1 00000000000 0000000000000000000000000000000000000000000000000000
            ```
            
            ##### Overflow (Infinity)

            Overflow occurs when input exceeds the largest magnitude possible.

            Example:
            ```
            1e309  -> +Infinity
            -1e309 -> -Infinity
            ```

            IEEE-754 infinity representation:

            ```
            sign | 11111111111 | 000...000
            ```

            ##### Underflow (Denormalized)

            Values smaller than the smallest magnitude possible, but still representable
            are **denormalized**:
            - Peg exponent to -1022 and scale the value appropriately (`0.xxx * 2^-1022`)
            - Set biased exponent (e') to zero
            - Store significant bits directly in the fraction field
            

            ##### NaN (qNaN)

            Invalid inputs, like non-decimal strings, are represented as **NaN**. We use a fixed quiet NaN representation:

            ```
            0 11111111111 1111111111111111111111111111111111111111111111111111
            ```

            This contains:

            ```
            Sign = 0
            Exponent = 11111111111
            Fraction = xxx...xxxx
            ```

            where the exponent MSb is `1`, which identifies a quiet NaN.
            """
        )

    st.subheader("Input")

    st.write(
        "The **decimal input** allows usual decimal values (`128.0`), "
        "scientific notation (`1.28e-2`), and signed inputs (`+12.8`, `-0`)."
    )

    with st.form(key="decimal_to_dp"):

        number = st.text_input(
            label="Decimal Number",
            placeholder="Enter a decimal number"
        )

        submit = st.form_submit_button(label="Convert")

    if submit and number:

        binary, special_case = conv.dec_to_dp(number)

        hexadecimal = conv.bin_to_hex(
            binary,
            zero_extend=True,
            upper=True
        )

        st.subheader("Output")

        st.write(
            "For the conversion process, **round to nearest, ties to even** "
            "rounding is used."
        )

        with st.container(border=True):

            if special_case:
                st.write("**Special Case**")

                colors = {
                    "Overflow": "red",
                    "Underflow": "orange",
                    "NaN": "gray"
                }

                st.badge(
                    special_case,
                    color=colors.get(special_case, "blue")
                )

            st.write("**IEEE-754 Binary**")
            st.code(conv.format_bin(binary), language="text")
            st.code(conv.format_dp(binary), language="text")

            st.write("**IEEE-754 Hexadecimal**")
            st.code(
                conv.format_hex(hexadecimal, upper=True),
                language="text"
            )

# SCENARIO 2: ROUNDING METHODS
def rounding_tab():
    """Render rounding methods tab."""

    st.header("Rounding Methods")

    with st.form(key="rounding"):

        input_format = st.radio(
            "Input Format",
            ["Decimal", "Binary"],
            horizontal=True
        )

        number = st.text_input(
            "Number",
            placeholder="Enter a number"
        )

        digits = st.number_input(
            "Target Number of Digits",
            min_value=1,
            step=1
        )

        submit = st.form_submit_button("Round")

    if submit:
        # Validate inputs are not empty
        if not operand1 or not operand2:
            st.warning("Please enter both operands.")
            return

        is_hex = (operand_format == "IEEE Hexadecimal")

        if operation == "/":
            # Call your new Division function!
            result = ar.divide_grs(operand1, operand2, is_hex)
            
            st.subheader("Division Result")
            
            # Display Special Case Badge if applicable
            if result["special_case"]:
                st.warning(f"**Special Case Triggered:** {result['special_case']}")
            
            # Formatted Output Display
            with st.container(border=True):
                st.write("**Decimal Result:**")
                st.code(result["final_dec"], language="text")
                
                st.write("**IEEE-754 Binary:**")
                # Using Kimberly/Adolfo's formatter for proper spacing
                st.code(conv.format_bin(result["final_bin"]), language="text")
                st.code(conv.format_dp(result["final_bin"]), language="text")
                
                st.write("**IEEE-754 Hexadecimal:**")
                st.code(conv.format_hex(result["final_hex"], upper=True), language="text")
                
            # Expandable Step-by-Step GRS Process
            with st.expander("View Step-by-Step GRS Process", expanded=True):
                for step in result["steps"]:
                    st.text(step)
                    
        elif operation == "-":
            st.info("Subtraction is assigned to Mikael! Waiting for his module.")


# SCENARIO 3: ARITHMETIC OPERATIONS
def arithmetic_tab():
    """Render arithmetic operations tab."""

    st.header("Arithmetic Operations (GRS Method)")

    with st.form(key="arithmetics"):

        operand_format = st.radio(
            "Operand Format",
            ["Decimal", "IEEE Hexadecimal"],
            horizontal=True
        )

        col1, col2, col3 = st.columns([2, 1, 2])

        with col1:
            operand1 = st.text_input(
                "Operand 1",
                placeholder="Enter first operand"
            )

        with col2:
            operation = st.selectbox(
                "Operation",
                [
                    "-",
                    "/"
                ]
            )

        with col3:
            operand2 = st.text_input(
                "Operand 2",
                placeholder="Enter second operand"
            )

        submit = st.form_submit_button("Compute")

    if submit:
        # Validate inputs are not empty
        if not operand1 or not operand2:
            st.warning("Please enter both operands.")
            return

        is_hex = (operand_format == "IEEE Hexadecimal")

        if operation == "/":
            # Call your new Division function!
            result = ar.divide_grs(operand1, operand2, is_hex)
            
            st.subheader("Division Result")
            
            # Display Special Case Badge if applicable
            if result["special_case"]:
                st.warning(f"**Special Case Triggered:** {result['special_case']}")
            
            # Formatted Output Display
            with st.container(border=True):
                st.write("**Decimal Result:**")
                st.code(result["final_dec"], language="text")
                
                st.write("**IEEE-754 Binary:**")
                # Using Kimberly/Adolfo's formatter for proper spacing
                st.code(conv.format_bin(result["final_bin"]), language="text")
                st.code(conv.format_dp(result["final_bin"]), language="text")
                
                st.write("**IEEE-754 Hexadecimal:**")
                st.code(conv.format_hex(result["final_hex"], upper=True), language="text")
                
            # Expandable Step-by-Step GRS Process
            with st.expander("View Step-by-Step GRS Process", expanded=True):
                for step in result["steps"]:
                    st.text(step)
                    
        elif operation == "-":
            st.info("Subtraction is assigned to Mikael! Waiting for his module.")


def app():
    """Render web application."""

    st.title("Decimal 64-bit Floating-Point Machine")
    st.write("IEEE-754 decimal double-precision operations!")

    tab1, tab2, tab3 = st.tabs(
        [
            "Decimal → Double Precision",
            "Rounding Methods",
            "Arithmetic Operations"
        ]
    )

    with tab1:
        decimal_to_dp_tab()

    with tab2:
        rounding_tab()

    with tab3:
        arithmetic_tab()


if __name__ == "__main__":
    app()
    
    # conv.test_case_dp()