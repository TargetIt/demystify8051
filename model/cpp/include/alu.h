#pragma once
#include "types.h"

namespace echo_8051 {

struct ALU {
    static u8 parity(u8 v) noexcept {
        v ^= v >> 4; v ^= v >> 2; v ^= v >> 1;
        return v & 1;
    }

    static void update_psw_add(u8& psw, u8 a, u8 b, u8 carry_in, u16 result) noexcept {
        if (result > 0xFF) psw |= (1 << PSW_CY); else psw &= ~(1 << PSW_CY);
        if (((a & 0x0F) + (b & 0x0F) + carry_in) > 0x0F) psw |= (1 << PSW_AC); else psw &= ~(1 << PSW_AC);
        bool c6 = ((a & 0x7F) + (b & 0x7F) + carry_in) > 0x7F;
        bool c7 = result > 0xFF;
        (c6 ^ c7) ? psw |= (1 << PSW_OV) : psw &= ~(1 << PSW_OV);
        parity(result & 0xFF) ? psw |= (1 << PSW_P) : psw &= ~(1 << PSW_P);
    }

    static void update_psw_sub(u8& psw, u8 a, u8 b, u8 borrow_in, int result) noexcept {
        (a < (b + borrow_in)) ? psw |= (1 << PSW_CY) : psw &= ~(1 << PSW_CY);
        ((a & 0x0F) < ((b & 0x0F) + borrow_in)) ? psw |= (1 << PSW_AC) : psw &= ~(1 << PSW_AC);
        bool b6 = (a & 0x7F) < ((b & 0x7F) + borrow_in);
        bool b7 = a < (b + borrow_in);
        (b6 ^ b7) ? psw |= (1 << PSW_OV) : psw &= ~(1 << PSW_OV);
        parity(result & 0xFF) ? psw |= (1 << PSW_P) : psw &= ~(1 << PSW_P);
    }

    static u8 add(u8 a, u8 b, u8& psw) noexcept {
        u16 r = u16(a) + b;
        update_psw_add(psw, a, b, 0, r);
        return u8(r);
    }
    static u8 addc(u8 a, u8 b, u8& psw) noexcept {
        u8 cy = (psw >> PSW_CY) & 1;
        u16 r = u16(a) + b + cy;
        update_psw_add(psw, a, b, cy, r);
        return u8(r);
    }
    static u8 subb(u8 a, u8 b, u8& psw) noexcept {
        u8 cy = (psw >> PSW_CY) & 1;
        int r = int(a) - b - cy;
        update_psw_sub(psw, a, b, cy, r);
        return u8(r);
    }
    static u8 inc(u8 v) noexcept { return v + 1; }
    static u8 dec(u8 v) noexcept { return v - 1; }

    static void mul(u8 a, u8 b, u8& acc, u8& b_reg, u8& psw) noexcept {
        u16 r = u16(a) * b;
        acc = u8(r);
        b_reg = u8(r >> 8);
        psw &= ~(1 << PSW_CY);
        r > 255 ? psw |= (1 << PSW_OV) : psw &= ~(1 << PSW_OV);
        parity(acc) ? psw |= (1 << PSW_P) : psw &= ~(1 << PSW_P);
    }

    static void div(u8 a, u8 b, u8& acc, u8& b_reg, u8& psw) noexcept {
        if (b == 0) { psw |= (1 << PSW_OV); acc = 0xFF; b_reg = 0; return; }
        psw &= ~((1 << PSW_OV) | (1 << PSW_CY));
        acc = a / b; b_reg = a % b;
        parity(acc) ? psw |= (1 << PSW_P) : psw &= ~(1 << PSW_P);
    }

    static u8 da(u8 a, u8& psw) noexcept {
        u8 adj = 0;
        if ((a & 0x0F) > 9 || (psw & (1 << PSW_AC))) adj |= 0x06;
        if ((a & 0xF0) > 0x90 || (psw & (1 << PSW_CY))) adj |= 0x60;
        u16 r = u16(a) + adj;
        if (r > 0xFF) psw |= (1 << PSW_CY);
        a = u8(r);
        parity(a) ? psw |= (1 << PSW_P) : psw &= ~(1 << PSW_P);
        return a;
    }

    static u8 anl(u8 a, u8 b) noexcept { return a & b; }
    static u8 orl(u8 a, u8 b) noexcept { return a | b; }
    static u8 xrl(u8 a, u8 b) noexcept { return a ^ b; }
    static u8 cpl(u8 a) noexcept { return ~a; }
    static u8 rl(u8 a) noexcept { return (a << 1) | (a >> 7); }
    static u8 rlc(u8 a, u8& psw) noexcept {
        u8 cy = (psw >> PSW_CY) & 1;
        u8 r = (a << 1) | cy;
        (a & 0x80) ? psw |= (1 << PSW_CY) : psw &= ~(1 << PSW_CY);
        return r;
    }
    static u8 rr(u8 a) noexcept { return (a >> 1) | (a << 7); }
    static u8 rrc(u8 a, u8& psw) noexcept {
        u8 cy = (psw >> PSW_CY) & 1;
        u8 r = (a >> 1) | (cy << 7);
        (a & 0x01) ? psw |= (1 << PSW_CY) : psw &= ~(1 << PSW_CY);
        return r;
    }
    static u8 swap(u8 a) noexcept { return (a << 4) | (a >> 4); }
};

} // namespace echo_8051
