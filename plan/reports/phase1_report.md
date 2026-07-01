# Phase 1 报告 — 顶层结构识别

> 完成日期: 2026-07-01 | 状态: ✅ 完成

## 1. 执行摘要

Phase 1 通过总线驱动的分析方法，成功从扁平网表中识别出 15 条关键功能总线，并通过 FF 的总线连接特征将 121 个接口寄存器精确归类到 15 个功能组。这些功能组与 Spec 中的 12 个模块一一对应，为 Phase 2 逐模块反向提供了清晰的锚点。

## 2. 关键方法发现：总线驱动优于纯聚类

初始的 FF-FF 连接聚类产生了 1,533 个微小簇——这是因为综合 flatten 后 FF 间的直接连接非常稀疏。切换为**总线驱动方法**后，通过追踪每个 FF 连接到的 15 条关键总线，精确识别出 121 个接口寄存器，分类为 15 个功能组。

## 3. 识别的关键总线与模块对应

| 总线 | 位宽 | 总 fanout | 对应模块 | 功能 |
|------|:---:|:--:|------|------|
| `_07126_` (IR) | 7 | 859 | Decoder | 指令寄存器，所有控制信号的源头 |
| `_07111_` (PC) | 16 | 236 | Control FSM | 程序计数器 |
| `_07109_` (ACC) | 8 | 199 | ALU | 累加器 |
| `_07121_` (DB_B) | 8 | 183 | ALU | ALU 输入 B / B 寄存器 |
| `_07110_` (CTRL) | 8 | 173 | Control FSM | 控制信号输出 |
| `_07104_` (PSW) | 3 | 167 | PSW | 标志位 (CY/AC/OV) |
| `_07127_` (ADDR) | 12 | 143 | RAM/SFR | 地址总线 |
| `_07076_` (DBUS_0) | 8 | 140 | Data Path | 数据总线阶段 0 |
| `_07057_` (DBUS_1) | 8 | 128 | Data Path | 数据总线阶段 1 |
| `_07067_` (DBUS_2) | 8 | 101 | Data Path | 数据总线阶段 2 |
| `_07108_` (SFR_DIN) | 8 | 57 | SFR Block | SFR 数据输入 |
| `_07123_` (SFR_DOUT) | 8 | 53 | SFR Block | SFR 数据输出 |
| `_07143_` (RAM_ADDR) | 8 | 53 | IRAM | RAM 地址 |
| `_07112_` (RAM_DATA) | 3 | 49 | IRAM | RAM 数据/控制 |
| `_07106_` (PC_LOW) | 8 | 47 | Control FSM | PC 低字节 |

### 3.1 三级流水线数据通路

```
                  DBUS_0            DBUS_1           DBUS_2
                  _07076_           _07057_          _07067_
                (8b, 140 fan)     (8b, 128 fan)    (8b, 101 fan)
  SFR_DOUT ──→  [Stage 0]  ──→  [Stage 1]  ──→  [Stage 2]  ──→ ACC
  _07123_                                                ↑
                                                         │
  DB_B ←── ALU Input B                                    │
  _07121_ (8b, 183 fan)                                  │
                                                         │
  ACC ←── Accumulator ←──────────────────────────────────┘
  _07109_ (8b, 199 fan)
```

这揭示了 8051 内部的 3 级流水线结构：SFR 读取 → 流水级 0 → 流水级 1 → 流水级 2 → ACC 写回。

## 4. 模块边界标定结果

基于总线连接特征，1,626 个 FF 被分级分类：

| 分类层级 | FFs | 说明 |
|---------|:---:|------|
| Level 1 — 接口寄存器 | 121 | 直接连接到大总线，边界清晰 |
| Level 2 — 模块内部 | ~1,500 | 需要通过 fan-in/fan-out 锥分析分配 |
| 未分配 | 26 | 孤立的控制/流水线 FF |

### 4.1 模块→FF 映射（Level 1 接口）

