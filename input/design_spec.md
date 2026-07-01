# echo_8051 设计方案

## 1. 顶层架构

```
┌──────────────────────────────────────────────────────────────┐
│                       echo_8051 Top                          │
│  ┌─────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐     │
│  │   CPU   │  │  Program │  │  Internal │  │  SFR     │     │
│  │   Core  │  │  ROM     │  │  RAM      │  │  Block   │     │
│  │         │  │  4KB     │  │  128B     │  │  128B    │     │
│  └────┬────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘     │
│       │            │             │             │            │
│  ┌────┴────────────┴─────────────┴─────────────┴────┐      │
│  │              Internal Data Bus (8-bit)            │      │
│  └────┬────────────┬─────────────┬─────────────┬────┘      │
│  ┌────┴────┐  ┌────┴────┐  ┌─────┴──────┐  ┌───┴──────┐   │
│  │ Timer   │  │  UART   │  │ Interrupt  │  │ I/O Port │   │
│  │ T0 + T1 │  │  Serial │  │ Controller │  │ P0-P3    │   │
│  └─────────┘  └─────────┘  └────────────┘  └──────────┘   │
└──────────────────────────────────────────────────────────────┘
```

## 2. CPU 核微架构

### 2.1 数据通路

```
PC[15:0] ──→ Program ROM ──→ Instruction Register ──→ Decoder
                                                        │
                    ┌───────────────────────────────────┤
                    ▼                                   ▼
              Control FSM                        Immediate/Address
                    │                                   │
        ┌───────────┼───────────┐                      │
        ▼           ▼           ▼                      │
     ALU_op     RegFile     Memory_sel                  │
        │        (4 banks)     │                       │
        ▼           │          ▼                       │
   ┌─────────┐      │     ┌─────────┐                  │
   │   ALU   │◄─────┼────►│  RAM    │                  │
   │  8-bit  │      │     │  SFR    │                  │
   └────┬────┘      │     └────┬────┘                  │
        │           │          │                       │
        ▼           ▼          ▼                       │
   ┌──────────────────────────────────┐                │
   │        Internal Data Bus          │                │
   └──────────────────────────────────┘                │
```

### 2.2 状态机

经典的 8051 取指-执行状态机（参考 OC8051）：

```
FETCH ──→ DECODE ──→ EXECUTE ──→ WRITEBACK
  ▲                                    │
  └────────────────────────────────────┘
```

- **FETCH**: PC → ROM, 读取操作码
- **DECODE**: 操作码 → 微码 ROM → 控制信号
- **EXECUTE**: ALU 运算, 数据访存, 外设操作
- **WRITEBACK**: 结果写回寄存器/RAM/SFR

对于多字节指令（2-3 字节），FETCH 阶段根据需要读入操作数。

### 2.3 微码方案

采用微码 ROM 实现指令译码（参考 R8051 微码方案）：

- 微码宽度：24 位控制信号
- 微码深度：256 字（按操作码索引）
- 控制信号包括：
  - `alu_op[3:0]` — ALU 操作选择
  - `src_a_sel[1:0]` — 操作数 A 来源（ACC / 立即数 / RAM / SFR）
  - `src_b_sel[2:0]` — 操作数 B 来源（B / 立即数 / R0-R7 / @Ri / RAM）
  - `dst_sel[1:0]` — 结果目标（ACC / RAM / SFR / PC）
  - `mem_read` / `mem_write` — 存储器读写
  - `pc_op[1:0]` — PC 控制（+1 / jump / call / ret）
  - `flag_update` — PSW 更新使能
  - `next_state[1:0]` — 下一状态

## 3. 模块分解

### 3.1 模块列表

| 模块 | 文件名 | 功能 |
|------|--------|------|
| `echo_8051_top` | `echo_8051_top.v` | 顶层集成 |
| `cpu_core` | `cpu_core.v` | CPU 核（ALU + 控制 + 寄存器组） |
| `alu` | `alu.v` | 8 位算术逻辑单元 |
| `decoder` | `decoder.v` | 指令译码器（微码 ROM） |
| `control_fsm` | `control_fsm.v` | 主控制状态机 |
| `reg_file` | `reg_file.v` | 寄存器组（4 banks × 8 regs） |
| `psw` | `psw.v` | 程序状态字 |
| `iram` | `iram.v` | 128B 内部 RAM |
| `sfr_block` | `sfr_block.v` | SFR 寄存器组 |
| `prom` | `prom.v` | 4KB 程序 ROM |
| `timer` | `timer.v` | T0/T1 定时计数器 |
| `uart` | `uart.v` | 串行口 |
| `intc` | `intc.v` | 中断控制器 |
| `io_ports` | `io_ports.v` | P0-P3 I/O 端口 |

### 3.2 ALU 设计

```
         ┌─────────────────────┐
  A[7:0] │                     │
  ──────►│                     │
  B[7:0] │   8-bit ALU         │──────► result[7:0]
  ──────►│                     │
  op[3:0]│   ADD, ADDC, SUBB   │──────► flags (CY, AC, OV)
  ──────►│   MUL, DIV          │
  CY_in  │   ANL, ORL, XRL     │
  ──────►│   INC, DEC, DA      │
         │   RL, RLC, RR, RRC  │
         │   SWAP, CLR, CPL    │
         └─────────────────────┘
```

### 3.3 译码器设计

