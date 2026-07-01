# echo_8051 反向工程项目执行计划

> 版本: v0.1 | 状态: Draft | 最后更新: 2026-07-01

---

## 文档索引

| 文档 | 路径 | 说明 |
|------|------|------|
| 执行计划 | `plan/01_execution_plan.md` | 本文档 — 整体计划与阶段定义 |
| Phase 0 报告 | `plan/reports/phase0_report.md` | 网表解析完成报告 |
| Phase 1 报告 | `plan/reports/phase1_report.md` | 顶层结构识别报告 |
| Phase 2 报告 | `plan/reports/phase2_report.md` | 逐模块反向报告 |
| Phase 3 报告 | `plan/reports/phase3_report.md` | RTL 集成报告 |
| Phase 4 报告 | `plan/reports/phase4_report.md` | 验证报告 |
| 风险登记册 | `plan/risk_register.md` | 全局风险与缓释措施 |
| 问题跟踪 | `plan/issue_tracker.md` | 跨阶段未解决问题 |
| 信号映射表 | `doc/signal_mapping.md` | 匿名连线→功能信号 |

---

## 1. 项目总览

### 1.1 目标

将一份 **56,136 行、8,534 个标准单元的匿名扁平门级网表**，反向还原为 **结构清晰、可读可维护的行为级 RTL 代码**，并通过功能验证确认等价性。

### 1.2 输入基线

| 编号 | 输入件 | 位置 | 描述 |
|------|--------|------|------|
| I-NET | 门级网表 | `input/echo_8051_synth.v` | 56K lines, 8,534 cells, 1,626 FFs |
| I-SPEC | 设计规格书 | `input/design_spec.md` | 原始架构——模块列表、接口、微码方案、SFR 映射 |
| I-REQ | 反向需求 | `requirements/01_reverse_engineering.md` | 项目范围、技术路线、验收标准 |

### 1.3 输出基线

| 编号 | 输出件 | 位置 | 描述 |
|------|--------|------|------|
| O-RTL | 行为级 RTL | `rtl/` | 12 个可综合 Verilog 模块 |
| O-TB | 验证环境 | `tb/` | testbench + ISA 测试套件 |
| O-DOC | 反向文档 | `doc/` | 反向报告、信号映射、模块接口 |
| O-REP | 阶段报告 | `plan/reports/` | 每个阶段的完整报告 |

---

## 2. 阶段总览

```
Phase 0         Phase 1           Phase 2            Phase 3         Phase 4
网表解析    →   顶层结构识别   →   逐模块反向     →   RTL集成     →   验证闭环
(1-2天)         (2-3天)           (5-7天)            (3-4天)         (3-5天)

产出:            产出:             产出:              产出:           产出:
cell graph      模块边界划分     12个模块RTL        顶层RTL         testbench
寄存器清单      rough hierarchy  模块testbench      集成网表        仿真报告
                 信号初步命名     模块验证报告      集成报告        验证报告
```

---

## 3. Phase 0 — 网表解析与基础设施

**目标**: 将网表文件解析为可编程操作的数据结构，识别所有寄存器并建立连接图。

### 3.0 前置条件

| 编号 | 检查项 | 状态 |
|------|--------|:--:|
| PRE0.1 | 网表文件可被标准 Verilog parser 解析 | — |
| PRE0.2 | Sky130 HD 标准单元库功能描述可用 | — |
| PRE0.3 | Python/Yosys 工具链就绪 | — |

### 3.1 子阶段

#### P0.1 — Verilog 网表解析器

| 项 | 内容 |
|------|------|
| **输入** | `input/echo_8051_synth.v` |
| **过程** | 编写 Python 脚本，使用 `pyverilog` 或正则解析 Flat Verilog，提取 module、wire、cell instance、port connection |
| **输出** | `tools/netlist_parser.py` — 网表解析脚本 |
| **验证** | 解析后 instance_count == 8534, wire_count 匹配, DFF_count == 1626 |

