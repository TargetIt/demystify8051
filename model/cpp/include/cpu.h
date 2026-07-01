#pragma once
#include "types.h"
#include "memory.h"
#include "alu.h"
#include "decoder.h"

namespace echo_8051 {

class CPU {
public:
    explicit CPU(u32 rom_size = 4096);
    void reset();

    // Program loading
    void load_hex(const char* filename);
    void load_bytes(const u8* data, size_t len, u16 start_addr = 0);

    // Execution
    u8 step();       // execute one instruction, returns cycles
    void run(i64 max_cycles = -1, i64 max_instr = -1);

    // Interrupt
    void request_interrupt(u16 vector, u8 flag_sfr, u8 flag_bit, u8 enable_bit);
    void service_interrupts();

    // Timer
    void update_timers(u8 cycles);

    // Fetch
    u8 fetch() {
        u8 b = mem.read_rom(pc);
        pc = (pc + 1) & 0xFFFF;
        return b;
    }

    // Register bank
    u8 reg_bank_base() { return ((mem.psw() >> PSW_RS0) & 3) * 8; }
    u8 read_rn(u8 n) { return mem.read_iram(reg_bank_base() + (n & 7)); }
    void write_rn(u8 n, u8 v) { mem.write_iram(reg_bank_base() + (n & 7), v); }
    u8 r0_addr() { return read_rn(0); }
    u8 r1_addr() { return read_rn(1); }

    s8 signed_rel(u8 imm) { return (imm & 0x80) ? s8(imm) - 256 : s8(imm); }

    // State (non-const because mem accessors are non-const)
    CPUState get_state();

    // Public members
    Memory mem;
    u16 pc = 0;
    u64 cycles = 0;
    u64 instr_count = 0;
    bool running = true;
    bool intr_active = false;
    u32 rom_size;

    std::vector<std::pair<u16, u8>> pending_intr; // (vector, priority)
    std::vector<u8> uart_rx_buf;
};

} // namespace echo_8051
