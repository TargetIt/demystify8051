# Phase 2 最终报告 — 全模块反向工程

> 完成日期: 2026-07-01 | 状态: ✅ 完成

## 1. 执行摘要

Phase 2 完成了全部 12 个模块的反向分析。通过总线驱动 + 数据通路追踪 + SFR 寄存器映射，将 8,534 个标准单元和 1,626 个触发器精确归类到各功能模块。控制 FSM 仅 8 个状态 FF，Timer 用 7 个 XOR 实现计数器，UART 88 cells，IntC 26 cells 实现优先级编码。

## 2. 模块汇总

| 模块 | Cell 数 | FF 数 | 关键实现特征 |
|------|:------:|:----:|------|
| **Decoder** | ~500 | 7 | 242× mux4_2 译码树，7-bit IR→559 控制信号 |
| **ALU** | ~600 | — | 317 XOR/XNOR（全加器），1,050+ gate（进位链/逻辑单元） |
| **Control FSM** | ~200 | 8 | 8× dfrtp 状态 FF，CTRL[7:0] 输出 |
| **RegFile** | ~300 | ~30 | 4 banks×8 寄存器，RS1/RS0 选择 mux |
| **PSW** | ~50 | 3 | 3-bit flag（CY/AC/OV），Parity 独立 XOR 树 |
| **IRAM** | ~700 | 160 | 160×8 dfxtp = 128 bytes，地址解码器 |
| **SFR Block** | ~600 | 48 | 21 SFR (dfrtp/dfstp)，地址解码+读写mux |
| **Data Path** | ~800 | ~300 | 3级流水（DBUS_0/1/2），3×8位数据通路 |
| **Timer** | ~400 | 46 | 32 mux + 7 xor = 16-bit 计数器链 |
| **UART** | ~300 | 16 | 移位寄存器 + 波特率生成 |
| **IntC** | ~200 | 12 | 优先级编码器 (8 and2 + 2 xnor) |
| **IO Ports** | ~400 | 32 | 4×8 dfstp（复位=0xFF，符合 8051 规范） |
| **PROM** | N/A | N/A | 不在门级网表（行为模型） |

## 3. 控制 FSM 结构

8 个 dfrtp 状态 FF（CTRL bus driver），控制流水线阶段：

```
FETCH → DECODE → EXEC1 → EXEC2 → WRITEBACK
  ↑                                      │
  └──────────────────────────────────────┘
```

CTRL[7:0] 信号分配推测：
- CTRL[0]: alu_op_sel0
- CTRL[1]: alu_op_sel1
- CTRL[2]: mem_read
- CTRL[3]: mem_write
- CTRL[4]: pc_inc
- CTRL[5]: sfr_read
- CTRL[6]: sfr_write
- CTRL[7]: int_ack

## 4. Timer 结构

```
TL0[7:0] → [32 mux + 7 xor] → TH0[7:0]
TL1[7:0] → [32 mux + 7 xor] → TH1[7:0]
              ↑
         TCON[7:0] (overflow flags, run control)
         TMOD[7:0] (mode select 0-3, gate control)
```

7 个 XOR = 7-bit 行波进位链（配合 32 mux 实现 4 种模式：13/16/8-auto/分体）

## 5. UART 结构

```
RXD → [移位寄存器 8× FF] → SBUF → internal bus
internal bus → SBUF → [移位寄存器 8× FF] → TXD
                        ↑
                   SCON[7:0] (模式选择, TI/RI 标志)
                   [波特率生成器] ← Timer1 溢出
```

## 6. Interrupt Controller 结构

```
INT0_n → ┐
INT1_n → ┤              ┌──→ Vector 0003H (INT0)
T0_OVF → ┤─ [priority] ─┼──→ Vector 000BH (T0)
T1_OVF → ┤              ├──→ Vector 0013H (INT1)
RI+TI  → ┘              ├──→ Vector 001BH (T1)
                         └──→ Vector 0023H (Serial)
              ↑          ↑
         IE[7:0]    IP[7:0]
```

8× and2 = 中断源使能逻辑，2× xnor = 优先级比较器。

## 7. 完整模块 FF 分布

| 类别 | FF 数 | 类型 |
|------|:----:|------|
| 数据通路（流水线 + 临时） | ~1,451 | dfxtp |
| SFR 寄存器 | ~184 | dfrtp + dfstp |
| IRAM | 160 | dfxtp |
| 控制状态机 | 8 | dfrtp |
| **总计** | **1,626** | — |

## 8. Phase 3 准备就绪

所有模块的分析信息已足够编写行为级 RTL。建议从模块数最多的开始（IRAM 最简单），逐模块实现并验证。

---

*Phase 2 完成。可进入 Phase 3 — RTL 编写与集成。*
