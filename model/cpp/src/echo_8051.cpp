#include "cpu.h"
#include <fstream>
#include <string>
#include <algorithm>
#include <cstring>
#include <cstdlib>

namespace echo_8051 {

// ===== Instruction Handlers =====
#define HANDLER(name) static void name(CPU& cpu, u8 opcode)

HANDLER(nop) {}

HANDLER(ljmp) { u8 h=cpu.fetch(); u8 l=cpu.fetch(); cpu.pc=(u16(h)<<8)|l; }
HANDLER(lcall){u8 h=cpu.fetch();u8 l=cpu.fetch();u16 ra=cpu.pc;u8& sp=cpu.mem.sp();
  cpu.mem.write_iram((sp+1)&0xFF,ra&0xFF);cpu.mem.write_iram((sp+2)&0xFF,ra>>8);sp+=2;cpu.pc=(u16(h)<<8)|l;}
HANDLER(ret){u8& sp=cpu.mem.sp();u16 a=(u16(cpu.mem.read_iram(sp))<<8)|cpu.mem.read_iram((sp-1)&0xFF);sp-=2;cpu.pc=a;}
HANDLER(reti){ret(cpu,0);cpu.intr_active=false;}
HANDLER(sjmp){s8 r=cpu.signed_rel(cpu.fetch());cpu.pc=(cpu.pc+r)&0xFFFF;}
HANDLER(ajmp){u8 a=cpu.fetch();cpu.pc=((cpu.pc&0xF800)|((opcode&0xE0)<<3)|a)&0xFFFF;}
HANDLER(acall){u8 a=cpu.fetch();u16 ra=cpu.pc;u8& sp=cpu.mem.sp();
  cpu.mem.write_iram((sp+1)&0xFF,ra&0xFF);cpu.mem.write_iram((sp+2)&0xFF,ra>>8);sp+=2;cpu.pc=((cpu.pc&0xF800)|((opcode&0xE0)<<3)|a)&0xFFFF;}

HANDLER(jz){s8 r=cpu.signed_rel(cpu.fetch());if(cpu.mem.acc()==0)cpu.pc=(cpu.pc+r)&0xFFFF;}
HANDLER(jnz){s8 r=cpu.signed_rel(cpu.fetch());if(cpu.mem.acc()!=0)cpu.pc=(cpu.pc+r)&0xFFFF;}
HANDLER(jc){s8 r=cpu.signed_rel(cpu.fetch());if(cpu.mem.carry())cpu.pc=(cpu.pc+r)&0xFFFF;}
HANDLER(jnc){s8 r=cpu.signed_rel(cpu.fetch());if(!cpu.mem.carry())cpu.pc=(cpu.pc+r)&0xFFFF;}
HANDLER(jb){u8 b=cpu.fetch();s8 r=cpu.signed_rel(cpu.fetch());if(cpu.mem.read_bit(b))cpu.pc=(cpu.pc+r)&0xFFFF;}
HANDLER(jnb){u8 b=cpu.fetch();s8 r=cpu.signed_rel(cpu.fetch());if(!cpu.mem.read_bit(b))cpu.pc=(cpu.pc+r)&0xFFFF;}
HANDLER(jbc){u8 b=cpu.fetch();s8 r=cpu.signed_rel(cpu.fetch());if(cpu.mem.read_bit(b)){cpu.mem.write_bit(b,false);cpu.pc=(cpu.pc+r)&0xFFFF;}}
HANDLER(jmp_adptr){cpu.pc=(cpu.mem.dptr()+cpu.mem.acc())&0xFFFF;}

HANDLER(cjne_a_imm){u8 i=cpu.fetch();s8 r=cpu.signed_rel(cpu.fetch());if(cpu.mem.acc()!=i)cpu.pc=(cpu.pc+r)&0xFFFF;cpu.mem.set_carry(cpu.mem.acc()<i);}
HANDLER(cjne_a_dir){u8 d=cpu.fetch();s8 r=cpu.signed_rel(cpu.fetch());u8 v=cpu.mem.read_iram(d);if(cpu.mem.acc()!=v)cpu.pc=(cpu.pc+r)&0xFFFF;cpu.mem.set_carry(cpu.mem.acc()<v);}
HANDLER(cjne_ir0_imm){u8 i=cpu.fetch();s8 r=cpu.signed_rel(cpu.fetch());u8 v=cpu.mem.read_iram(cpu.r0_addr());if(v!=i)cpu.pc=(cpu.pc+r)&0xFFFF;cpu.mem.set_carry(v<i);}
HANDLER(cjne_ir1_imm){u8 i=cpu.fetch();s8 r=cpu.signed_rel(cpu.fetch());u8 v=cpu.mem.read_iram(cpu.r1_addr());if(v!=i)cpu.pc=(cpu.pc+r)&0xFFFF;cpu.mem.set_carry(v<i);}
HANDLER(cjne_rn_imm){u8 n=reg_index(opcode);u8 i=cpu.fetch();s8 r=cpu.signed_rel(cpu.fetch());u8 v=cpu.read_rn(n);if(v!=i)cpu.pc=(cpu.pc+r)&0xFFFF;cpu.mem.set_carry(v<i);}

HANDLER(djnz_dir){u8 d=cpu.fetch();s8 r=cpu.signed_rel(cpu.fetch());u8 v=ALU::dec(cpu.mem.read_iram(d));cpu.mem.write_iram(d,v);if(v)cpu.pc=(cpu.pc+r)&0xFFFF;}
HANDLER(djnz_rn){u8 n=reg_index(opcode);s8 r=cpu.signed_rel(cpu.fetch());u8 v=ALU::dec(cpu.read_rn(n));cpu.write_rn(n,v);if(v)cpu.pc=(cpu.pc+r)&0xFFFF;}

// MOV
HANDLER(mov_a_imm){cpu.mem.acc()=cpu.fetch();}
HANDLER(mov_a_dir){cpu.mem.acc()=cpu.mem.read_iram(cpu.fetch());}
HANDLER(mov_a_ir0){cpu.mem.acc()=cpu.mem.read_iram(cpu.r0_addr());}
HANDLER(mov_a_ir1){cpu.mem.acc()=cpu.mem.read_iram(cpu.r1_addr());}
HANDLER(mov_dir_a){cpu.mem.write_iram(cpu.fetch(),cpu.mem.acc());}
HANDLER(mov_dir_imm){u8 d=cpu.fetch();cpu.mem.write_iram(d,cpu.fetch());}
HANDLER(mov_dir_dir){u8 d=cpu.fetch();cpu.mem.write_iram(d,cpu.mem.read_iram(cpu.fetch()));}
HANDLER(mov_dir_ir0){cpu.mem.write_iram(cpu.fetch(),cpu.mem.read_iram(cpu.r0_addr()));}
HANDLER(mov_dir_ir1){cpu.mem.write_iram(cpu.fetch(),cpu.mem.read_iram(cpu.r1_addr()));}
HANDLER(mov_ir0_a){cpu.mem.write_iram(cpu.r0_addr(),cpu.mem.acc());}
HANDLER(mov_ir1_a){cpu.mem.write_iram(cpu.r1_addr(),cpu.mem.acc());}
HANDLER(mov_ir0_imm){cpu.mem.write_iram(cpu.r0_addr(),cpu.fetch());}
HANDLER(mov_ir1_imm){cpu.mem.write_iram(cpu.r1_addr(),cpu.fetch());}
HANDLER(mov_ir0_dir){cpu.mem.write_iram(cpu.r0_addr(),cpu.mem.read_iram(cpu.fetch()));}
HANDLER(mov_ir1_dir){cpu.mem.write_iram(cpu.r1_addr(),cpu.mem.read_iram(cpu.fetch()));}
HANDLER(mov_dptr_imm){u8 h=cpu.fetch();u8 l=cpu.fetch();cpu.mem.set_dptr((u16(h)<<8)|l);}

HANDLER(movc_a_apc){cpu.mem.acc()=cpu.mem.read_rom(cpu.pc+cpu.mem.acc());}
HANDLER(movc_a_adptr){cpu.mem.acc()=cpu.mem.read_rom(cpu.mem.dptr()+cpu.mem.acc());}

HANDLER(movx_a_dptr){cpu.mem.acc()=cpu.mem.read_xram(cpu.mem.dptr());}
HANDLER(movx_a_ir0){cpu.mem.acc()=cpu.mem.read_xram(cpu.mem.read_iram(cpu.r0_addr()));}
HANDLER(movx_a_ir1){cpu.mem.acc()=cpu.mem.read_xram(cpu.mem.read_iram(cpu.r1_addr()));}
HANDLER(movx_dptr_a){cpu.mem.write_xram(cpu.mem.dptr(),cpu.mem.acc());}
HANDLER(movx_ir0_a){cpu.mem.write_xram(cpu.mem.read_iram(cpu.r0_addr()),cpu.mem.acc());}
HANDLER(movx_ir1_a){cpu.mem.write_xram(cpu.mem.read_iram(cpu.r1_addr()),cpu.mem.acc());}

// PUSH/POP
HANDLER(push_dir){u8 v=cpu.mem.read_iram(cpu.fetch());u8& sp=cpu.mem.sp();sp=(sp+1)&0xFF;cpu.mem.write_iram(sp,v);}
HANDLER(pop_dir){u8 v=cpu.mem.read_iram(cpu.mem.sp());cpu.mem.sp()=(cpu.mem.sp()-1)&0xFF;cpu.mem.write_iram(cpu.fetch(),v);}

// XCH/XCHD/SWAP
HANDLER(xch_a_dir){u8 d=cpu.fetch();u8 t=cpu.mem.read_iram(d);cpu.mem.write_iram(d,cpu.mem.acc());cpu.mem.acc()=t;}
HANDLER(xch_a_ir0){u8 d=cpu.r0_addr();u8 t=cpu.mem.read_iram(d);cpu.mem.write_iram(d,cpu.mem.acc());cpu.mem.acc()=t;}
HANDLER(xch_a_ir1){u8 d=cpu.r1_addr();u8 t=cpu.mem.read_iram(d);cpu.mem.write_iram(d,cpu.mem.acc());cpu.mem.acc()=t;}
HANDLER(xchd_a_ir0){u8 d=cpu.r0_addr();u8 v=cpu.mem.read_iram(d);u8 a=cpu.mem.acc();cpu.mem.acc()=(a&0xF0)|(v&0x0F);cpu.mem.write_iram(d,(v&0xF0)|(a&0x0F));}
HANDLER(xchd_a_ir1){u8 d=cpu.r1_addr();u8 v=cpu.mem.read_iram(d);u8 a=cpu.mem.acc();cpu.mem.acc()=(a&0xF0)|(v&0x0F);cpu.mem.write_iram(d,(v&0xF0)|(a&0x0F));}
HANDLER(swap_a){cpu.mem.acc()=ALU::swap(cpu.mem.acc());}

// ADD/ADDC/SUBB
HANDLER(add_a_imm){cpu.mem.acc()=ALU::add(cpu.mem.acc(),cpu.fetch(),cpu.mem.psw());}
HANDLER(add_a_dir){cpu.mem.acc()=ALU::add(cpu.mem.acc(),cpu.mem.read_iram(cpu.fetch()),cpu.mem.psw());}
HANDLER(add_a_ir0){cpu.mem.acc()=ALU::add(cpu.mem.acc(),cpu.mem.read_iram(cpu.r0_addr()),cpu.mem.psw());}
HANDLER(add_a_ir1){cpu.mem.acc()=ALU::add(cpu.mem.acc(),cpu.mem.read_iram(cpu.r1_addr()),cpu.mem.psw());}
HANDLER(addc_a_imm){cpu.mem.acc()=ALU::addc(cpu.mem.acc(),cpu.fetch(),cpu.mem.psw());}
HANDLER(addc_a_dir){cpu.mem.acc()=ALU::addc(cpu.mem.acc(),cpu.mem.read_iram(cpu.fetch()),cpu.mem.psw());}
HANDLER(addc_a_ir0){cpu.mem.acc()=ALU::addc(cpu.mem.acc(),cpu.mem.read_iram(cpu.r0_addr()),cpu.mem.psw());}
HANDLER(addc_a_ir1){cpu.mem.acc()=ALU::addc(cpu.mem.acc(),cpu.mem.read_iram(cpu.r1_addr()),cpu.mem.psw());}
HANDLER(subb_a_imm){cpu.mem.acc()=ALU::subb(cpu.mem.acc(),cpu.fetch(),cpu.mem.psw());}
HANDLER(subb_a_dir){cpu.mem.acc()=ALU::subb(cpu.mem.acc(),cpu.mem.read_iram(cpu.fetch()),cpu.mem.psw());}
HANDLER(subb_a_ir0){cpu.mem.acc()=ALU::subb(cpu.mem.acc(),cpu.mem.read_iram(cpu.r0_addr()),cpu.mem.psw());}
HANDLER(subb_a_ir1){cpu.mem.acc()=ALU::subb(cpu.mem.acc(),cpu.mem.read_iram(cpu.r1_addr()),cpu.mem.psw());}

// INC/DEC
HANDLER(inc_a){cpu.mem.acc()=ALU::inc(cpu.mem.acc());}
HANDLER(inc_dir){u8 d=cpu.fetch();cpu.mem.write_iram(d,ALU::inc(cpu.mem.read_iram(d)));}
HANDLER(inc_ir0){u8 d=cpu.r0_addr();cpu.mem.write_iram(d,ALU::inc(cpu.mem.read_iram(d)));}
HANDLER(inc_ir1){u8 d=cpu.r1_addr();cpu.mem.write_iram(d,ALU::inc(cpu.mem.read_iram(d)));}
HANDLER(inc_dptr){cpu.mem.set_dptr(cpu.mem.dptr()+1);}
HANDLER(dec_a){cpu.mem.acc()=ALU::dec(cpu.mem.acc());}
HANDLER(dec_dir){u8 d=cpu.fetch();cpu.mem.write_iram(d,ALU::dec(cpu.mem.read_iram(d)));}
HANDLER(dec_ir0){u8 d=cpu.r0_addr();cpu.mem.write_iram(d,ALU::dec(cpu.mem.read_iram(d)));}
HANDLER(dec_ir1){u8 d=cpu.r1_addr();cpu.mem.write_iram(d,ALU::dec(cpu.mem.read_iram(d)));}

// MUL/DIV/DA
HANDLER(mul_ab){u8 a,bv;ALU::mul(cpu.mem.acc(),cpu.mem.b(),a,bv,cpu.mem.psw());cpu.mem.acc()=a;cpu.mem.b()=bv;}
HANDLER(div_ab){u8 a,bv;ALU::div(cpu.mem.acc(),cpu.mem.b(),a,bv,cpu.mem.psw());cpu.mem.acc()=a;cpu.mem.b()=bv;}
HANDLER(da_a){cpu.mem.acc()=ALU::da(cpu.mem.acc(),cpu.mem.psw());}

// ANL/ORL/XRL
HANDLER(anl_a_imm){cpu.mem.acc()=ALU::anl(cpu.mem.acc(),cpu.fetch());}
HANDLER(anl_a_dir){cpu.mem.acc()=ALU::anl(cpu.mem.acc(),cpu.mem.read_iram(cpu.fetch()));}
HANDLER(anl_a_ir0){cpu.mem.acc()=ALU::anl(cpu.mem.acc(),cpu.mem.read_iram(cpu.r0_addr()));}
HANDLER(anl_a_ir1){cpu.mem.acc()=ALU::anl(cpu.mem.acc(),cpu.mem.read_iram(cpu.r1_addr()));}
HANDLER(anl_dir_a){u8 d=cpu.fetch();cpu.mem.write_iram(d,ALU::anl(cpu.mem.read_iram(d),cpu.mem.acc()));}
HANDLER(anl_dir_imm){u8 d=cpu.fetch();cpu.mem.write_iram(d,ALU::anl(cpu.mem.read_iram(d),cpu.fetch()));}
HANDLER(orl_a_imm){cpu.mem.acc()=ALU::orl(cpu.mem.acc(),cpu.fetch());}
HANDLER(orl_a_dir){cpu.mem.acc()=ALU::orl(cpu.mem.acc(),cpu.mem.read_iram(cpu.fetch()));}
HANDLER(orl_a_ir0){cpu.mem.acc()=ALU::orl(cpu.mem.acc(),cpu.mem.read_iram(cpu.r0_addr()));}
HANDLER(orl_a_ir1){cpu.mem.acc()=ALU::orl(cpu.mem.acc(),cpu.mem.read_iram(cpu.r1_addr()));}
HANDLER(orl_dir_a){u8 d=cpu.fetch();cpu.mem.write_iram(d,ALU::orl(cpu.mem.read_iram(d),cpu.mem.acc()));}
HANDLER(orl_dir_imm){u8 d=cpu.fetch();cpu.mem.write_iram(d,ALU::orl(cpu.mem.read_iram(d),cpu.fetch()));}
HANDLER(xrl_a_imm){cpu.mem.acc()=ALU::xrl(cpu.mem.acc(),cpu.fetch());}
HANDLER(xrl_a_dir){cpu.mem.acc()=ALU::xrl(cpu.mem.acc(),cpu.mem.read_iram(cpu.fetch()));}
HANDLER(xrl_a_ir0){cpu.mem.acc()=ALU::xrl(cpu.mem.acc(),cpu.mem.read_iram(cpu.r0_addr()));}
HANDLER(xrl_a_ir1){cpu.mem.acc()=ALU::xrl(cpu.mem.acc(),cpu.mem.read_iram(cpu.r1_addr()));}
HANDLER(xrl_dir_a){u8 d=cpu.fetch();cpu.mem.write_iram(d,ALU::xrl(cpu.mem.read_iram(d),cpu.mem.acc()));}
HANDLER(xrl_dir_imm){u8 d=cpu.fetch();cpu.mem.write_iram(d,ALU::xrl(cpu.mem.read_iram(d),cpu.fetch()));}

// CLR/CPL/RL/RLC/RR/RRC
HANDLER(clr_a){cpu.mem.acc()=0;}
HANDLER(cpl_a){cpu.mem.acc()=ALU::cpl(cpu.mem.acc());}
HANDLER(rl_a){cpu.mem.acc()=ALU::rl(cpu.mem.acc());}
HANDLER(rlc_a){cpu.mem.acc()=ALU::rlc(cpu.mem.acc(),cpu.mem.psw());}
HANDLER(rr_a){cpu.mem.acc()=ALU::rr(cpu.mem.acc());}
HANDLER(rrc_a){cpu.mem.acc()=ALU::rrc(cpu.mem.acc(),cpu.mem.psw());}

// Bit ops
HANDLER(clr_c){cpu.mem.set_carry(false);}
HANDLER(setb_c){cpu.mem.set_carry(true);}
HANDLER(cpl_c){cpu.mem.set_carry(!cpu.mem.carry());}
HANDLER(clr_bit){cpu.mem.write_bit(cpu.fetch(),false);}
HANDLER(setb_bit){cpu.mem.write_bit(cpu.fetch(),true);}
HANDLER(cpl_bit){u8 b=cpu.fetch();cpu.mem.write_bit(b,!cpu.mem.read_bit(b));}
HANDLER(mov_c_bit){cpu.mem.set_carry(cpu.mem.read_bit(cpu.fetch()));}
HANDLER(mov_bit_c){cpu.mem.write_bit(cpu.fetch(),cpu.mem.carry());}
HANDLER(anl_c_bit){cpu.mem.set_carry(cpu.mem.carry()&&cpu.mem.read_bit(cpu.fetch()));}
HANDLER(anl_c_nbit){cpu.mem.set_carry(cpu.mem.carry()&&!cpu.mem.read_bit(cpu.fetch()));}
HANDLER(orl_c_bit){cpu.mem.set_carry(cpu.mem.carry()||cpu.mem.read_bit(cpu.fetch()));}
HANDLER(orl_c_nbit){cpu.mem.set_carry(cpu.mem.carry()||!cpu.mem.read_bit(cpu.fetch()));}

// Rn handlers (generated by lambda wrappers)
template<void (*H)(CPU&, u8)> void rn_dispatch(CPU& cpu, u8 opcode) {
    u8 n = reg_index(opcode);
    // These need inline because each mov/add/etc Rn uses Rn value differently
    H(cpu, opcode);
}

// ===== Opcode Table =====
std::array<InstrInfo, 256> OPCODES;

#define R(op, mnem, bytes, cycles, handler) OPCODES[op] = {mnem, bytes, cycles, handler}

// Handlers for Rn variants
HANDLER(mov_a_rn){cpu.mem.acc()=cpu.read_rn(reg_index(opcode));}
HANDLER(mov_rn_a){cpu.write_rn(reg_index(opcode),cpu.mem.acc());}
HANDLER(mov_rn_imm){cpu.write_rn(reg_index(opcode),cpu.fetch());}
HANDLER(mov_rn_dir){cpu.write_rn(reg_index(opcode),cpu.mem.read_iram(cpu.fetch()));}
HANDLER(mov_dir_rn){cpu.mem.write_iram(cpu.fetch(),cpu.read_rn(reg_index(opcode)));}
HANDLER(add_a_rn){cpu.mem.acc()=ALU::add(cpu.mem.acc(),cpu.read_rn(reg_index(opcode)),cpu.mem.psw());}
HANDLER(addc_a_rn){cpu.mem.acc()=ALU::addc(cpu.mem.acc(),cpu.read_rn(reg_index(opcode)),cpu.mem.psw());}
HANDLER(subb_a_rn){cpu.mem.acc()=ALU::subb(cpu.mem.acc(),cpu.read_rn(reg_index(opcode)),cpu.mem.psw());}
HANDLER(anl_a_rn){cpu.mem.acc()=ALU::anl(cpu.mem.acc(),cpu.read_rn(reg_index(opcode)));}
HANDLER(orl_a_rn){cpu.mem.acc()=ALU::orl(cpu.mem.acc(),cpu.read_rn(reg_index(opcode)));}
HANDLER(xrl_a_rn){cpu.mem.acc()=ALU::xrl(cpu.mem.acc(),cpu.read_rn(reg_index(opcode)));}
HANDLER(inc_rn){cpu.write_rn(reg_index(opcode),ALU::inc(cpu.read_rn(reg_index(opcode))));}
HANDLER(dec_rn){cpu.write_rn(reg_index(opcode),ALU::dec(cpu.read_rn(reg_index(opcode))));}
HANDLER(xch_a_rn){u8 n=reg_index(opcode);u8 t=cpu.read_rn(n);cpu.write_rn(n,cpu.mem.acc());cpu.mem.acc()=t;}

void build_opcode_table() {
    OPCODES.fill({"NOP", 1, 1, nop});

    R(0x00,"NOP",1,1,nop);
    R(0x02,"LJMP",3,2,ljmp);
    for(int i=0;i<8;i++){R(u8(0x01+i*2),"AJMP",2,2,ajmp);R(u8(0x11+i*2),"ACALL",2,2,acall);}

    R(0x03,"RR A",1,1,rr_a); R(0x13,"RRC A",1,1,rrc_a);
    R(0x23,"RL A",1,1,rl_a); R(0x33,"RLC A",1,1,rlc_a);

    R(0x04,"INC A",1,1,inc_a); R(0x05,"INC direct",2,1,inc_dir); R(0x06,"INC @R0",1,1,inc_ir0); R(0x07,"INC @R1",1,1,inc_ir1);
    for(int r=0;r<8;r++) R(u8(0x08+r),"INC Rn",1,1,inc_rn);

    R(0x10,"JBC bit,rel",3,2,jbc);
    R(0x12,"LCALL",3,2,lcall);
    R(0x14,"DEC A",1,1,dec_a); R(0x15,"DEC direct",2,1,dec_dir); R(0x16,"DEC @R0",1,1,dec_ir0); R(0x17,"DEC @R1",1,1,dec_ir1);
    for(int r=0;r<8;r++) R(u8(0x18+r),"DEC Rn",1,1,dec_rn);

    R(0x20,"JB bit,rel",3,2,jb);
    R(0x22,"RET",1,2,ret);
    for(int i=0;i<16;i++) R(u8(0x21+i*2),"AJMP",2,2,ajmp);

    R(0x24,"ADD A,#data",2,1,add_a_imm); R(0x25,"ADD A,direct",2,1,add_a_dir); R(0x26,"ADD A,@R0",1,1,add_a_ir0); R(0x27,"ADD A,@R1",1,1,add_a_ir1);
    for(int r=0;r<8;r++) R(u8(0x28+r),"ADD A,Rn",1,1,add_a_rn);

    R(0x30,"JNB bit,rel",3,2,jnb);
    R(0x32,"RETI",1,2,reti);
    for(int i=0;i<8;i++) R(u8(0x31+i*2),"ACALL",2,2,acall);

    R(0x34,"ADDC A,#data",2,1,addc_a_imm); R(0x35,"ADDC A,direct",2,1,addc_a_dir); R(0x36,"ADDC A,@R0",1,1,addc_a_ir0); R(0x37,"ADDC A,@R1",1,1,addc_a_ir1);
    for(int r=0;r<8;r++) R(u8(0x38+r),"ADDC A,Rn",1,1,addc_a_rn);

    R(0x40,"JC rel",2,2,jc);
    for(int i=0;i<16;i++) R(u8(0x41+i*2),"AJMP",2,2,ajmp);
    R(0x42,"ORL direct,A",2,1,orl_dir_a); R(0x43,"ORL direct,#data",3,2,orl_dir_imm);
    R(0x44,"ORL A,#data",2,1,orl_a_imm); R(0x45,"ORL A,direct",2,1,orl_a_dir); R(0x46,"ORL A,@R0",1,1,orl_a_ir0); R(0x47,"ORL A,@R1",1,1,orl_a_ir1);
    for(int r=0;r<8;r++) R(u8(0x48+r),"ORL A,Rn",1,1,orl_a_rn);

    R(0x50,"JNC rel",2,2,jnc);
    for(int i=0;i<8;i++) R(u8(0x51+i*2),"ACALL",2,2,acall);
    R(0x52,"ANL direct,A",2,1,anl_dir_a); R(0x53,"ANL direct,#data",3,2,anl_dir_imm);
    R(0x54,"ANL A,#data",2,1,anl_a_imm); R(0x55,"ANL A,direct",2,1,anl_a_dir); R(0x56,"ANL A,@R0",1,1,anl_a_ir0); R(0x57,"ANL A,@R1",1,1,anl_a_ir1);
    for(int r=0;r<8;r++) R(u8(0x58+r),"ANL A,Rn",1,1,anl_a_rn);

    R(0x60,"JZ rel",2,2,jz);
    for(int i=0;i<16;i++) R(u8(0x61+i*2),"AJMP",2,2,ajmp);
    R(0x62,"XRL direct,A",2,1,xrl_dir_a); R(0x63,"XRL direct,#data",3,2,xrl_dir_imm);
    R(0x64,"XRL A,#data",2,1,xrl_a_imm); R(0x65,"XRL A,direct",2,1,xrl_a_dir); R(0x66,"XRL A,@R0",1,1,xrl_a_ir0); R(0x67,"XRL A,@R1",1,1,xrl_a_ir1);
    for(int r=0;r<8;r++) R(u8(0x68+r),"XRL A,Rn",1,1,xrl_a_rn);

    R(0x70,"JNZ rel",2,2,jnz);
    for(int i=0;i<8;i++) R(u8(0x71+i*2),"ACALL",2,2,acall);
    R(0x72,"ORL C,bit",2,2,orl_c_bit); R(0x73,"JMP @A+DPTR",1,2,jmp_adptr);
    R(0x74,"MOV A,#data",2,1,mov_a_imm); R(0x75,"MOV direct,#data",3,2,mov_dir_imm);
    R(0x76,"MOV @R0,#data",2,1,mov_ir0_imm); R(0x77,"MOV @R1,#data",2,1,mov_ir1_imm);
    for(int r=0;r<8;r++) R(u8(0x78+r),"MOV Rn,#data",2,1,mov_rn_imm);

    R(0x80,"SJMP",2,2,sjmp);
    for(int i=0;i<16;i++) R(u8(0x81+i*2),"AJMP",2,2,ajmp);
    R(0x82,"ANL C,bit",2,2,anl_c_bit);
    R(0x83,"MOVC A,@A+PC",1,2,movc_a_apc);
    R(0x84,"DIV AB",1,4,div_ab);
    R(0x85,"MOV direct,direct",3,2,mov_dir_dir);
    R(0x86,"MOV direct,@R0",2,2,mov_dir_ir0); R(0x87,"MOV direct,@R1",2,2,mov_dir_ir1);
    for(int r=0;r<8;r++) R(u8(0x88+r),"MOV direct,Rn",2,2,mov_dir_rn);

    R(0x90,"MOV DPTR,#data16",3,2,mov_dptr_imm);
    for(int i=0;i<8;i++) R(u8(0x91+i*2),"ACALL",2,2,acall);
    R(0x92,"MOV bit,C",2,2,mov_bit_c);
    R(0x93,"MOVC A,@A+DPTR",1,2,movc_a_adptr);
    R(0x94,"SUBB A,#data",2,1,subb_a_imm); R(0x95,"SUBB A,direct",2,1,subb_a_dir); R(0x96,"SUBB A,@R0",1,1,subb_a_ir0); R(0x97,"SUBB A,@R1",1,1,subb_a_ir1);
    for(int r=0;r<8;r++) R(u8(0x98+r),"SUBB A,Rn",1,1,subb_a_rn);

    R(0xA0,"ORL C,/bit",2,2,orl_c_nbit);
    for(int i=0;i<16;i++) R(u8(0xA1+i*2),"AJMP",2,2,ajmp);
    R(0xA2,"MOV C,bit",2,1,mov_c_bit);
    R(0xA3,"INC DPTR",1,2,inc_dptr);
    R(0xA4,"MUL AB",1,4,mul_ab);
    // 0xA5 reserved
    R(0xA6,"MOV @R0,direct",2,2,mov_ir0_dir); R(0xA7,"MOV @R1,direct",2,2,mov_ir1_dir);
    for(int r=0;r<8;r++) R(u8(0xA8+r),"MOV Rn,direct",2,2,mov_rn_dir);

    R(0xB0,"ANL C,/bit",2,2,anl_c_nbit);
    for(int i=0;i<8;i++) R(u8(0xB1+i*2),"ACALL",2,2,acall);
    R(0xB2,"CPL bit",2,1,cpl_bit);
    R(0xB3,"CPL C",1,1,cpl_c);
    R(0xB4,"CJNE A,#data,rel",3,2,cjne_a_imm); R(0xB5,"CJNE A,direct,rel",3,2,cjne_a_dir);
    R(0xB6,"CJNE @R0,#data,rel",3,2,cjne_ir0_imm); R(0xB7,"CJNE @R1,#data,rel",3,2,cjne_ir1_imm);
    for(int r=0;r<8;r++) R(u8(0xB8+r),"CJNE Rn,#data,rel",3,2,cjne_rn_imm);

    R(0xC0,"PUSH direct",2,2,push_dir);
    for(int i=0;i<16;i++) R(u8(0xC1+i*2),"AJMP",2,2,ajmp);
    R(0xC2,"CLR bit",2,1,clr_bit); R(0xC3,"CLR C",1,1,clr_c);
    R(0xC4,"SWAP A",1,1,swap_a);
    R(0xC5,"XCH A,direct",2,1,xch_a_dir); R(0xC6,"XCH A,@R0",1,1,xch_a_ir0); R(0xC7,"XCH A,@R1",1,1,xch_a_ir1);
    for(int r=0;r<8;r++) R(u8(0xC8+r),"XCH A,Rn",1,1,xch_a_rn);

    R(0xD0,"POP direct",2,2,pop_dir);
    for(int i=0;i<8;i++) R(u8(0xD1+i*2),"ACALL",2,2,acall);
    R(0xD2,"SETB bit",2,1,setb_bit); R(0xD3,"SETB C",1,1,setb_c);
    R(0xD4,"DA A",1,1,da_a);
    R(0xD5,"DJNZ direct,rel",3,2,djnz_dir);
    R(0xD6,"XCHD A,@R0",1,1,xchd_a_ir0); R(0xD7,"XCHD A,@R1",1,1,xchd_a_ir1);
    for(int r=0;r<8;r++) R(u8(0xD8+r),"DJNZ Rn,rel",2,2,djnz_rn);

    R(0xE0,"MOVX A,@DPTR",1,2,movx_a_dptr);
    for(int i=0;i<16;i++) R(u8(0xE1+i*2),"AJMP",2,2,ajmp);
    R(0xE2,"MOVX A,@R0",1,2,movx_a_ir0); R(0xE3,"MOVX A,@R1",1,2,movx_a_ir1);
    R(0xE4,"CLR A",1,1,clr_a);
    R(0xE5,"MOV A,direct",2,1,mov_a_dir); R(0xE6,"MOV A,@R0",1,1,mov_a_ir0); R(0xE7,"MOV A,@R1",1,1,mov_a_ir1);
    for(int r=0;r<8;r++) R(u8(0xE8+r),"MOV A,Rn",1,1,mov_a_rn);

    R(0xF0,"MOVX @DPTR,A",1,2,movx_dptr_a);
    for(int i=0;i<8;i++) R(u8(0xF1+i*2),"ACALL",2,2,acall);
    R(0xF2,"MOVX @R0,A",1,2,movx_ir0_a); R(0xF3,"MOVX @R1,A",1,2,movx_ir1_a);
    R(0xF4,"CPL A",1,1,cpl_a);
    R(0xF5,"MOV direct,A",2,1,mov_dir_a); R(0xF6,"MOV @R0,A",1,1,mov_ir0_a); R(0xF7,"MOV @R1,A",1,1,mov_ir1_a);
    for(int r=0;r<8;r++) R(u8(0xF8+r),"MOV Rn,A",1,1,mov_rn_a);
}

const InstrInfo& decode(u8 opcode) noexcept {
    return OPCODES[opcode];
}

// ===== CPU Implementation =====

CPU::CPU(u32 rs) : rom_size(rs) {
    build_opcode_table();
    reset();
    // ROM size is fixed at 4096 in Memory; larger sizes not supported
    // Use load_bytes() for programs < 4096 bytes
}

void CPU::reset() {
    mem.reset();
    pc = 0;
    cycles = 0;
    instr_count = 0;
    running = true;
    intr_active = false;
    pending_intr.clear();
    uart_rx_buf.clear();
}

void CPU::load_bytes(const u8* data, size_t len, u16 start_addr) {
    for (size_t i = 0; i < len && (start_addr + i) < mem.rom.size(); i++)
        mem.rom[start_addr + i] = data[i];
}

static u8 hex2(const char* s) { return u8(std::strtol(s, nullptr, 16)); }
static u16 hex4(const char* s) { return u16(std::strtol(s, nullptr, 16)); }

void CPU::load_hex(const char* filename) {
    std::ifstream f(filename);
    if (!f) return;
    std::string line;
    u32 ext_addr = 0;
    while (std::getline(f, line)) {
        if (line.empty() || line[0] != ':') continue;
        u8 byte_count = hex2(line.c_str() + 1);
        u16 address = hex4(line.c_str() + 3);
        u8 rec_type = hex2(line.c_str() + 7);
        if (rec_type == 0x00) {
            u32 addr = ext_addr + address;
            for (int i = 0; i < byte_count; i++) {
                u8 b = hex2(line.c_str() + 9 + i*2);
                if (addr < mem.rom.size()) mem.rom[addr] = b;
                addr++;
            }
        } else if (rec_type == 0x01) break;
        else if (rec_type == 0x02) ext_addr = hex4(line.c_str() + 9) << 4;
        else if (rec_type == 0x04) ext_addr = hex4(line.c_str() + 9) << 16;
    }
}

u8 CPU::step() {
    if (!running) return 0;
    service_interrupts();

    u8 opcode = fetch();
    auto& info = decode(opcode);
    info.handler(*this, opcode);

    instr_count++;
    cycles += info.cycles;
    update_timers(info.cycles);
    return info.cycles;
}

void CPU::run(i64 max_cycles, i64 max_instr) {
    u64 start_c = cycles;
    u64 start_i = instr_count;
    while (running) {
        if (max_cycles > 0 && i64(cycles - start_c) >= max_cycles) break;
        if (max_instr > 0 && i64(instr_count - start_i) >= max_instr) break;
        step();
    }
}

void CPU::service_interrupts() {
    if (pending_intr.empty()) return;
    if (!(mem.ie() & (1 << IE_EA))) { pending_intr.clear(); return; }
    auto [vec, pri] = pending_intr[0];
    pending_intr.clear();
    u8& sp = mem.sp();
    mem.write_iram((sp+1)&0xFF, pc & 0xFF);
    mem.write_iram((sp+2)&0xFF, (pc >> 8) & 0xFF);
    sp += 2;
    intr_active = true;
    pc = vec;
}

void CPU::request_interrupt(u16 vector, u8 flag_sfr, u8 flag_bit, u8 enable_bit) {
    if (!(mem.ie() & (1 << enable_bit))) return;
    mem.sfr_at(flag_sfr) |= (1 << flag_bit);
    u8 pri = 0;
    switch (enable_bit) {
        case IE_ES: pri = (mem.ip() & 0x10) ? 1 : 0; break;
        case IE_ET1: pri = (mem.ip() & 0x08) ? 1 : 0; break;
        case IE_EX1: pri = (mem.ip() & 0x04) ? 1 : 0; break;
        case IE_ET0: pri = (mem.ip() & 0x02) ? 1 : 0; break;
        default: pri = (mem.ip() & 0x01) ? 1 : 0; break;
    }
    pending_intr.push_back({vector, pri});
    std::sort(pending_intr.begin(), pending_intr.end(),
              [](auto& a, auto& b) { return a.second > b.second; });
}

void CPU::update_timers(u8 elapsed) {
    u8 tmod = mem.sfr_at(SFR_TMOD);
    u8 tcon = mem.sfr_at(SFR_TCON);

    for (int tn = 0; tn < 2; tn++) {
        u8 tr_bit = tn == 0 ? TCON_TR0 : TCON_TR1;
        if (!(tcon & (1 << tr_bit))) continue;

        u8 th_addr = tn == 0 ? SFR_TH0 : SFR_TH1;
        u8 tl_addr = tn == 0 ? SFR_TL0 : SFR_TL1;
        u8 mode = ((tmod >> (tn*4)) & 3);

        // In ISS mode, timers tick per machine cycle (12 oscillator clocks)
        // elapsed is in machine cycles, so we count directly
        u8 th = mem.sfr_at(th_addr);
        u8 tl = mem.sfr_at(tl_addr);

        if (mode == 0) { // 13-bit
            u16 val = ((u16(th) << 5) | (tl & 0x1F)) + elapsed;
            if (val > 0x1FFF) {
                val = 0;
                tcon |= (1 << (tn == 0 ? TCON_TF0 : TCON_TF1));
                request_interrupt(tn == 0 ? INT_VEC_T0 : INT_VEC_T1,
                                  SFR_TCON, tn == 0 ? TCON_TF0 : TCON_TF1,
                                  tn == 0 ? IE_ET0 : IE_ET1);
            }
            mem.sfr_at(th_addr) = (val >> 5) & 0xFF;
            mem.sfr_at(tl_addr) = val & 0x1F;
        } else if (mode == 1) { // 16-bit
            u16 val = ((u16(th) << 8) | tl) + elapsed;
            if (val > 0xFFFF) {
                val = 0;
                tcon |= (1 << (tn == 0 ? TCON_TF0 : TCON_TF1));
                request_interrupt(tn == 0 ? INT_VEC_T0 : INT_VEC_T1,
                                  SFR_TCON, tn == 0 ? TCON_TF0 : TCON_TF1,
                                  tn == 0 ? IE_ET0 : IE_ET1);
            }
            mem.sfr_at(th_addr) = (val >> 8) & 0xFF;
            mem.sfr_at(tl_addr) = val & 0xFF;
        } else if (mode == 2) { // 8-bit auto-reload
            u16 val = tl + elapsed;
            if (val > 0xFF) {
                val = 0;
                tcon |= (1 << (tn == 0 ? TCON_TF0 : TCON_TF1));
                request_interrupt(tn == 0 ? INT_VEC_T0 : INT_VEC_T1,
                                  SFR_TCON, tn == 0 ? TCON_TF0 : TCON_TF1,
                                  tn == 0 ? IE_ET0 : IE_ET1);
                mem.sfr_at(tl_addr) = th; // reload
            } else {
                mem.sfr_at(tl_addr) = u8(val);
            }
        }
    }
    mem.tcon() = tcon;
}

CPUState CPU::get_state() {
    CPUState s;
    s.pc = pc;
    s.acc = mem.acc();
    s.b = mem.b();
    s.psw = mem.psw();
    s.sp = mem.sp();
    s.dptr = mem.dptr();
    s.cycles = cycles;
    s.instructions = instr_count;
    std::copy(mem.iram.begin(), mem.iram.end(), s.iram.begin());
    std::copy(mem.sfr.begin(), mem.sfr.end(), s.sfr.begin());
    return s;
}

} // namespace echo_8051
