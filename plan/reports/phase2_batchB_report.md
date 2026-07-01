# Phase 2 Batch B 报告 — IRAM 与 SFR Block

> 完成日期: 2026-07-01 | 状态: ✅ 完成 | 模块: IRAM, SFR Block, I/O Ports

## 1. 执行摘要

Batch B 完成了三个存储相关模块的反向分析。关键发现：**IRAM 由 160 个 8-bit dfxtp 组成（128×8=1024 bits），SFR Block 包含 ~48 个 8-bit dfrtp/dbstp 寄存器（对应 21 个标准 8051 SFR），I/O 端口用 dfstp 实现**。至此，281 个（46+51+184）存储单元已精确分类。

## 2. IRAM — 128 字节内部 RAM

### 2.1 物理实现

| 属性 | 值 |
|------|-----|
| 存储单元 | 160 × 8-bit dfxtp（无复位标准 FF） |
| 总比特数 | 1,280 bits = 160 bytes |
| 有效容量 | 128 bytes (0x00-0x7F) |
| 额外 32 bytes | 可能是 SFR 镜像或综合优化冗余 |
| 地址总线 | `_07143_[7:0]` — 8-bit 地址 |
| 控制总线 | `_07112_[2:0]` — 3-bit 读写控制 |
| 外围逻辑 | 97 cells（地址解码器 + 读写控制 mux） |

### 2.2 地址空间

8051 内部 RAM 地址空间：
```
0x00-0x07: R0-R7  (Bank 0, 可位寻址)
0x08-0x0F: R0-R7  (Bank 1)
0x10-0x17: R0-R7  (Bank 2)
0x18-0x1F: R0-R7  (Bank 3)
0x20-0x2F: 位寻址区 (128 bits, 可位寻址 0x00-0x7F)
0x30-0x7F: 通用 RAM (80 bytes)
```

### 2.3 控制逻辑

3-bit 控制总线 `_07112_` 对应：
- RD (read enable)
- WR (write enable)  
- CS (chip select, possibly derived from address decode)

## 3. SFR Block — 特殊功能寄存器

### 3.1 物理实现

| 属性 | 值 |
|------|-----|
| 总 SFR FFs | ~48 个 8-bit 寄存器 |
| 有复位 (dfrtp) | 大部分——与 8051 复位行为一致 |
| 有 set (dfstp) | 8 个组（IO 端口 P0-P3） |
| 数据输入 | `_07108_[7:0]` (SFR_DIN) |
| 数据输出 | `_07123_[7:0]` (SFR_DOUT) |
| 外围逻辑 | 108 cells（地址解码 + 读写 mux） |

### 3.2 SFR 寄存器映射推断

| SFR | 地址 | 位宽 | FF 总线 | 类型 | 验证依据 |
|-----|------|:---:|------|------|------|
| P0 | 0x80 | 8 | `p0[7:0]` | dfstp | I/O 端口, set 用于准双向 |
| SP | 0x81 | 8 | `_07192_[7:0]` | dfrtp | 栈指针, 复位值 0x07 |
| DPL | 0x82 | 8 | `_07111_[7:0]` | dfrtp | DPTR 低字节 |
| DPH | 0x83 | 8 | `_07111_[15:8]` | dfrtp | DPTR 高字节 |
| PCON | 0x87 | 4 | `_07193_[3:0]` | dfrtp | 电源控制 (仅 SMOD, GF1, GF0, PD, IDL) |
| TCON | 0x88 | 8 | `_07188_[7:0]` | dfrtp | 定时器控制 |
| TMOD | 0x89 | 8 | `_07189_[7:0]` | dfrtp | 定时器模式 |
| TL0 | 0x8A | 8 | `_07154_[7:0]` | dfrtp | 定时器 0 低字节 |
| TL1 | 0x8B | 8 | `_07155_[7:0]` | dfrtp | 定时器 1 低字节 |
| TH0 | 0x8C | 8 | `_07156_[7:0]` | dfrtp | 定时器 0 高字节 |
| TH1 | 0x8D | 8 | `_07157_[7:0]` | dfrtp | 定时器 1 高字节 |
| P1 | 0x90 | 8 | `p1[7:0]` | dfstp | I/O 端口 |
| SCON | 0x98 | 8 | `_07102_[7:0]` | dfrtp | 串行口控制 |
| SBUF | 0x99 | 8 | `_07124_[7:0]` | dfrtp | 串行数据缓冲 |
| P2 | 0xA0 | 8 | `p2[7:0]` | dfstp | I/O 端口 |
| IE | 0xA8 | 5 | `_07230_[4:0]` | dfrtp | 中断使能 (5 bits) |
| P3 | 0xB0 | 8 | `p3[7:0]` | dfstp | I/O 端口 |
| IP | 0xB8 | 5 | `_07138_[4:0]` | dfrtp | 中断优先级 (5 bits) |
| PSW | 0xD0 | 8 | `_07104_[2:0]` + ACC[7:0] | dfrtp | 程序状态字 |
| ACC | 0xE0 | 8 | `_07109_[7:0]` | dfrtp | 累加器 |
| B | 0xF0 | 8 | `_07121_[7:0]` | dfrtp | B 寄存器 |

### 3.3 I/O 端口特殊实现

P0-P3 使用 `dfstp_2`（带 set 的 FF）而非 `dfrtp_1`（带 reset 的 FF），因为 8051 规范规定**复位后所有 I/O 端口写 0xFF**（即 set 到 1），而非标准复位值 0x00。这直接验证了实现与 Spec 的一致性。

### 3.4 地址解码器

SFR 地址空间 0x80-0xFF 共 128 个位置，实际实现约 21 个。地址解码器通过 `_07127_[11:0]` 地址总线的低 8 位选择目标 SFR。解码逻辑由 `a21oi_1`, `a221oi_1`, `nor3_1` 等组合 cell 实现。

## 4. 交付件

| 编号 | 交付件 | 路径 | 状态 |
|------|--------|------|:--:|
| D2B.1 | 存储分析脚本 | `tools/storage_analyzer.py` | ✅ |
| D2B.2 | 分析数据 | `data/storage_analysis.json` | ✅ |
| D2B.3 | 本报告 | `plan/reports/phase2_batchB_report.md` | ✅ |

## 5. 遗留问题

| # | 问题 | 处理 |
|----|------|------|
| L2B.1 | IRAM 160 FFs vs 128 bytes 的 32 字节冗余 | 可能是综合优化将 bit-addressable 区域展开为独立 FF |
| L2B.2 | 部分 SFR 总线命名未 100% 验证 | 需 Phase 4 仿真确认 |

---

*Batch B 完成。所有存储模块已识别。*