#### P0.2 — Cell Graph 构建

| 项 | 内容 |
|------|------|
| **输入** | P0.1 解析结果 |
| **过程** | 构建有向图：节点 = cell/wire/port，边 = pin 连接。区分组合逻辑边（cell→cell via wire）和时序边（FF D→Q） |
| **输出** | `tools/cell_graph.py` + `data/cell_graph.pkl` — 可查询的图数据结构 |
| **验证** | 每个 cell 的 fan-in/fan-out 可遍历，无孤立节点 |

#### P0.3 — 寄存器识别与分类

| 项 | 内容 |
|------|------|
| **输入** | P0.2 的 cell graph |
| **过程** | 提取所有 `dfrtp`/`dfstp`/`dfxtp` 实例，按 fan-out 连接模式分类：<br>— 数据寄存器（fan-out 到组合逻辑再回 FF）<br>— 状态寄存器（fan-out 到控制逻辑）<br>— 流水线寄存器（单级直通） |
| **输出** | `data/register_map.json` — 1,626 个寄存器清单：[instance_name, cell_type, clock_domain, fan_in_count, fan_out_count, connected_ports] |
| **验证** | 寄存器总数 == 1626，时钟和复位连接一致性检查 |

#### P0.4 — 时钟域与复位分析

| 项 | 内容 |
|------|------|
| **输入** | P0.3 寄存器清单 |
| **过程** | 追踪每个 FF 的 CLK 和 RST 引脚，确认统一时钟域（单时钟 `clk`，单复位 `rst_n`），检测是否有门控时钟 |
| **输出** | `data/clock_domain.json` — 时钟域分析结果 |
| **验证** | 所有 FF 时钟来源可追踪到顶层 `clk` 端口 |

### 3.2 Phase 0 交付件

| 编号 | 交付件 | 类型 | 路径 |
|------|--------|------|------|
| D0.1 | 网表解析脚本 | 代码 | `tools/netlist_parser.py` |
| D0.2 | Cell Graph 数据 | 数据 | `data/cell_graph.pkl` |
| D0.3 | 寄存器清单 | 数据 | `data/register_map.json` |
| D0.4 | 时钟域报告 | 数据 | `data/clock_domain.json` |
| D0.5 | Phase 0 报告 | 报告 | `plan/reports/phase0_report.md` |

### 3.3 Phase 0 质量门禁

- [ ] 8,534 个 cell 全部解析，无遗漏
- [ ] 1,626 个寄存器全部识别并标注 cell type
- [ ] 每个寄存器可正向/反向追踪至少 2 级逻辑锥
- [ ] Cell graph 数据结构通过 `assert` 完整性检查

### 3.4 Phase 0 风险与遗留

| # | 风险/问题 | 严重度 | 处理方式 |
|---|----------|:--:|------|
| R0.1 | Sky130 标准单元行为模型缺失 | 低 | 使用 Yosys 内置仿真模型；仅需知道 cell function |
| R0.2 | pyverilog 对大网表解析性能 | 中 | 备选：基于正则的轻量解析器 |
| R0.3 | 网表使用 Verilog-95 语法 | 低 | 语法子集简单，正则可覆盖 |

---

## 4. Phase 1 — 顶层结构识别

**目标**: 将 8,534 个 cell 的扁平网表，按照功能边界划分为 10-12 个逻辑簇，建立模块边界假设。

### 4.1 子阶段

#### P1.1 — I/O 端口反向追踪

| 项 | 内容 |
|------|------|
| **输入** | P0.2 cell graph + 顶层端口列表 (14 ports) |
| **过程** | 从每个顶层端口反向追踪 fan-in 逻辑锥，识别第一级输入逻辑和最后一级输出逻辑。标记"端口相关的 cell 集合" |
| **输出** | `data/io_boundary_cells.json` — 每个端口关联的 cell 集合 |
| **验证** | 每个输出端口可追踪到至少一个 FF 或组合逻辑根节点 |

