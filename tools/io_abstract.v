// IO Cell Abstraction for Formal Equivalence
// Replaces Sky130 IO pad cells with simple behavioral equivalents
// that Yosys SAT solver can reason about

// ── Bidirectional IO pads → simple tristate ──
module sky130_fd_sc_hd__lpflow_inputiso1p_1 (input A, input SLEEP, output X);
    assign X = SLEEP ? 1'bz : A;
endmodule

module sky130_fd_sc_hd__lpflow_isobufsrc_1 (input A, input SLEEP, output X);
    assign X = A;
endmodule

// ── Set-dominant FF → regular DFF with SET=1 on reset ──
// dfstp: DFF with SET (asynchronous set to 1). Used for IO ports (reset=0xFF)
// Replace with behavioral DFF that initializes to 1
module sky130_fd_sc_hd__dfstp_2 (input CLK, input D, input SET_B, output Q);
    reg q_reg;
    assign Q = q_reg;
    always @(posedge CLK or negedge SET_B)
        if (!SET_B) q_reg <= 1'b1;
        else        q_reg <= D;
endmodule

// ── Regular DFF with async reset (already works) ──
// These are standard and Yosys handles them via clk2fflogic
// Keep as-is — no override needed

// ── Tristate output buffer → simple wire ──
// (if any exist in the netlist)
