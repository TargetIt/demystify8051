# echo_8051 验证方案

## 1. 验证策略总览

```
                    ┌─────────────────┐
                    │  Directed Tests │  ← 模块级，覆盖边界条件
                    └────────┬────────┘
                             ▼
                    ┌─────────────────┐
                    │  Random Tests   │  ← 指令序列随机生成
                    └────────┬────────┘
                             ▼
                    ┌─────────────────┐
                    │   UVM Testbench │  ← 系统级验证环境
                    └────────┬────────┘
                             ▼
                    ┌─────────────────┐
                    │  Gate-Level Sim │  ← 后仿真 + SDF 标注
                    └─────────────────┘
```

## 2. 验证层级

### Level 0 — 模块级验证

每个子模块有独立的 testbench，采用定向测试：

| 模块 | Testbench | 测试项 | 通过标准 |
|------|-----------|--------|---------|
| `alu` | `tb_alu.v` | 所有 ALU 操作（ADD/ADDC/SUBB/MUL/DIV/LOGIC/ROTATE）的输入组合 | 100% 操作覆盖 |
| `decoder` | `tb_decoder.v` | 255 操作码译码正确性 + 未定义操作码处理 | 255/255 opcodes |
| `reg_file` | `tb_reg_file.v` | 4 组寄存器读写、bank 切换 | 全部读写正确 |
| `iram` | `tb_iram.v` | 128B 读写、位寻址区操作 | 全部地址读写正确 |
| `timer` | `tb_timer.v` | T0/T1 4 种模式、溢出中断、门控 | 模式/时序正确 |
| `uart` | `tb_uart.v` | 模式 0-3 发送/接收、波特率生成 | 发送=接收 比对 |
| `intc` | `tb_intc.v` | 5 源中断、2 级优先级、嵌套 | 优先级/向量正确 |
| `io_port` | `tb_io_port.v` | P0-P3 读写、复用功能 | 读写一致 |

### Level 1 — 核级验证

集成 CPU 核 + ROM + RAM + SFR，不包含外设细粒度：

| 测试套件 | 说明 | 工具 |
|---------|------|------|
| `isa_compliance` | 全部 255 操作码执行验证，比对 ACC/PSW/RAM 结果 | Python ISS 比对 |
| `random_sequence` | 随机指令序列，比对 RTL vs C++ ISS | 自动 scoreboard |
| `boundary_test` | 极限条件：栈溢出、中断嵌套、地址回绕 | 直接 testbench |
| `instruction_timing` | 验证每条指令的执行周期数 | 波形检查 |

### Level 2 — 系统级 UVM 验证

```
uvm_env/
├── uvm_agent_in       ← 输入激励代理（指令注入）
├── uvm_agent_out      ← 输出监控代理（端口/内存状态）
├── uvm_scoreboard     ← 自动比对（RTL vs 参考模型）
├── uvm_coverage       ← 功能覆盖率收集
├── uvm_sequences      ← 测试序列库
└── uvm_tests          ← 测试用例
```

UVM 验证项：
- 指令对测试（所有相邻指令对组合）
- 中断随机注入（随机中断源 + 随机时机）
- 外设压力测试（Timer + UART 并发）
- 复位恢复测试
- 电源模式测试（PCON 空闲/掉电模式）

### Level 3 — 门级后仿真

- 综合后网表 + SDF 标注
- min/typ/max corner
- 验证时序收敛
- 功耗估算（SAIF/VCD 标注）

## 3. 覆盖率计划

| 覆盖类型 | 工具 | 目标 |
|---------|------|------|
| Line coverage | Verilator / Icarus | ≥ 95% |
| Toggle coverage | Verilator | ≥ 90% |
| Branch coverage | Verilator | ≥ 90% |
| Condition coverage | Verilator | ≥ 85% |
| FSM state coverage | 直接检查 | 100% |
| Opcode coverage | 功能覆盖组 | 255/255 |
| Interrupt coverage | 功能覆盖组 | 所有中断组合 |
| Cross coverage | 功能覆盖组 | 指令×寻址方式 |

## 4. 参考模型比对流程

```
Step 1: 生成测试向量
  → 随机指令序列生成器 → {opcode, operands}[]

Step 2: 独立执行
  → C++ ISS 执行 → 黄金输出 {ACC, PSW, SP, RAM, SFR}
  → RTL DUT 仿真 → 实际输出 {ACC, PSW, SP, RAM, SFR}

Step 3: 自动比对
  → scoreboard 逐周期比对:
    - ACC 值
    - PSW 标志位 (CY, AC, OV, P)
    - SP 值
    - RAM 内容
    - SFR 关键字段
    - PC 值（间接通过执行流检查）

Step 4: 差异分析
  → 定位第一个差异周期
  → 生成精简复现用例
  → 波形回放调试
```

## 5. 测试用例计数估算

| 类别 | 数量 | 说明 |
|------|------|------|
| 模块 directed tests | ~80 | 每模块 8-15 个定向测试 |
| ISA compliance | 255 | 每个操作码至少 1 个测试 |
| Random sequences | 10,000+ | 自动化随机生成 |
| UVM tests | ~50 | 复杂场景测试 |
| Gate-level tests | ~20 | 关键路径验证 |
| **总计** | **10,000+** | — |