#### P1.2 — 寄存器功能聚类

| 项 | 内容 |
|------|------|
| **输入** | P0.3 寄存器清单 + P1.1 I/O 关联 |
| **过程** | 对 1,626 个 FF 执行图谱聚类：<br>1. 构建 FF-FF 连接图（weight = 共享的组合逻辑锥大小）<br>2. 应用 Louvain/谱聚类，自动划分为 ~12 个簇<br>3. 将簇大小与 Spec 中模块的寄存器需求对齐 |
| **输出** | `data/register_clusters.json` — 每个 FF 的功能模块归属 |
| **验证** | 簇的数量与 Spec 模块数一致（±2），每个簇的 FF 数量合理 |

#### P1.3 — 功能模块边界标定

| 项 | 内容 |
|------|------|
| **输入** | P1.2 聚类结果 + I-SPEC 模块列表 |
| **过程** | 将自动聚类结果与 Spec 中的 12 个模块手动对齐：<br>— ALU (~200 cells)<br>— Decoder (~300 cells)<br>— Control FSM (~150 cells)<br>— RegFile (~400 cells)<br>— IRAM (~600 cells)<br>— SFR Block (~500 cells)<br>— Timer (~400 cells)<br>— UART (~300 cells)<br>— IntC (~200 cells)<br>— IO Ports (~400 cells)<br>— PROM (~100 cells)<br>— 未分类 (余量) |
| **输出** | `data/module_boundaries.json` — 每个模块的推测 cell 范围 |
| **验证** | 模块间边界 cell 的交叉连接数最小化，交叉连接可解释（总线、控制信号） |

#### P1.4 — 总线与数据通路识别

| 项 | 内容 |
|------|------|
| **输入** | P1.3 模块边界 + cell graph |
| **过程** | 识别 8-bit 宽度的数据总线（8 条并行的相同逻辑路径），标记为 `internal_data_bus`。识别关键控制信号路径 |
| **输出** | `data/bus_signals.json` — 总线信号清单与路由 |
| **验证** | 总线宽度 = 8 bit，连接模块数量 ≥ 5 |

### 4.2 Phase 1 交付件

| 编号 | 交付件 | 类型 | 路径 |
|------|--------|------|------|
| D1.1 | I/O 边界分析 | 数据 | `data/io_boundary_cells.json` |
| D1.2 | 寄存器聚类结果 | 数据 | `data/register_clusters.json` |
| D1.3 | 模块边界标定 | 数据 | `data/module_boundaries.json` |
| D1.4 | 总线信号清单 | 数据 | `data/bus_signals.json` |
| D1.5 | 初步信号命名 | 数据 | `data/signal_naming_v0.json` |
| D1.6 | Phase 1 报告 | 报告 | `plan/reports/phase1_report.md` |

### 4.3 Phase 1 质量门禁

- [ ] 所有 12 个 Spec 模块在网表中定位到对应的 cell 区域
- [ ] 每个模块的 FF 数在合理范围（与 Spec 期望 ±50%）
- [ ] 8-bit 内部数据总线已识别
- [ ] 关键控制信号（alu_op, mem_read, mem_write, pc_ctrl 等）路径初步标记

### 4.4 Phase 1 风险与遗留

| # | 风险/问题 | 严重度 | 处理方式 |
|---|----------|:--:|------|
| R1.1 | 自动聚类结果与 Spec 模块边界不吻合 | 中 | 手动调整，结合 Spec 信号名进行启发式匹配 |
| R1.2 | 综合优化导致模块边界模糊（cross-boundary optimization） | 高 | Yosys `flatten` 后可能无清晰边界。允许相邻模块间有模糊地带，标注为 grey area |
| R1.3 | 某些 Spec 模块在网表中不存在（如 PROM 是行为模型） | 中 | 记录为"未在门级网表中实现"，直接基于 Spec 重写 |
| R1.4 | 网表中存在未在 Spec 中描述的额外逻辑 | 低 | 分析后决策：bug fix / 综合 artifact / 未文档化功能 |

