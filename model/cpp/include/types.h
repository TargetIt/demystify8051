#pragma once
#include <cstdint>
#include <array>
#include <vector>
#include <string_view>
#include <functional>

namespace echo_8051 {

using u8  = uint8_t;
using u16 = uint16_t;
using u32 = uint32_t;
using u64 = uint64_t;
using s8  = int8_t;
using s16 = int16_t;
using i64 = int64_t;

// SFR addresses
constexpr u8 SFR_P0   = 0x80;
constexpr u8 SFR_SP   = 0x81;
constexpr u8 SFR_DPL  = 0x82;
constexpr u8 SFR_DPH  = 0x83;
constexpr u8 SFR_PCON = 0x87;
constexpr u8 SFR_TCON = 0x88;
constexpr u8 SFR_TMOD = 0x89;
constexpr u8 SFR_TL0  = 0x8A;
constexpr u8 SFR_TL1  = 0x8B;
constexpr u8 SFR_TH0  = 0x8C;
constexpr u8 SFR_TH1  = 0x8D;
constexpr u8 SFR_P1   = 0x90;
constexpr u8 SFR_SCON = 0x98;
constexpr u8 SFR_SBUF = 0x99;
constexpr u8 SFR_P2   = 0xA0;
constexpr u8 SFR_IE   = 0xA8;
constexpr u8 SFR_P3   = 0xB0;
constexpr u8 SFR_IP   = 0xB8;
constexpr u8 SFR_PSW  = 0xD0;
constexpr u8 SFR_ACC  = 0xE0;
constexpr u8 SFR_B    = 0xF0;

// PSW bit positions
constexpr u8 PSW_P  = 0;
constexpr u8 PSW_OV = 2;
constexpr u8 PSW_RS0 = 3;
constexpr u8 PSW_RS1 = 4;
constexpr u8 PSW_F0 = 5;
constexpr u8 PSW_AC = 6;
constexpr u8 PSW_CY = 7;

// IE bits
constexpr u8 IE_EX0 = 0, IE_ET0 = 1, IE_EX1 = 2, IE_ET1 = 3, IE_ES = 4, IE_EA = 7;

// Interrupt vectors
constexpr u16 INT_VEC_INT0 = 0x0003;
constexpr u16 INT_VEC_T0   = 0x000B;
constexpr u16 INT_VEC_INT1 = 0x0013;
constexpr u16 INT_VEC_T1   = 0x001B;
constexpr u16 INT_VEC_UART = 0x0023;

// TCON bits
constexpr u8 TCON_IT0=0, TCON_IE0=1, TCON_IT1=2, TCON_IE1=3;
constexpr u8 TCON_TR0=4, TCON_TF0=5, TCON_TR1=6, TCON_TF1=7;

// Instruction info
struct InstrInfo {
    std::string_view mnemonic;
    u8 nbytes;
    u8 cycles;
    void (*handler)(class CPU& cpu, u8 opcode);
};

// CPU state snapshot
struct CPUState {
    u16 pc;
    u8 acc, b, psw, sp;
    u16 dptr;
    u64 cycles;
    u64 instructions;
    std::array<u8, 128> iram;
    std::array<u8, 128> sfr;
};

} // namespace echo_8051
