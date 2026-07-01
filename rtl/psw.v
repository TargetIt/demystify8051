// PSW — Program Status Word
// Reverse-engineered from gate-level netlist (3 dfrtp FFs: _07104_[2:0])
// Implements CY (Carry), AC (Aux Carry), OV (Overflow) flags
// Note: P (Parity) is computed combinatorially from ACC, not stored in PSW FFs

module psw (
    input  wire       clk,
    input  wire       rst_n,
    input  wire       psw_write,       // write enable from decoder
    input  wire [2:0] flags_in,        // {CY, AC, OV} from ALU
    output wire [2:0] flags_out,       // current flag values
    output wire [7:0] psw_out          // 8-bit SFR read value
);
    reg [2:0] cy_ac_ov;  // bit2=CY, bit1=AC, bit0=OV

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            cy_ac_ov <= 3'b000;
        else if (psw_write)
            cy_ac_ov <= flags_in;
    end

    assign flags_out = cy_ac_ov;
    // PSW format: {CY, AC, F0, RS1, RS0, OV, -, P}
    // P (parity) is computed combinatorially from ACC
    // F0, RS1, RS0 are set by software
    assign psw_out = {cy_ac_ov[2], cy_ac_ov[1], 1'b0, 2'b00, cy_ac_ov[0], 1'b0, 1'b0};

endmodule