---

## 5. Phase 2 — 逐模块反向工程

**目标**: 对每个模块，从其 cell 集合中提取功能描述，编写等价行为 RTL 和模块级 testbench。

### 5.1 通用子阶段模板（每个模块重复执行）

```
P2.X.1 — 输入准备
P2.X.2 — 数据通路追踪
P2.X.3 — 控制逻辑提取
P2.X.4 — RTL 编写
P2.X.5 — 模块级验证
P2.X.6 — 模块反向报告
```

#### 模板详解

| 子阶段 | 输入 | 过程 | 输出 | 验证 |
|--------|------|------|------|------|
| P2.X.1 输入准备 | 模块边界数据 (`module_boundaries.json`)、cell graph、Spec 中该模块描述 | 确认模块的 cell 范围、I/O 信号列表 | 模块 cell 清单、边界端口清单 | cell 计数 = 预期值 ±10% |
| P2.X.2 数据通路追踪 | 模块 cell 清单、cell graph | 从模块输出反向追踪到输入，标记 datapath cells；对组合逻辑锥做布尔函数抽取 | 数据通路图、关键信号标注 | 8-bit 数据通路一致性 |
| P2.X.3 控制逻辑提取 | 数据通路标注结果 | 追踪控制信号的生成逻辑（decoder/FSM→控制信号），还原真值表/状态转移 | 控制信号真值表、FSM 状态图 | FSM 状态覆盖 100% |
| P2.X.4 RTL 编写 | P2.X.2+P2.X.3 分析结果 | 编写干净的行为级 Verilog-2001 RTL，保持与 Spec 接口一致 | `rtl/<module_name>.v` | Yosys 综合 zero errors |
| P2.X.5 模块级验证 | 模块 RTL + cell graph | 编写 testbench，对比 RTL 与原网表模块的行为（随机输入对比输出） | `tb/tb_<module_name>.v` + 验证日志 | 1000+ 随机测试向量通过 |
| P2.X.6 模块报告 | 全部中间产物 | 记录反向过程、关键发现、遗留问题 | `plan/reports/module_reports/<module>_report.md` | 报告完整性 |

### 5.2 模块执行顺序（按依赖关系）

| 批 | 模块 | 预估 cell | 优先级 | 依赖 |
|----|------|:--------:|:------:|------|
| A | ALU | ~200 | P0 | 无 |
| A | 寄存器组 | ~400 | P0 | 无 |
| A | PSW | ~50 | P0 | ALU |
| B | 内部 RAM (IRAM) | ~600 | P0 | 无 |
| B | SFR Block | ~500 | P0 | 无 |
| C | 译码器 (Decoder) | ~300 | P0 | 无 |
| C | 控制状态机 (Control FSM) | ~150 | P0 | Decoder |
| D | 程序 ROM (PROM) | N/A | P1 | 无（行为模型） |
| D | I/O 端口 (P0-P3) | ~400 | P1 | 无 |
| E | 定时器 (T0/T1) | ~400 | P2 | SFR |
| E | 中断控制器 (IntC) | ~200 | P2 | SFR |
| E | 串行口 (UART) | ~300 | P2 | SFR, Timer |

### 5.3 模块级交付件（每个模块一份）

| 编号 | 交付件 | 路径模板 |
|------|--------|---------|
| DX.1 | 模块 RTL | `rtl/<module>.v` |
| DX.2 | 模块 testbench | `tb/tb_<module>.v` |
| DX.3 | 模块验证日志 | `tb/logs/<module>_verify.log` |
| DX.4 | 模块反向报告 | `plan/reports/module_reports/<module>_report.md` |

