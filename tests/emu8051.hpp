#pragma once
// Focused 8051 interpreter for offline firmware regression checks.
// It is not an MCU, radio, USB host or flash emulator.
#include <array>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <iterator>
#include <stdexcept>
#include <string>
#include <vector>

using Bytes = std::vector<uint8_t>;
static void require(bool yes, const char* why) { if (!yes) throw std::runtime_error(why); }
static int rel(uint8_t n) { return static_cast<int8_t>(n); }

struct CPU {
    const Bytes& rom;
    std::array<uint8_t, 256> d{};
    std::array<uint8_t, 4096> x{};
    std::vector<uint16_t> calls;
    uint16_t pc = 0;
    bool carry = false;
    unsigned modeled_template_copies = 0;
    unsigned modeled_nv_saves = 0;
    explicit CPU(const Bytes& image): rom(image) {}
    uint8_t& a() { return d[0xe0]; }
    uint16_t ptr() { return (uint16_t(d[0x83]) << 8) | d[0x82]; }
    void ptr(uint16_t p) { d[0x82] = p; d[0x83] = p >> 8; }
    uint8_t fetch() { require(pc < rom.size(), "PC outside ROM"); return rom[pc++]; }
    uint8_t& xd(uint16_t p) { require(p >= 0x8000 && p < 0x9000, "Unexpected XDATA access"); return x[p-0x8000]; }
    bool bit(uint8_t b) {
        if (b == 0xd7) return carry;
        const uint8_t adr = b < 0x80 ? 0x20 + b/8 : b & 0xf8;
        return (d[adr] >> (b & 7)) & 1;
    }
    void add(uint8_t v, bool withCarry) {
        unsigned n = unsigned(a()) + v + (withCarry && carry);
        a() = n; carry = n > 255;
    }
    void sub(uint8_t v) {
        unsigned n = unsigned(v) + carry;
        bool borrow = unsigned(a()) < n;
        a() = unsigned(a()) - n; carry = borrow;
    }
    bool return_from_call() {
        if (calls.empty()) return false;
        pc=calls.back(); calls.pop_back(); return true;
    }
    void run(uint16_t entry, uint16_t stop = 0xffff) {
        require(calls.empty(), "Unbalanced call stack at entry");
        pc = entry;
        for (unsigned steps = 0; steps < 50000; ++steps) {
            if (pc == stop) { require(calls.empty(), "Stop inside nested call"); return; }
            // Only the unchanged PS3 ROM-template copy is modeled. Check all
            // operands so a different helper invocation cannot silently pass.
            if (pc == 0x1554) {
                require(d[3]==0xff && d[2]==0x58 && d[1]==0x50 &&
                        d[5]==1 && d[4]==0x84 && d[0]==0x30 && d[6]==0 && d[7]==49,
                        "Unexpected generic-copy invocation");
                for (unsigned i=0; i<49; ++i) xd(0x8430+i)=rom[0x5850+i];
                ++modeled_template_copies;
                if (!return_from_call()) return;
                continue;
            }
            // Observe legacy settings-save calls without pretending to model
            // nonvolatile hardware. The new PC toggle must never reach this.
            if (pc == 0x3c98) {
                ++modeled_nv_saves;
                if (!return_from_call()) return;
                continue;
            }
            auto op = fetch();
            if (op >= 0x78 && op <= 0x7f) { d[op-0x78] = fetch(); continue; }
            if (op >= 0xe8 && op <= 0xef) { a() = d[op-0xe8]; continue; }
            if (op >= 0xf8) { d[op-0xf8] = a(); continue; }
            if (op >= 0x08 && op <= 0x0f) { ++d[op-0x08]; continue; }
            if (op >= 0x28 && op <= 0x2f) { add(d[op-0x28], false); continue; }
            if (op >= 0x38 && op <= 0x3f) { add(d[op-0x38], true); continue; }
            if (op >= 0x48 && op <= 0x4f) { a() |= d[op-0x48]; continue; }
            if (op >= 0x58 && op <= 0x5f) { a() &= d[op-0x58]; continue; }
            if (op >= 0x68 && op <= 0x6f) { a() ^= d[op-0x68]; continue; }
            if (op >= 0x88 && op <= 0x8f) { d[fetch()]=d[op-0x88]; continue; }
            if (op >= 0x98 && op <= 0x9f) { sub(d[op-0x98]); continue; }
            if (op >= 0xa8 && op <= 0xaf) { d[op-0xa8] = d[fetch()]; continue; }
            if (op >= 0xb8 && op <= 0xbf) { auto v=fetch(); int r=rel(fetch()); auto lhs=d[op-0xb8]; carry=lhs<v; if(lhs!=v) pc+=r; continue; }
            if (op >= 0xc8 && op <= 0xcf) { auto old=a(); a()=d[op-0xc8]; d[op-0xc8]=old; continue; }
            if (op >= 0xd8 && op <= 0xdf) { int r=rel(fetch()); if (--d[op-0xd8]) pc += r; continue; }
            switch (op) {
                case 0x00: break;
                case 0x02: { unsigned h=fetch(), l=fetch(); pc=(h<<8)|l; break; }
                case 0x04: ++a(); break;
                case 0x05: ++d[fetch()]; break;
                case 0x12: { unsigned h=fetch(), l=fetch(); calls.push_back(pc); pc=(h<<8)|l; break; }
                case 0x13: { bool c=a()&1; a()=(a()>>1)|(carry?0x80:0); carry=c; break; }
                case 0x14: --a(); break;
                case 0x15: --d[fetch()]; break;
                case 0x20: { auto b=fetch(); int r=rel(fetch()); if (bit(b)) pc+=r; break; }
                case 0x22: if (calls.empty()) return; else { pc=calls.back(); calls.pop_back(); } break;
                case 0x23: a()=(a()<<1)|(a()>>7); break;
                case 0x24: { auto v=fetch(); add(v,false); break; }
                case 0x25: { auto v=d[fetch()]; add(v,false); break; }
                case 0x30: { auto b=fetch(); int r=rel(fetch()); if (!bit(b)) pc+=r; break; }
                case 0x33: { bool c=a()&0x80; a()=(a()<<1)|carry; carry=c; break; }
                case 0x34: { auto v=fetch(); add(v,true); break; }
                case 0x35: { auto v=d[fetch()]; add(v,true); break; }
                case 0x40: { int r=rel(fetch()); if (carry) pc+=r; break; }
                case 0x43: { auto adr=fetch(), v=fetch(); d[adr]|=v; break; }
                case 0x44: a() |= fetch(); break;
                case 0x45: a() |= d[fetch()]; break;
                case 0x50: { int r=rel(fetch()); if (!carry) pc+=r; break; }
                case 0x53: { auto adr=fetch(), v=fetch(); d[adr]&=v; break; }
                case 0x54: a() &= fetch(); break;
                case 0x55: a() &= d[fetch()]; break;
                case 0x60: { int r=rel(fetch()); if (!a()) pc+=r; break; }
                case 0x63: { auto adr=fetch(), v=fetch(); d[adr]^=v; break; }
                case 0x64: a() ^= fetch(); break;
                case 0x65: a() ^= d[fetch()]; break;
                case 0x70: { int r=rel(fetch()); if (a()) pc+=r; break; }
                case 0x73: pc += 0; pc=ptr()+a(); break;
                case 0x74: a()=fetch(); break;
                case 0x75: { auto adr=fetch(), v=fetch(); d[adr]=v; break; }
                case 0x80: { int r=rel(fetch()); pc+=r; break; }
                case 0x85: { auto src=fetch(), dst=fetch(); d[dst]=d[src]; break; }
                case 0x90: { unsigned h=fetch(), l=fetch(); ptr((h<<8)|l); break; }
                case 0x93: require(ptr()+a()<rom.size(), "MOVC outside ROM"); a()=rom[ptr()+a()]; break;
                case 0x94: { auto v=fetch(); sub(v); break; }
                case 0x95: { auto v=d[fetch()]; sub(v); break; }
                case 0xa2: carry=bit(fetch()); break;
                case 0xa3: ptr(ptr()+1); break;
                case 0xb4: { auto v=fetch(); int r=rel(fetch()); carry=a()<v; if(a()!=v)pc+=r; break; }
                case 0xc3: carry=false; break;
                case 0xc4: a()=(a()<<4)|(a()>>4); break;
                case 0xc5: { auto adr=fetch(), old=a(); a()=d[adr]; d[adr]=old; break; }
                case 0xd3: carry=true; break;
                case 0xe0: a()=xd(ptr()); break;
                case 0xe4: a()=0; break;
                case 0xe5: a()=d[fetch()]; break;
                case 0xe6: case 0xe7: a()=d[d[op-0xe6]]; break;
                case 0xf0: xd(ptr())=a(); break;
                case 0xf4: a()=~a(); break;
                case 0xf5: { auto adr=fetch(); d[adr]=a(); break; }
                case 0xf6: case 0xf7: d[d[op-0xf6]]=a(); break;
                default: throw std::runtime_error("Unsupported opcode " + std::to_string(op) + " at " + std::to_string(pc-1));
            }
        }
        throw std::runtime_error("Instruction limit");
    }
};
