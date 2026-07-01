"""8051 ALU: arithmetic, logic, rotate, and flag computation."""

from .memory import PSW_CY, PSW_AC, PSW_OV, PSW_P


class ALU:
    """8-bit ALU implementing all 8051 operations."""

    @staticmethod
    def _parity(v: int) -> int:
        """Compute 8051 parity bit (1 if odd number of 1s)."""
        v &= 0xFF
        v ^= v >> 4
        v ^= v >> 2
        v ^= v >> 1
        return v & 1

    @staticmethod
    def _update_psw_add(psw: int, a: int, b: int, carry_in: int, result: int) -> int:
        """Update PSW after ADD/ADDC."""
        # CY: carry out of bit 7
        if result > 0xFF:
            psw |= (1 << PSW_CY)
        else:
            psw &= ~(1 << PSW_CY)
        # AC: carry out of bit 3
        if ((a & 0x0F) + (b & 0x0F) + carry_in) > 0x0F:
            psw |= (1 << PSW_AC)
        else:
            psw &= ~(1 << PSW_AC)
        # OV: carry into bit 7 XOR carry out of bit 7
        carry_bit6 = ((a & 0x7F) + (b & 0x7F) + carry_in) > 0x7F
        carry_bit7 = result > 0xFF
        if carry_bit6 ^ carry_bit7:
            psw |= (1 << PSW_OV)
        else:
            psw &= ~(1 << PSW_OV)
        # P
        if ALU._parity(result & 0xFF):
            psw |= (1 << PSW_P)
        else:
            psw &= ~(1 << PSW_P)
        return psw

    @staticmethod
    def _update_psw_sub(psw: int, a: int, b: int, borrow_in: int, result: int) -> int:
        """Update PSW after SUBB."""
        # CY: borrow (set if result < 0)
        if a < (b + borrow_in):
            psw |= (1 << PSW_CY)
        else:
            psw &= ~(1 << PSW_CY)
        # AC: borrow from bit 4 into bit 3
        if (a & 0x0F) < ((b & 0x0F) + borrow_in):
            psw |= (1 << PSW_AC)
        else:
            psw &= ~(1 << PSW_AC)
        # OV: borrow into bit 7 XOR borrow out of bit 7
        borrow_bit6 = (a & 0x7F) < ((b & 0x7F) + borrow_in)
        borrow_bit7 = a < (b + borrow_in)
        if borrow_bit6 ^ borrow_bit7:
            psw |= (1 << PSW_OV)
        else:
            psw &= ~(1 << PSW_OV)
        # P
        if ALU._parity(result & 0xFF):
            psw |= (1 << PSW_P)
        else:
            psw &= ~(1 << PSW_P)
        return psw

    # ===== Arithmetic =====

    @staticmethod
    def add(a: int, b: int, psw: int) -> tuple[int, int]:
        """ADD A, src — result, new_psw."""
        result = a + b
        return result & 0xFF, ALU._update_psw_add(psw, a, b, 0, result)

    @staticmethod
    def addc(a: int, b: int, psw: int) -> tuple[int, int]:
        """ADDC A, src — result, new_psw."""
        cy = 1 if (psw & (1 << PSW_CY)) else 0
        result = a + b + cy
        return result & 0xFF, ALU._update_psw_add(psw, a, b, cy, result)

    @staticmethod
    def subb(a: int, b: int, psw: int) -> tuple[int, int]:
        """SUBB A, src — result, new_psw."""
        cy = 1 if (psw & (1 << PSW_CY)) else 0
        result = a - b - cy
        new_psw = ALU._update_psw_sub(psw, a, b, cy, result)
        return result & 0xFF, new_psw

    @staticmethod
    def inc(a: int) -> int:
        return (a + 1) & 0xFF

    @staticmethod
    def dec(a: int) -> int:
        return (a - 1) & 0xFF

    @staticmethod
    def mul(a: int, b: int, psw: int) -> tuple[int, int, int]:
        """MUL AB — (a_result, b_result, psw)."""
        result = a * b
        b_val = (result >> 8) & 0xFF
        a_val = result & 0xFF
        # CY always cleared
        new_psw = psw & ~(1 << PSW_CY)
        # OV set if result > 255
        if result > 0xFF:
            new_psw |= (1 << PSW_OV)
        else:
            new_psw &= ~(1 << PSW_OV)
        # P
        if ALU._parity(a_val):
            new_psw |= (1 << PSW_P)
        else:
            new_psw &= ~(1 << PSW_P)
        return a_val, b_val, new_psw

    @staticmethod
    def div(a: int, b: int, psw: int) -> tuple[int, int, int]:
        """DIV AB — (quotient_a, remainder_b, psw)."""
        new_psw = psw
        if b == 0:
            new_psw |= (1 << PSW_OV)
            return 0xFF, 0, new_psw
        new_psw &= ~(1 << PSW_OV)
        new_psw &= ~(1 << PSW_CY)
        quotient = a // b
        remainder = a % b
        if ALU._parity(quotient):
            new_psw |= (1 << PSW_P)
        else:
            new_psw &= ~(1 << PSW_P)
        return quotient, remainder, new_psw

    @staticmethod
    def da(a: int, psw: int) -> tuple[int, int]:
        """DA A — Decimal Adjust for BCD addition."""
        new_psw = psw
        adjust = 0
        if (a & 0x0F) > 9 or (psw & (1 << PSW_AC)):
            adjust |= 0x06
        if (a & 0xF0) > 0x90 or (psw & (1 << PSW_CY)):
            adjust |= 0x60
        result = a + adjust
        if result > 0xFF:
            new_psw |= (1 << PSW_CY)
        result &= 0xFF
        if ALU._parity(result):
            new_psw |= (1 << PSW_P)
        else:
            new_psw &= ~(1 << PSW_P)
        return result, new_psw

    # ===== Logic =====

    @staticmethod
    def anl(a: int, b: int) -> int:
        return a & b

    @staticmethod
    def orl(a: int, b: int) -> int:
        return a | b

    @staticmethod
    def xrl(a: int, b: int) -> int:
        return a ^ b

    @staticmethod
    def cpl(a: int) -> int:
        return (~a) & 0xFF

    @staticmethod
    def clr() -> int:
        return 0

    # ===== Rotate =====

    @staticmethod
    def rl(a: int) -> int:
        return ((a << 1) | (a >> 7)) & 0xFF

    @staticmethod
    def rlc(a: int, psw: int) -> tuple[int, int]:
        cy = 1 if (psw & (1 << PSW_CY)) else 0
        result = ((a << 1) | cy) & 0xFF
        new_psw = psw
        if a & 0x80:
            new_psw |= (1 << PSW_CY)
        else:
            new_psw &= ~(1 << PSW_CY)
        return result, new_psw

    @staticmethod
    def rr(a: int) -> int:
        return ((a >> 1) | (a << 7)) & 0xFF

    @staticmethod
    def rrc(a: int, psw: int) -> tuple[int, int]:
        cy = 1 if (psw & (1 << PSW_CY)) else 0
        result = ((a >> 1) | (cy << 7)) & 0xFF
        new_psw = psw
        if a & 0x01:
            new_psw |= (1 << PSW_CY)
        else:
            new_psw &= ~(1 << PSW_CY)
        return result, new_psw

    @staticmethod
    def swap(a: int) -> int:
        return ((a << 4) | (a >> 4)) & 0xFF