### 5.4 Phase 2 风险与遗留

| # | 风险/问题 | 严重度 | 处理方式 |
|---|----------|:--:|------|
| R2.1 | 综合优化将模块间的逻辑混合（cross-boundary optimization） | 高 | 接受部分逻辑无法完美分离；标注 grey area，在 RTL 中保持等价但不强求边界一致 |
| R2.2 | 布尔函数抽取在大逻辑锥上计算爆炸 | 中 | 对深度 >10 的逻辑锥改用仿真验证而非形式化抽取 |
| R2.3 | SFR 地址解码器与大 MUX 难以还原 | 中 | 通过随机读写 + 观察响应反推地址映射 |
| R2.4 | 多周期指令的时序难以还原 | 中 | 依靠控制 FSM 的状态数 + Spec 状态描述推断 |
| R2.5 | 微码 ROM 内容在综合后散落为随机逻辑 | 高 | 通过控制信号的真值表反推微码位宽和字段含义 |

---

## 6. Phase 3 — RTL 集成

**目标**: 将 Phase 2 产出的 12 个独立模块 RTL 集成为完整的 `echo_8051_top`，确认模块间接口一致性。

### 6.1 子阶段

#### P3.1 — 接口一致性检查

| 项 | 内容 |
|------|------|
| **输入** | 12 个模块 RTL + design_spec 接口定义 |
| **过程** | 逐模块检查端口名、位宽、方向是否与 Spec 一致。确认模块间 signal 对应（bus, control, status） |
| **输出** | `data/interface_matrix.csv` — 模块×模块的信号对应矩阵 |
| **验证** | 所有 Spec 定义的 interconnect 有对应信号 |

#### P3.2 — 顶层集成

| 项 | 内容 |
|------|------|
| **输入** | 12 个模块 RTL + 接口矩阵 |
| **过程** | 编写 `echo_8051_top.v`，例化 12 个模块，连接所有信号 |
| **输出** | `rtl/echo_8051_top.v` |
| **验证** | Yosys 综合 zero errors (hierarchy check) |

#### P3.3 — 集成仿真

| 项 | 内容 |
|------|------|
| **输入** | 顶层 RTL + 简易 testbench |
| **过程** | 运行简单程序（NOP loop, MOV, ADD），确认时钟/复位/取指 行为正确 |
| **输出** | `tb/tb_echo_8051_top.v` + 集成仿真日志 |
| **验证** | 基本指令序列执行正确，无明显信号 X/Z |

### 6.2 Phase 3 交付件

| 编号 | 交付件 | 路径 |
|------|--------|------|
| D3.1 | 接口矩阵 | `data/interface_matrix.csv` |
| D3.2 | 顶层 RTL | `rtl/echo_8051_top.v` |
| D3.3 | 顶层 testbench | `tb/tb_echo_8051_top.v` |
| D3.4 | 集成仿真日志 | `tb/logs/integration_sim.log` |
| D3.5 | Phase 3 报告 | `plan/reports/phase3_report.md` |

---

## 7. Phase 4 — 验证闭环

**目标**: 系统级验证，确认 RTL 与原始网表在所有 255 个 8051 操作码上行为等价。

### 7.1 子阶段

#### P4.1 — ISA 合规测试

| 项 | 内容 |
|------|------|
| **输入** | 顶层 RTL + Python/C++ ISS |
| **过程** | 对 255 个操作码逐一生成测试向量，RTL 和 ISS 同时执行，比对 ACC/PSW/RAM/SFR |
| **输出** | `tb/isa_tests/` — 255 个 hex 测试文件 |
| **验证** | 255/255 操作码行为一致 |

#### P4.2 — 随机指令序列测试

| 项 | 内容 |
|------|------|
| **输入** | 顶层 RTL + ISS |
| **过程** | 生成 10,000+ 随机指令序列，自动比对 |
| **输出** | 仿真报告（pass/fail 统计、覆盖率） |
| **验证** | 随机测试通过率 ≥ 99.9% |