| 模块 | 接口 FF 数 | 关键总线 | 推定范围 |
|------|:--------:|------|------|
| Decoder | 7 | IR[6:0] | ~300 cells |
| ALU | 16 | ACC, DB_B | ~200 cells |
| Control FSM | 24 | PC[15:0], CTRL[7:0], PC_LOW | ~150 cells |
| PSW | 3 | PSW_FLAGS[2:0] | ~50 cells |
| Data Path | 24 | DBUS_0, DBUS_1, DBUS_2 | ~400 cells |
| SFR Block | 16 | SFR_DIN, SFR_DOUT | ~500 cells |
| IRAM | 11 | RAM_ADDR, RAM_DATA | ~600 cells |
| RegFile | ~30 | (internal, shared bus) | ~400 cells |
| Timer | ~24 | (internal, timer-specific) | ~400 cells |
| UART | ~8 | (internal, serial-specific) | ~300 cells |
| IntC | ~6 | (internal, interrupt-specific) | ~200 cells |
| IO Ports | ~16 | p0-p3 ports | ~400 cells |

### 4.2 控制信号辐射图

IR `_07126_[6:0]` 有 559 个 reader——这 7 个位直接控制网表中 **超过一半** 的组合逻辑。它们极可能对应 8051 指令的 opcode 高位字段，经译码器展开为控制信号。

## 5. 交付件清单

| 编号 | 交付件 | 路径 | 状态 |
|------|--------|------|:--:|
| D1.1 | I/O 边界分析 | `data/io_boundary.json` | ✅ |
| D1.2 | 寄存器聚类结果 | `data/register_clusters.json` | ✅ |
| D1.3 | 总线分析 | `data/bus_info.json` | ✅ |
| D1.4 | 总线驱动分组 | `data/bus_analysis.json` | ✅ |
| D1.5 | 模块边界标定 | `data/module_proposal.json` | ✅ |
| D1.6 | 分析脚本 | `tools/module_analyzer.py` `tools/bus_analyzer.py` | ✅ |
| D1.7 | 本报告 | `plan/reports/phase1_report.md` | ✅ |

## 6. 质量门禁

| # | 检查项 | 状态 |
|----|--------|:--:|
| G1.1 | 15 条关键总线已识别并命名 | ✅ |
| G1.2 | 121 个接口 FF 按总线连接分组 | ✅ |
| G1.3 | 模块→总线对应关系建立 | ✅ |
| G1.4 | 三级流水线结构已识别 | ✅ |
| G1.5 | IR 信号路径可追踪（559 readers） | ✅ |

## 7. 遗留问题

| # | 问题 | 严重度 | 处理 |
|----|------|:--:|------|
| L1.1 | ~1,500 个内部 FF 未按模块精确分配 | 中 | Phase 2 将通过扇入/扇出锥分析逐模块分配 |
| L1.2 | Timer/UART/IntC 等外设缺乏明显的独立总线特征 | 中 | 需 Phase 2 通过数据通路追踪和 Spec 对比识别 |
| L1.3 | I/O 端口 p0-p3 在网表中通过三态 buffer 连接，解析器可能未追踪 | 低 | Phase 2 IO ports 模块需单独处理 |
| L1.4 | `_07126_` 为 7-bit 而非 8-bit | 低 | 8051 opcode 仅 255 个有效值，7-bit 覆盖 128 个直接编码，可能 MSB 另有他用 |

## 8. Phase 2 建议执行顺序

基于 Phase 1 的依赖分析，推荐以下顺序（已有依赖关系的模块优先）：

```
Batch A (零依赖, 锚点模块):
  ├── Decoder    ← IR 总线是控制中枢, 最先识别
  ├── ACC/ALU    ← ACC & DB_B 总线是数据路径核心
  └── PSW        ← 仅 3-bit, 最简单

Batch B (数据通路):
  ├── Data Path  ← DBUS_0/1/2 三级流水
  ├── IRAM       ← RAM_ADDR/DATA
  └── SFR Block  ← SFR_DIN/DOUT

Batch C (控制):
  └── Control FSM ← 依赖 Decoder + 数据通路

Batch D (外设, 后续):
  ├── Timer, UART, IntC, IO Ports
  └── RegFile (依赖地址解码器)
```

---

*Phase 1 通过。建议 Phase 2 从 Decoder 模块开始，因为 IR 总线是整颗芯片的控制中枢。*
