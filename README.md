# demystify8051

Completely anonymous, fully flattened gate-level netlist of an 8051-compatible microcontroller, synthesized to SkyWater 130nm (SKY130 HD) standard cells, along with the original design specification documents.

## Contents

| File | Description |
|------|-------------|
| `echo_8051_synth.v` | Anonymous flat gate-level netlist (SKY130 HD, 8,544 cells) |
| `area_report.txt` | Yosys synthesis area/cell statistics |
| `synthesis_report.md` | Synthesis methodology and results |
| `design_spec.md` | 8051 microarchitecture design specification |
| `requirements.md` | Original project requirements |
| `verification_plan.md` | Verification methodology and test plan |
| `issues.md` | Known issues and errata |
| `research.md` | Background research and references |
| `delivery_standards.md` | Physical implementation delivery standards |

## Netlist Properties

- **Process**: SkyWater 130nm (sky130_fd_sc_hd)
- **Cells**: 8,544 standard cells
- **Flip-flops**: 1,626
- **Area**: 76,013 um2
- **Clock**: 50 MHz target (cell-delay clean at synthesis level)
- **Anonymization**: All internal nets renamed to `_00000_`..`_XXXXX_`; single flat module; zero functional hierarchy

## Source

Generated from the [echo_8051](https://github.com/TargetIt/echo_8051) project.