#### P4.3 — 中断与外设测试

| 项 | 内容 |
|------|------|
| **输入** | 顶层 RTL |
| **过程** | 中断注入测试、Timer 模式测试、UART 回环测试 |
| **输出** | 外设验证报告 |
| **验证** | 中断优先级/向量正确，Timer 溢出时序正确 |

#### P4.4 — 形式等价性检查

| 项 | 内容 |
|------|------|
| **输入** | RTL + 原始网表 |
| **过程** | 使用 Yosys `equiv_*` 命令进行组合逻辑等价性检查 |
| **输出** | 等价性检查报告 |
| **验证** | equiv_status == proven |

### 7.2 Phase 4 交付件

| 编号 | 交付件 | 路径 |
|------|--------|------|
| D4.1 | ISA 测试套件 | `tb/isa_tests/` |
| D4.2 | 随机测试脚本 | `tb/random_test.py` |
| D4.3 | 覆盖率报告 | `tb/logs/coverage_report.txt` |
| D4.4 | 等价性检查报告 | `tb/logs/equiv_check.log` |
| D4.5 | 最终验证报告 | `plan/reports/phase4_report.md` |

---

## 8. 全局基础设施

### 8.1 脚本工具清单

| 脚本 | 路径 | 功能 |
|------|------|------|
| 网表解析器 | `tools/netlist_parser.py` | 解析 Flat Verilog → Python dict |
| Cell Graph | `tools/cell_graph.py` | 构建/查询 cell 连接图 |
| 寄存器分析 | `tools/register_analyzer.py` | FF 识别、分类、聚类 |
| 逻辑锥提取 | `tools/cone_extractor.py` | 从给定 FF/port 提取 fan-in cone |
| 布尔函数抽取 | `tools/bool_extractor.py` | 组合逻辑锥 → 真值表/表达式 |
| 自动 testbench 生成 | `tools/tb_generator.py` | 从模块 RTL 自动生成对比验证 TB |
| ISS Runner | `tools/iss_runner.py` | 调用 Python/C++ ISS 执行 hex 文件 |

### 8.2 目录结构

```
demystify8051/
├── input/                        # 原始输入 (read-only)
│   ├── design_spec.md
│   └── echo_8051_synth.v
├── requirements/                 # 需求文档
│   └── 01_reverse_engineering.md
├── plan/                         # 计划与报告
│   ├── 01_execution_plan.md     ← 本文档
│   ├── risk_register.md
│   ├── issue_tracker.md
│   └── reports/
│       ├── phase0_report.md
│       ├── phase1_report.md
│       ├── phase2_report.md
│       ├── phase3_report.md
│       ├── phase4_report.md
│       └── module_reports/
│           ├── alu_report.md
│           ├── decoder_report.md
│           └── ...
├── tools/                        # 工具脚本
├── data/                         # 中间数据
├── rtl/                          # 产出 RTL
├── tb/                           # 验证环境
│   ├── logs/
│   └── isa_tests/
└── doc/                          # 最终文档
    ├── reverse_engineering_report.md
    ├── module_interface.md
    └── signal_mapping.md
```

---

## 9. 阶段执行状态

| 阶段 | 状态 | 开始 | 完成 | 报告 |
|------|:--:|------|------|------|
| Phase 0 — 网表解析 | 🔴 未开始 | — | — | — |
| Phase 1 — 顶层识别 | 🔴 未开始 | — | — | — |
| Phase 2 — 逐模块反向 | 🔴 未开始 | — | — | — |
| Phase 3 — RTL 集成 | 🔴 未开始 | — | — | — |
| Phase 4 — 验证闭环 | 🔴 未开始 | — | — | — |

---

*本文档将在每个阶段/子阶段完成后更新对应的执行状态、输出路径和遗留问题。*
