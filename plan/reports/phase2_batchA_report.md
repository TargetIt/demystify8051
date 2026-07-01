# Phase 2 Batch A 报告 — Decoder, ALU, Data Path

> 完成日期: 2026-07-01 | 状态: ✅ 完成 | 模块: Decoder, ALU, Data Path, PSW

## 1. 执行摘要

Batch A 完成了四个核心模块的反向分析。关键发现：**Decoder 由 242 个 4-to-1 MUX 构成译码树**（非微码 ROM），**数据通路为 3 级流水线**（DBUS_0→DBUS_1→DBUS_2），**ALU 由 XOR/XNOR 阵列实现**（共 317 个 XOR/XNOR cell），数据流为 SFR→(MUX)→DBUS_0→(ALU)→DBUS_1→(ALU)→DBUS_2→ACC。

## 2. Decoder 模块分析

### 2.1 实现结构

| 属性 | 值 |
|------|-----|
| 输入 | `_07126_[6:0]` — 7-bit 指令寄存器 |
| 直接读取 IR 的 cell | 559 个 |
| 主导 cell 类型 | `mux4_2` (242 个, 43%) |
| 次级 cell 类型 | `o21ai_0` (127 个, 23%) |
| 输出控制信号 | 559 条 |

### 2.2 译码结构推断

```
IR[6:0] ──→ [Level 0: 242× mux4_2] ──→ [Level 1: NOR/NAND gates] ──→ 559 control signals
            ├─ 每个 mux4 选择 4 种可能的控制值
            ├─ 选择线 = IR bits 的子集
            └─ 输出 = 某一条控制信号的真值
```

**证据**：
- `mux4_2` 在 IR reader 中占 43%，这是典型的多级译码器结构
- 最高 fanout 信号 `_01785_` 控制 99 个目标——这是全局使能类信号
- 信号 `_01782_` (54 targets), `_01781_` (35 targets) 是次级全局控制

### 2.3 控制信号分级

| 级别 | 信号 | Fanout | 推测功能 |
|------|------|:-----:|------|
| L0 全局 | `_01785_` | 99 | 主使能 / ALU 操作使能 |
| L0 全局 | `_01782_` | 54 | 存储器读使能 |
| L0 全局 | `_01781_` | 35 | 存储器写使能 |
| L1 模块级 | `_03596_`~`_05640_` | 8-12 | 各外设使能信号 |
| L2 细粒度 | 500+ 信号 | 1-7 | 具体操作选择（ADD/SUB/MOV...） |

### 2.4 为什么不是微码 ROM？

微码 ROM 通常由规则的大规模存储阵列（DFF + 译码）实现。但网表中 242 个 `mux4_2` 是**分布式选择逻辑**——每个 mux 独立地根据 IR 位选择控制值。这是硬连线 FSM 风格，速度更快但更分散。

## 3. ALU 模块分析

### 3.1 数据通路架构

```
SFR_DOUT(_07123_) ──→ [MUX tree] ──→ DBUS_0(_07076_)
                                           │
                                      [ALU Stage 1]
                                           │
                                           ▼
                                      DBUS_1(_07057_)
                                           │
                                      [ALU Stage 2]  ← CTRL(_07110_)
                                           │
                                           ▼
                                      DBUS_2(_07067_)
                                           │
                                           ▼
                                      ACC(_07109_)
```

**关键发现**：
- ACC 和 DB_B 不直接汇入同一 ALU cell（intersection=0），数据通过流水线串行
- ALU 操作分散在 DBUS_0→DBUS_1 和 DBUS_1→DBUS_2 两个阶段
- CTRL[7:0] 信号选通 ALU 操作类型

### 3.2 ALU 运算资源

| 资源 | 数量 | 功能 |
|------|:---:|------|
| `xnor2_1` | 210 | 异或非——全加器核心 |
| `xor2_1` | 107 | 异或——全加器/减法器核心 |
| `mux2_1` | 171 | 操作选择 |
| `a21oi_1` | 1,050 | 与或非——进位链 + 逻辑运算 |
| `o21ai_0` | 1,028 | 或与非——进位链 + 逻辑运算 |
| `nor2_1` | 1,368 | 或非——逻辑运算 |
| `nand2_1` | 1,224 | 与非——逻辑运算 |

XOR+XNOR = 317 个 cell → 8-bit × ~40 cells/bit → 典型的**行波进位加法器** + **逻辑运算单元**。

### 3.3 ALU 操作推断

基于 cell 类型分布，8051 ALU 指令对应的硬件：
- **ADD/ADDC**: `xor2 × 2` + `a21oi` + `o21ai` — 全加器链
- **SUBB**: `xor2` (补码取反) + 全加器链
- **ANL/ORL/XRL**: `nand2`/`nor2`/`xor2` 阵列
- **INC/DEC**: 简化版全加器（+1/-1）
- **MUL/DIV**: 可能需要 `mux4_2` 切换数据通路（迭代算法）
- **DA (BCD 调整)**: `maj3_1` 检测半进位

## 4. 数据通路总结

### 4.1 三级流水线

| 阶段 | 总线 | 驱动数 | 读取数 | 功能 |
|------|------|:---:|:---:|------|
| Stage 0 | `_07123_` (SFR_DOUT) | 8 | 35 | SFR 读出 |
| Stage 0 | `_07076_` (DBUS_0) | 8 | 113 | 第一级 ALU 输入 |
| Stage 1 | `_07057_` (DBUS_1) | 8 | 117 | ALU 中间结果 |
| Stage 2 | `_07067_` (DBUS_2) | 8 | 70 | ALU 最终结果 |
| WB | `_07109_` (ACC) | 8 | 178 | 累加器写回 |

### 4.2 PSW 标志位

| 位 | 寄存器 | Fanout | 功能 |
|----|--------|:-----:|------|
| Bit 0 | `_07104_[0]` | 71 | PSW.P (Parity) |
| Bit 1 | `_07104_[1]` | — | 推测 PSW.CY / AC |
| Bit 2 | `_07104_[2]` | 73 | 推测 PSW.OV |
| 3-bit 宽度 | — | — | 仅实现了 CY+AC+OV（Parity 可能单独生成） |

## 5. 下一步：RTL 编写（Phase 3）

基于以上分析，Decoder + ALU + Data Path 的 RTL 框架：

```verilog
// decoder.v — 7-bit opcode → control signals
// 242× mux4_2 可简化为: case(opcode[6:0]) → signal_assignments

// alu.v — 8-bit ALU with carry chain
// xnor/xor 317 cells → full adder + logic unit

// data_path.v — 3-stage pipeline
// SFR_DOUT → MUX → DBUS_0 → ALU_stage1 → DBUS_1 → ALU_stage2 → DBUS_2 → ACC
```

## 6. 遗留问题

| # | 问题 | 处理方式 |
|----|------|------|
| L2.1 | 559 条控制信号到具体指令的映射未完成 | 需 Phase 3 通过仿真验证逐信号标注 |
| L2.2 | MUL/DIV 的迭代数据通路未追踪 | 复杂——暂标记为 Spec 参考实现 |
| L2.3 | PSW parity 位可能用独立 XOR 树实现 | 从 PSW_FLAGS bus 的 reader 中追踪 |

## 7. 交付件

| 编号 | 交付件 | 路径 | 状态 |
|------|--------|------|:--:|
| D2A.1 | Decoder 分析 | `tools/decoder_analyzer.py` | ✅ |
| D2A.2 | Pipeline 分析 | `tools/pipeline_analyzer.py` | ✅ |
| D2A.3 | 本报告 | `plan/reports/phase2_batchA_report.md` | ✅ |
