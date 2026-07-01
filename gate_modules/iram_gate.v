// Auto-extracted: iram (19 cells)
module iram_gate (
    input _02087_,
    input _02484_,
    input _02617_,
    input _02657_,
    input _02719_,
    input _02755_,
    input _02776_,
    input _03087_,
    input clk,
    input rst_n,
    output _00000_,
    output _02030_,
    output _02619_,
    output _02620_,
    output _02621_,
    output _02636_,
    output _02638_,
    output _02778_,
    output _02781_,
    output _03086_,
    output [2:0] _07112_,
    input clk, input rst_n
);
  wire _00107_;
  wire _00108_;
  wire _00109_;
  wire _02759_;
  wire _03088_;
  wire _06708_;
  sky130_fd_sc_hd__nand2b_1 _07619_ (
    .A_N(_07112_[2]),
    .B(_07112_[1]),
    .Y(_02030_)
  );
  sky130_fd_sc_hd__lpflow_isobufsrc_1 _08208_ (
    .A(_07112_[1]),
    .SLEEP(_07112_[0]),
    .X(_02619_)
  );
  sky130_fd_sc_hd__nor2_1 _08209_ (
    .A(_07112_[0]),
    .B(_02030_),
    .Y(_02620_)
  );
  sky130_fd_sc_hd__nand2b_1 _08210_ (
    .A_N(_07112_[2]),
    .B(_02619_),
    .Y(_02621_)
  );
  sky130_fd_sc_hd__nand2b_1 _08225_ (
    .A_N(_07112_[1]),
    .B(_07112_[0]),
    .Y(_02636_)
  );
  sky130_fd_sc_hd__lpflow_inputiso1p_1 _08227_ (
    .A(_07112_[2]),
    .SLEEP(_02636_),
    .X(_02638_)
  );
  sky130_fd_sc_hd__nand2_1 _08348_ (
    .A(_02087_),
    .B(_02657_),
    .Y(_02759_)
  );
  sky130_fd_sc_hd__lpflow_inputiso1p_1 _08367_ (
    .A(_02719_),
    .SLEEP(_02776_),
    .X(_02778_)
  );
  sky130_fd_sc_hd__nor3_1 _08370_ (
    .A(_07112_[1]),
    .B(_07112_[2]),
    .C(_07112_[0]),
    .Y(_02781_)
  );
  sky130_fd_sc_hd__clkinv_1 _08371_ (
    .A(_02781_),
    .Y(_00000_)
  );
  sky130_fd_sc_hd__nand2_1 _08691_ (
    .A(_02617_),
    .B(_02620_),
    .Y(_03086_)
  );
  sky130_fd_sc_hd__o221ai_1 _08692_ (
    .A1(_02621_),
    .A2(_02759_),
    .B1(_02778_),
    .B2(_02638_),
    .C1(_03086_),
    .Y(_00108_)
  );
  sky130_fd_sc_hd__nand3_1 _08694_ (
    .A(_02484_),
    .B(_02620_),
    .C(_03087_),
    .Y(_03088_)
  );
  sky130_fd_sc_hd__nand3_1 _08695_ (
    .A(_00000_),
    .B(_03086_),
    .C(_03088_),
    .Y(_00107_)
  );
  sky130_fd_sc_hd__a21oi_1 _13781_ (
    .A1(_02484_),
    .A2(_03087_),
    .B1(_02755_),
    .Y(_06708_)
  );
  sky130_fd_sc_hd__a21oi_1 _13782_ (
    .A1(_02759_),
    .A2(_06708_),
    .B1(_02621_),
    .Y(_00109_)
  );
  sky130_fd_sc_hd__dfrtp_1 _15430_ (
    .CLK(clk),
    .D(_00107_),
    .Q(_07112_[0]),
    .RESET_B(rst_n)
  );
  sky130_fd_sc_hd__dfrtp_1 _15431_ (
    .CLK(clk),
    .D(_00108_),
    .Q(_07112_[1]),
    .RESET_B(rst_n)
  );
  sky130_fd_sc_hd__dfrtp_1 _15432_ (
    .CLK(clk),
    .D(_00109_),
    .Q(_07112_[2]),
    .RESET_B(rst_n)
  );
endmodule