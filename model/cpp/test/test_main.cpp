#include "echo_8051.h"
#include <cstdio>
#include <cassert>
#include <vector>

using namespace echo_8051;

static int pass = 0, fail = 0;

void check(const char* name, u64 actual, u64 expected) {
    if (actual == expected) { pass++; printf("  [PASS] %s: %llu\n", name, (unsigned long long)actual); }
    else { fail++; printf("  [FAIL] %s: got %llu, expected %llu\n", name, (unsigned long long)actual, (unsigned long long)expected); }
}

int main() {
    printf("=== echo_8051 C++ ISS Test ===\n\n");

    // Test 1: Reset state
    {
        Echo8051 cpu;
        auto s = cpu.get_state();
        check("PC after reset", s.pc, 0);
        check("ACC after reset", s.acc, 0);
        check("SP after reset", s.sp, 0x07);
    }

    // Test 2: NOP
    {
        Echo8051 cpu;
        u8 prog[] = {0x00, 0x00, 0x00, 0x00, 0x00};
        cpu.load_bytes(prog, 5);
        for (int i = 0; i < 5; i++) cpu.step();
        check("PC after 5 NOPs", cpu.get_pc(), 5);
    }

    // Test 3: MOV immediate
    {
        Echo8051 cpu;
        u8 prog[] = {0x74, 0x55}; // MOV A,#0x55
        cpu.load_bytes(prog, 2);
        cpu.step();
        check("MOV A,#0x55", cpu.acc(), 0x55);
    }

    // Test 4: ADD
    {
        Echo8051 cpu;
        u8 prog[] = {0x74, 0x10, 0x24, 0x20}; // MOV A,#0x10; ADD A,#0x20
        cpu.load_bytes(prog, 4);
        cpu.step(); cpu.step();
        check("ADD 0x10+0x20", cpu.acc(), 0x30);
    }

    // Test 5: ADD overflow
    {
        Echo8051 cpu;
        u8 prog[] = {0x74, 0xFF, 0x24, 0x01}; // MOV A,#0xFF; ADD A,#0x01
        cpu.load_bytes(prog, 4);
        cpu.step(); cpu.step();
        check("0xFF+0x01=0", cpu.acc(), 0x00);
        check("CY after overflow", (cpu.psw() >> PSW_CY) & 1, 1);
    }

    // Test 6: SUBB
    {
        Echo8051 cpu;
        u8 prog[] = {0x74, 0x50, 0xC3, 0x94, 0x10}; // MOV A,#0x50; CLR C; SUBB A,#0x10
        cpu.load_bytes(prog, 5);
        cpu.step(); cpu.step(); cpu.step();
        check("SUBB 0x50-0x10", cpu.acc(), 0x40);
    }

    // Test 7: MUL
    {
        Echo8051 cpu;
        u8 prog[] = {0x74, 0x0A, 0x75, 0xF0, 0x06, 0xA4}; // MOV A,#10; MOV B,#6; MUL AB
        cpu.load_bytes(prog, 6);
        cpu.step(); cpu.step(); cpu.step();
        check("MUL 10*6=A", cpu.acc(), 60);
        check("MUL 10*6=B", cpu.cpu.mem.b(), 0);
    }

    // Test 8: DIV
    {
        Echo8051 cpu;
        u8 prog[] = {0x74, 0x0F, 0x75, 0xF0, 0x04, 0x84}; // MOV A,#15; MOV B,#4; DIV AB
        cpu.load_bytes(prog, 6);
        cpu.step(); cpu.step(); cpu.step();
        check("DIV 15/4=A", cpu.acc(), 3);
        check("DIV 15%%4=B", cpu.cpu.mem.b(), 3);
    }

    // Test 9: PUSH/POP
    {
        Echo8051 cpu;
        u8 prog[] = {0x74, 0x42, 0xC0, 0xE0, 0xE4, 0xD0, 0xE0};
        cpu.load_bytes(prog, 7);
        cpu.step(); // MOV
        cpu.step(); // PUSH ACC
        check("SP after PUSH", cpu.cpu.mem.sp(), 0x08);
        cpu.step(); // CLR A
        check("ACC after CLR", cpu.acc(), 0x00);
        cpu.step(); // POP ACC
        check("ACC after POP", cpu.acc(), 0x42);
        check("SP after POP", cpu.cpu.mem.sp(), 0x07);
    }

    // Test 10: SJMP
    {
        Echo8051 cpu;
        u8 prog[] = {0x00, 0x80, 0x02, 0x74, 0xFF, 0x74, 0x42};
        cpu.load_bytes(prog, 7);
        cpu.step(); // NOP
        cpu.step(); // SJMP +2
        check("PC after SJMP", cpu.get_pc(), 5);
        cpu.step(); // MOV A,#0x42
        check("ACC after SJMP landing", cpu.acc(), 0x42);
    }

    // Test 11: LCALL/RET
    {
        Echo8051 cpu;
        std::vector<u8> prog(66000, 0x00);
        prog[0x00]=0x12; prog[0x01]=0x01; prog[0x02]=0x00; // LCALL 0x0100
        prog[0x0100]=0x22; // RET
        cpu.load_bytes(prog.data(), prog.size());
        cpu.step(); // LCALL
        check("PC after LCALL", cpu.get_pc(), 0x0100);
        cpu.step(); // RET
        check("PC after RET", cpu.get_pc(), 0x0003);
    }

    // Test 12: DJNZ
    {
        Echo8051 cpu;
        // MOV R0,#3 (2B: 0x78,0x03); NOP (1B: 0x00); DJNZ R0,rel (2B: 0xD8, 0xFD)
        // DJNZ at addr 3, next PC=5. Jump back to NOP: rel = 2-5 = -3 = 0xFD
        u8 prog[] = {0x78, 0x03, 0x00, 0xD8, 0xFD};
        cpu.load_bytes(prog, 5);
        cpu.step(); // MOV R0,#3: PC=2, R0=3
        cpu.step(); // NOP @2: PC=3
        cpu.step(); // DJNZ @3, rel=-3→PC=2: PC=2, R0=2
        check("R0 after 1st DJNZ", cpu.cpu.mem.read_iram(0), 2);
        cpu.step(); // NOP: PC=3
        cpu.step(); // DJNZ: PC=2, R0=1
        check("R0 after 2nd DJNZ", cpu.cpu.mem.read_iram(0), 1);
        cpu.step(); // NOP: PC=3
        cpu.step(); // DJNZ: R0=0, no jump, PC=5
        check("R0 after 3rd DJNZ", cpu.cpu.mem.read_iram(0), 0);
        check("PC after loop exit", cpu.get_pc(), 5);
    }

    printf("\n=== Results: %d/%d passed ===\n", pass, pass+fail);
    return fail > 0 ? 1 : 0;
}
