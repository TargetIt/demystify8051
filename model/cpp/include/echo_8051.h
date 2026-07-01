#pragma once
#include "cpu.h"

namespace echo_8051 {

class Echo8051 {
public:
    explicit Echo8051(u32 rom_size = 4096) : cpu(rom_size) {}

    void reset() { cpu.reset(); }
    void load_hex(const char* f) { cpu.load_hex(f); }
    void load_bytes(const u8* d, size_t len, u16 addr=0) { cpu.load_bytes(d,len,addr); }
    u8 step() { return cpu.step(); }
    void run(i64 max_cycles=-1, i64 max_instr=-1) { cpu.run(max_cycles, max_instr); }
    CPUState get_state() { return cpu.get_state(); }

    u16 get_pc() const { return cpu.pc; }
    u64 get_cycles() const { return cpu.cycles; }
    u64 get_instr_count() const { return cpu.instr_count; }
    u8 acc() { return cpu.mem.acc(); }
    u8 psw() { return cpu.mem.psw(); }

    CPU cpu;
};

} // namespace echo_8051
