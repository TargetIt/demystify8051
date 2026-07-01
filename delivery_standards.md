# echo_8051 交付标准

## 各阶段交付件清单

### Phase 0 — Spec
| 交付件 | 格式 | 说明 |
|--------|------|------|
| 设计方案 | design_spec.md | 架构设计、模块分解、接口定义 |
| 验证方案 | verification_plan.md | 验证策略、覆盖率计划 |
| 交付标准 | delivery_standards.md | 本文件 |

### Phase 1 — RTL
| 交付件 | 格式 | 说明 |
|--------|------|------|
| 全部 RTL 源码 | .v | Verilog-2001 可综合风格 |
| 模块接口文档 | .md | 每个模块的端口/功能说明 |
| RTL 风格检查报告 | .log | Verilator lint 通过 |

### Phase 2 — Simulation
| 交付件 | 格式 | 说明 |
|--------|------|------|
| 模块级 testbench | .v | 每模块独立验证 |
| 系统级 testbench | .v / .sv | CPU 核集成验证 |
| UVM 环境 | .sv | UVM agent/scoreboard/coverage |
| 仿真报告 | .md | 覆盖率、pass/fail 统计 |
| Python ISS 模型 | .py | 指令集仿真器 |
| C++ ISS 模型 | .cpp/.h | 高性能参考模型 |
| 交叉验证报告 | .md | RTL vs ISS 比对结果 |

### Phase 3 — Synthesis
| 交付件 | 格式 | 说明 |
|--------|------|------|
| Yosys 综合脚本 | .tcl | 综合约束与流程 |
| 门级网表 | .v | 综合后网表 |
| SDF | .sdf | 标准延时格式 |
| STA 报告 | .rpt | 静态时序分析 |
| 综合报告 | .md | 面积/时序/功耗摘要 |
| 综合日志 | .log | 完整综合日志 |

### Phase 4 — PnR
| 交付件 | 格式 | 说明 |
|--------|------|------|
| OpenLane 配置 | config.tcl | PnR 约束（面积/密度/时序） |
| DEF 版图 | .def | 设计交换格式 |
| PnR 网表 | .v | 后 PnR 门级网表 |
| SDF (multi-corner) | .sdf | min/nom/max × fast/typ/slow |
| SPEF | .spef | 寄生参数提取 |
| 版图截图 | .png | GDS 全貌 + 逐层 + 细节 |

### Phase 5 — Physical Verification
| 交付件 | 格式 | 说明 |
|--------|------|------|
| DRC 报告 | .rpt | Magic + KLayout, violations=0 |
| LVS 报告 | .rpt | net/device match, errors=0 |
| Antenna 报告 | .rpt | 天线效应检查 |
| 可制造性报告 | .rpt | 密度/填充检查 |

### Phase 6 — GDS
| 交付件 | 格式 | 说明 |
|--------|------|------|
| **GDSII 版图** | .gds | 最终流片文件 |
| LEF 库视图 | .lef | IP 集成用 |
| Liberty 时序库 | .lib | 时序模型 |
| SPICE 网表 | .spice | LVS 用 |
| 最终签核报告 | .md | 全流程质量门禁 |

## 质量门禁

| 门禁项 | 标准 | 测量方法 |
|--------|------|---------|
| RTL 风格 | Verilator lint 0 warnings | Verilator --lint-only |
| 功能正确性 | 全部测试用例 PASS | 仿真报告 |
| 代码覆盖率 | ≥ 95% line, ≥ 90% toggle | Verilator coverage |
| 功能覆盖率 | ≥ 95% | UVM covergroup |
| 综合通过 | Yosys 综合 0 errors | 综合日志 |
| 时序收敛 | WNS ≥ 0, WHS ≥ 0 | STA 报告 |
| DRC | 0 violations | Magic/KLayout DRC |
| LVS | 0 mismatches | Magic/KLayout LVS |
| Antenna | 0 violations | Magic antenna check |
| GDS 一致性 | Magic ↔ KLayout XOR = 0 | XOR comparison |

## 不交付项

以下内容不作为交付件，但保留在工作目录中：
- 中间运行日志（OpenLane runs/）
- 仿真波形文件（*.vcd）
- 临时构建产物（*.o, *.vvp）
