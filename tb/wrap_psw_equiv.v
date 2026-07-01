// PSW Module Equivalence Wrapper
// Maps RTL psw ports to gate-level psw_gate module ports
// Bus mapping from Phase 1: _07104_[2:0] = PSW flags, _07110_[3:0] = CTRL select

module wrap_psw_equiv (
    input wire clk, rst_n,
    input wire [2:0] ctrl,       // _07110_[3:1] = alu_op control
    input wire [2:0] flags_in,   // from ALU (cy, ac, ov)
    input wire write_en,         // psw_write
    output wire [2:0] flags_gold,
    output wire [2:0] flags_gate
);
    // RTL (gold)
    wire [7:0] psw_out_rtl;
    psw gold (
        .clk(clk), .rst_n(rst_n),
        .psw_write(write_en),
        .flags_in(flags_in),
        .flags_out(flags_gold),
        .psw_out(psw_out_rtl)
    );

    // Gate-level extracted module
    psw_gate gate (
        .clk(clk), .rst_n(rst_n),
        ._07104_(flags_gate),
        ._07110_({5'd0, ctrl}),
        // other inputs tied to 0
        ._00099_(1'b0), ._00100_(1'b0), ._00101_(1'b0),
        ._00102_(1'b0), ._00103_(1'b0), ._00104_(1'b0),
        ._00105_(1'b0), ._02291_(1'b0), ._02293_(1'b0),
        ._02302_(1'b0), ._02305_(1'b0), ._06858_(1'b0),
        ._06861_(1'b0), ._07121_(8'd0), ._07122_(1'b0),
        ._07143_(8'd0), ._00391_(1'b0), ._00399_(1'b0),
        ._00407_(1'b0), ._00415_(1'b0), ._00431_(1'b0),
        ._00439_(1'b0), ._00447_(1'b0), ._00455_(1'b0)
    );
endmodule
