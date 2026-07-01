#pragma once
#include "types.h"
#include <array>

namespace echo_8051 {

class CPU; // forward

extern std::array<InstrInfo, 256> OPCODES;

void build_opcode_table();

const InstrInfo& decode(u8 opcode) noexcept;

// Register index helpers for Rn instructions
inline u8 reg_index(u8 opcode) noexcept { return opcode & 0x07; }

} // namespace echo_8051
