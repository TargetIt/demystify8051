# echo_8051 遗留问题与待办

## 高优先级

| # | 问题 | 影响 | 修复方向 |
|---|------|------|---------|
| 1 | **时序违例 -0.76ns** (Slowest corner, 50MHz) | 芯片只能跑 ~48MHz | 放宽时钟到 22ns，或优化关键路径、加流水级 |
| 2 | **RTL bit-address 错误** | SETB/CLR/CPL bit, JB/JNB/JBC 对 SFR 位操作地址映射不对 (`bit_addr>>3` → 应为 `bit_addr&0xF8`) | RTL `cpu_core.v` 中 bit 操作 handler 需修复 |
| 3 | **RTL PSW 奇偶位未实现** | 依赖 Parity flag 的程序出错 | ALU 写 ACC 时同步更新 PSW.P |

## 中优先级

| # | 问题 | 影响 | 修复方向 |
|---|------|------|---------|
| 4 | **交叉验证 1 条差异** (42/43) | CLR A→POP ACC 连续执行时 ACC 中间值不可见 | 不影响最终结果，ISS 模型需同步 RTL 的 NBA 时序 |
| 5 | **UART RX 未完成** | Model + RTL UART 接收均为简化版 | 补全 RX 移位寄存器 + baud rate 采样 |
| 6 | **RETI 中断返回未充分测试** | 中断嵌套可能异常 | 补 RETI 完整测试 + 中断嵌套用例 |
| 7 | **DJNZ direct 未充分测试** | `DJNZ direct, rel` handler 可能存在边界问题 | 补交叉验证用例 |
| 8 | **MOV A,direct 读 SFR 有 1 周期延迟** | 连续 SFR 操作时读到旧值 | 加 SFR read forwarding 或 2-cycle SFR read |

## 低优先级

| # | 问题 | 影响 | 修复方向 |
|---|------|------|---------|
| 9 | **Timer mode 0/1 位宽不一致** | mode 0 用 10bit 代替 13bit | 修正 `{th[7:0], tl[4:0]}` = 13bit |
| 10 | **C++ model UART 简化** | 无 TX/RX 状态机 | 参照 Python model 补全 |
| 11 | **System demo INT0 按钮未接入** | 按钮仅更新 P3.2，未触发实际中断 | 连接 INT0 → ISR 方向反转 |
| 12 | **OpenLane report 生成崩溃** | `IndexError: list index out of range` 在 power report | OpenLane v1.1.1 bug, 升级或手动提取 metrics |

## 未覆盖的 RTL 操作码 (约 90 个 NOP 等效)

Intel 8051 有 255 个有效操作码。RTL 覆盖了全部 165 个真实指令，剩余约 90 个是 Intel 未定义的操作码（官方手册标记为保留），在 RTL 中作为 NOP 处理。这些不需要实现。

## Phase 2 UVM 验证（未开始）

- SystemVerilog UVM 环境搭建
- UVM agent / scoreboard / coverage
- RTL vs ISS 交叉验证自动化
- 代码覆盖率 ≥ 95%
- 功能覆盖率 ≥ 95%