```
  opcode[7:0] ──────► ucode_rom[255][23:0] ──────► control_signals[23:0]
                                         │
                                         ├─► alu_op[3:0]
                                         ├─► src_sel[5:0]
                                         ├─► dst_sel[1:0]
                                         ├─► mem_ctrl[1:0]
                                         ├─► pc_ctrl[1:0]
                                         ├─► flag_update
                                         └─► next_state[1:0]
```

## 4. 接口定义

### 4.1 顶层端口

| 信号 | 方向 | 宽度 | 说明 |
|------|------|------|------|
| `clk` | input | 1 | 系统时钟 |
| `rst_n` | input | 1 | 异步复位，低有效 |
| `ea_n` | input | 1 | 外部访问使能（低=外部ROM） |
| `ale` | output | 1 | 地址锁存使能 |
| `psen_n` | output | 1 | 程序存储使能 |
| `p0` | bidir | 8 | 端口 0（地址/数据复用） |
| `p1` | bidir | 8 | 端口 1 |
| `p2` | bidir | 8 | 端口 2（高位地址） |
| `p3` | bidir | 8 | 端口 3（特殊功能） |

### 4.2 SFR 地址映射

| 地址 | SFR | 说明 |
|------|-----|------|
| 0x80 | P0 | 端口 0 |
| 0x81 | SP | 栈指针 |
| 0x82 | DPL | 数据指针低字节 |
| 0x83 | DPH | 数据指针高字节 |
| 0x87 | PCON | 电源控制 |
| 0x88 | TCON | 定时器控制 |
| 0x89 | TMOD | 定时器模式 |
| 0x8A | TL0 | 定时器 0 低字节 |
| 0x8B | TL1 | 定时器 1 低字节 |
| 0x8C | TH0 | 定时器 0 高字节 |
| 0x8D | TH1 | 定时器 1 高字节 |
| 0x90 | P1 | 端口 1 |
| 0x98 | SCON | 串行口控制 |
| 0x99 | SBUF | 串行数据缓冲 |
| 0xA0 | P2 | 端口 2 |
| 0xA8 | IE | 中断使能 |
| 0xB0 | P3 | 端口 3 |
| 0xB8 | IP | 中断优先级 |
| 0xD0 | PSW | 程序状态字 |
| 0xE0 | ACC | 累加器 |
| 0xF0 | B | B 寄存器 |

## 5. 验证方案

### 5.1 验证层次

```
Level 0: 模块级验证 (directed test)
  ├── alu_tb     — 所有 ALU 操作测试
  ├── decoder_tb — 所有操作码译码测试
  ├── timer_tb   — 4 种模式测试
  ├── uart_tb    — 4 种波特率模式测试
  └── intc_tb    — 中断优先级/嵌套测试

Level 1: 核级验证 (directed + random)
  ├── cpu_tb     — 指令级随机测试
  └── isa_tb     — ISA 合规测试套件

Level 2: 系统级验证 (UVM)
  ├── uvm_env    — UVM 验证环境
  ├── ref_model  — Python/C++ 黄金参考模型
  └── scoreboard — 自动比对

Level 3: 后仿真 (gate-level)
  ├── gl_sim     — 门级网表仿真 + SDF 标注
  └── power_est  — 功耗估算
```

### 5.2 黄金参考模型比对

```
  ┌──────────┐     ┌──────────┐
  │ RTL DUT  │     │ C++ ISS  │
  └────┬─────┘     └────┬─────┘
       │                │
       │  (相同输入)      │
       ▼                ▼
  ┌──────────┐     ┌──────────┐
  │ 输出抓取  │ ─── │ 输出抓取  │
  └────┬─────┘     └────┬─────┘
       │                │
       └───────┬────────┘
               ▼
        ┌────────────┐
        │ Scoreboard │ → PASS/FAIL
        └────────────┘
```

### 5.3 覆盖率目标

| 覆盖率类型 | 目标 |
|-----------|------|
| 代码覆盖率 (line) | ≥ 95% |
| 代码覆盖率 (toggle) | ≥ 90% |
| 条件覆盖率 (condition) | ≥ 90% |
| 功能覆盖率 (spec-based) | ≥ 95% |
| 指令覆盖率 | 255/255 操作码 |
| 中断覆盖率 | 所有优先级组合 |

## 6. 交付标准

| 交付件 | 标准 | 验收方法 |
|--------|------|---------|
| RTL 源码 | Verilog-2001, 可综合 | Yosys 综合通过 |
| ISS 模型 | Python + C++, 周期精确 | 与 RTL 交叉验证一致 |
| 验证报告 | 覆盖率达标 | 覆盖率报告 |
| 综合网表 | Sky130 门级网表 | 综合 + STA 通过 |
| PnR 版图 | DEF + GDSII | DRC/LVS clean |
| 时序库 | LIB (NLDM/CCS) | 静态时序分析通过 |
| 物理验证 | DRC/LVS/ANT clean | Magic + KLayout 报告 |

## 7. 关键指标

| 指标 | 目标值 | 备注 |
|------|--------|------|
| 工艺节点 | SkyWater 130nm | sky130A |
| 时钟频率 | ≥ 50 MHz | 12T 模式, 20ns period |
| MIPS | ~4.2 MIPS | 50MHz / 12 |
| 芯片面积 | < 1.0 mm² | Core area |
| 功耗 | < 50 mW | @ 50 MHz, Typical corner |
| 门数 | ~8K-12K gates | 不含 ROM |
| ROM 面积 | ~0.15 mm² | 4KB |
