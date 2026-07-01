#pragma once
#include "types.h"

namespace echo_8051 {

class Memory {
public:
    static constexpr size_t ROM_SIZE = 4096;
    static constexpr size_t IRAM_SIZE = 128;
    static constexpr size_t SFR_SIZE = 128;
    static constexpr size_t XRAM_SIZE = 65536;

    Memory() { reset(); }

    void reset() {
        iram.fill(0);
        sfr.fill(0);
        xram.fill(0);
        sfr[SFR_SP - 0x80] = 0x07;
        for (auto addr : {SFR_P0, SFR_P1, SFR_P2, SFR_P3})
            sfr[addr - 0x80] = 0xFF;
    }

    // ROM
    u8 read_rom(u16 addr) const { return rom[addr % ROM_SIZE]; }
    void write_rom(u16 addr, u8 v) { rom[addr % ROM_SIZE] = v; }

    // IRAM (direct: 0x00-0x7F→IRAM, 0x80-0xFF→SFR)
    u8 read_iram(u8 addr) const {
        if (addr < 0x80) return iram[addr];
        return sfr[addr - 0x80];
    }
    void write_iram(u8 addr, u8 v) {
        if (addr < 0x80) iram[addr] = v;
        else sfr[addr - 0x80] = v;
    }

    // IRAM indirect (@R0/@R1: 0x80-0xFF not SFR)
    u8 read_indirect(u8 addr) const {
        return addr < 0x80 ? iram[addr] : 0;
    }
    void write_indirect(u8 addr, u8 v) {
        if (addr < 0x80) iram[addr] = v;
    }

    // XRAM
    u8 read_xram(u16 addr) const { return xram[addr]; }
    void write_xram(u16 addr, u8 v) { xram[addr] = v; }

    // SFR accessors
    u8& sfr_at(u8 addr) { return sfr[addr - 0x80]; }
    const u8& sfr_at(u8 addr) const { return sfr[addr - 0x80]; }

    u8& acc()   { return sfr[SFR_ACC - 0x80]; }
    u8& b()     { return sfr[SFR_B - 0x80]; }
    u8& psw()   { return sfr[SFR_PSW - 0x80]; }
    u8& sp()    { return sfr[SFR_SP - 0x80]; }
    u8& ie()    { return sfr[SFR_IE - 0x80]; }
    u8& ip()    { return sfr[SFR_IP - 0x80]; }
    u8& tcon()  { return sfr[SFR_TCON - 0x80]; }
    u8& scon()  { return sfr[SFR_SCON - 0x80]; }
    // Const accessors
    u8 acc_c() const { return sfr[SFR_ACC - 0x80]; }
    u8 b_c()   const { return sfr[SFR_B - 0x80]; }
    u8 psw_c() const { return sfr[SFR_PSW - 0x80]; }
    u8 sp_c()  const { return sfr[SFR_SP - 0x80]; }

    u16 dptr() const { return (u16(sfr[SFR_DPH - 0x80]) << 8) | sfr[SFR_DPL - 0x80]; }
    void set_dptr(u16 v) { sfr[SFR_DPL - 0x80] = v & 0xFF; sfr[SFR_DPH - 0x80] = (v >> 8) & 0xFF; }

    // Carry bit
    bool carry() { return psw() & (1 << PSW_CY); }
    void set_carry(bool v) { v ? psw() |= (1 << PSW_CY) : psw() &= ~(1 << PSW_CY); }

    // Bit operations
    bool read_bit(u8 bit_addr) const {
        u8 byte_addr = (bit_addr < 0x80) ? u8(0x20 + (bit_addr >> 3)) : u8(bit_addr & 0xF8);
        return read_iram(byte_addr) & (1 << (bit_addr & 7));
    }
    void write_bit(u8 bit_addr, bool v) {
        u8 byte_addr = (bit_addr < 0x80) ? u8(0x20 + (bit_addr >> 3)) : u8(bit_addr & 0xF8);
        u8 byte = read_iram(byte_addr);
        v ? byte |= (1 << (bit_addr & 7)) : byte &= ~(1 << (bit_addr & 7));
        write_iram(byte_addr, byte);
    }

    std::array<u8, ROM_SIZE> rom;
    std::array<u8, IRAM_SIZE> iram;
    std::array<u8, SFR_SIZE> sfr;
    std::array<u8, XRAM_SIZE> xram;
};

} // namespace echo_8051
