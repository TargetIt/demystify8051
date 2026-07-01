# echo_8051 调研报告

## 调研范围

调研开源 8051 微控制器 IP 核项目，重点评估其作为 echo_8051 参考设计的可行性。

## 候选开源项目

### 1. OC8051 (OpenCores) — 最成熟的开源 8051 ⭐推荐

| 属性 | 值 |
|------|-----|
| 仓库 | `opencores.org/project/8051` (GitHub: `freecores/8051`) |
| 语言 | Verilog |
| 规模 | ~4000 行 Verilog (多文件) |
| 架构 | 2 级流水线，Wishbone 总线 |
| 综合 | Altera Cyclone II, ~3917 LE, max ~30.8 MHz |
| 外设 | 兼容标准 8051，含 UART/Timer/I/O |
| 文档 | 丰富的社区文档，STEP FPGA 社区中文 Wiki |
| 已知问题 | 存在若干逻辑 bug（外部 RAM 地址、PSW、decoder），社区有修复方案 |
| 授权 | GPL/LGPL |

**优点**：最完整、文档最丰富、代码结构清晰、Wishbone 总线便于扩展
**缺点**：原始版本有 bug 需要修复、代码略显老旧（Verilog-95 风格）

### 2. R8051 (risclite) — 最精简的 Verilog 实现

| 属性 | 值 |
|------|-----|
| 仓库 | `github.com/risclite/R8051` |
| 语言 | Verilog |
| 规模 | 仅 2 个文件，~700 行 |
| 架构 | 3 级字节流水线（A-B-C） |
| 指令 | 支持全部 111 条指令 |
| 配套 | 有中文书籍《8051 软核处理器设计实战》 |
| 综合 | 可综合，Verilog-2001 |

**优点**：极其精简（适合学习和移植）、完全可综合
**缺点**：功能有限（无完整外设）、流水线建模不够精确

### 3. GOWIN-FPGA/OC8051_V1.0 — 最新的工业级移植（2024 年 11 月）

| 属性 | 值 |
|------|-----|
| 仓库 | `github.com/GOWIN-FPGA/OC8051_V1.0` |
| 语言 | Verilog |
| 特性 | 基于 OC8051，针对 GOWIN FPGA 优化 |
| 外设 | 完整支持 64KB ROM, 256B RAM, 3×Timer, UART, 6 中断/2 优先级 |
| 综合 | ✅ 可综合 |

**优点**：2024 年最新版本、工业级质量、完整外设
**缺点**：GOWIN FPGA 特化（部分代码需修改用于 ASIC）

### 4. PulseRain FP51-1T — 最高性能实现（SystemVerilog）

| 属性 | 值 |
|------|-----|
| 来源 | PulseRain Technology (GitHub) |
| 语言 | SystemVerilog |
| 架构 | 1T 单周期架构，大多数指令 1 个时钟 |
| 性能 | 最高 96 MHz |
| 特性 | OCD 片上调试、Wishbone、Arduino 兼容 BSP |
| 授权 | GPL v3 / 商业授权 |

**优点**：最高性能、片上调试验证、外设丰富
**缺点**：SystemVerilog 复杂（OpenLane/Yosys 对 SV 支持有限）、商业授权限制

### 5. mc8051 (Oregano) — VHDL 开源实现

| 属性 | 值 |
|------|-----|
| 语言 | VHDL |
| 综合 | Altera Cyclone II, fmax ~20 MHz |

**优点**：VHDL 实现（多一种选择）
**缺点**：性能较低、VHDL 在 Yosys/OpenLane 中支持有限

---

## 8051 指令集完整分析

### 操作码分布

Intel 8051 共有 **255 个有效操作码**（0x00-0xFE，0xA5 保留未定义），按指令类型：

| 类别 | 操作码数量 | 说明 |
|------|-----------|------|
| 数据传送 | ~50 | MOV/MOVC/MOVX/PUSH/POP/XCH |
| 算术运算 | ~30 | ADD/ADDC/SUBB/MUL/DIV/INC/DEC/DA |
| 逻辑运算 | ~25 | ANL/ORL/XRL/CLR/CPL/RL/RLC/RR/RRC/SWAP |
| 布尔操作 | ~17 | CLR/SETB/CPL/ANL/ORL/MOV/JC/JNC/JB/JNB/JBC（位操作） |
| 程序转移 | ~20 | LJMP/AJMP/SJMP/JMP/JZ/JNZ/CJNE/DJNZ/LCALL/ACALL/RET/RETI/NOP |
| 空操作 | ~113 | 大量操作码在标准 8051 中无定义（NOP 等效） |

### 关键架构参数

| 参数 | Intel 8051 | echo_8051 目标 |
|------|-----------|---------------|
| 数据宽度 | 8 位 | 8 位 |
| 地址宽度 | 16 位（64KB 程序 + 64KB 数据） | 同 |
| 寄存器组 | 4 组 × 8 寄存器 | 同 |
| 时钟模式 | 12T（12 时钟/机器周期） | 12T（后期可优化为 1T） |
| ALU | 8 位，支持 MUL/DIV | 同 |
| 程序 ROM | 4KB 掩膜 ROM | 4KB（行为模型用 RAM 模拟） |
| 内部 RAM | 128B 直接+间接 寻址 | 同 |
| SFR | 128B SFR 空间 | 同 |
| I/O | P0-P3 共 32 线 | 同 |
| 定时器 | T0, T1 | 同（可扩展 T2） |
| 串行口 | 全双工 UART, 4 模式 | 同 |
| 中断 | 5 源 2 优先级 | 同 |

---

## 推荐参考方案

### 首选参考：OC8051 + R8051 混合设计

1. **指令译码器** → 参考 R8051 的微码 ROM 设计（紧凑高效）
2. **ALU** → 参考 OC8051 的分层设计（清晰可测）
3. **外设 (Timer/UART/IntC)** → 参考 GOWIN OC8051（最完整）
4. **总线** → 采用简化的内部总线（非 Wishbone，降低复杂度）

### 设计策略

| 阶段 | 方案 |
|------|------|
| 建模 | Python ISS → C++ 高性能模型（周期精确） |
| RTL | Verilog-2001 可综合风格，模块化设计 |
| 验证 | 直接 testbench + UVM 框架（SystemVerilog） |
| 综合 | Yosys + OpenLane + Sky130A |
| PnR | OpenLane 自动流程 |
| 签核 | Magic/KLayout DRC/LVS |

### 工具链

| 用途 | 工具 |
|------|------|
| 仿真 (RTL) | Icarus Verilog / Verilator |
| UVM 验证 | Verilator + SystemVerilog (Verilator 5.x+) |
| 综合 | Yosys (via OpenLane) |
| PnR | OpenROAD (via OpenLane) |
| DRC/LVS | Magic / KLayout |
| 波形查看 | GTKWave / Surfer |
| 编译器 | SDCC（Small Device C Compiler，开源 8051 编译器） |
| 汇编器 | ASEM-51 / ASM51 |
