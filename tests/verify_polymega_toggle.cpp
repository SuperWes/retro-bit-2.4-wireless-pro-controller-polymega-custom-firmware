// Execute the patched dispatch and macro paths, then compare USB report bytes.
// No device I/O. Only the unchanged PS3 template copy and legacy NVM-save calls
// are modeled; see emu8051.hpp for those explicit boundaries.
#include "emu8051.hpp"
#include <algorithm>

static constexpr uint16_t state_address = 0x85ff;
static constexpr uint32_t start_button = 1u << 22, right_button = 1u << 13;
static constexpr uint32_t up_button = 1u << 14;
static constexpr uint32_t chord = start_button | right_button;
static constexpr unsigned hold_ticks = 625;
static uint64_t macro_iterations = 0;

static void inputs(CPU& c, uint32_t raw, const std::array<uint8_t,4>& axes,
                   uint8_t lt=0, uint8_t rt=0) {
    for (unsigned i=0; i<3; ++i) {
        c.xd(0x851d+i)=raw>>(8*i);
        c.xd(0x8526+i)=raw>>(8*i);
    }
    for (unsigned i=0; i<4; ++i) c.xd(0x8520+i)=axes[i];
    c.xd(0x8524)=lt; c.xd(0x8525)=rt;
}

static Bytes output(CPU& c, unsigned mode) {
    c.run(0x3460); // Actual call sites modified by this patch, not just wrappers.
    require(c.calls.empty(), "Report call stack not balanced");
    Bytes out(mode==2 ? 49 : 20);
    for (unsigned i=0; i<out.size(); ++i) out[i]=c.xd(0x8430+i);
    return out;
}

static Bytes report(const Bytes& rom, unsigned mode, uint8_t preset, uint32_t raw,
                    const std::array<uint8_t,4>& axes, uint8_t lt, uint8_t rt, uint8_t options=0) {
    CPU c(rom);
    c.xd(0x8542)=mode; c.xd(state_address)=preset;
    c.d[0x51]=1; c.d[0x52]=options;
    inputs(c,raw,axes,lt,rt);
    auto out=output(c,mode);
    require(c.xd(state_address)==preset, "Report builder changed toggle state");
    require(c.modeled_nv_saves==0, "Report processing reached a settings save");
    require(c.modeled_template_copies==(mode==2 ? 1u : 0u), "Wrong report builder dispatched");
    for (unsigned i=0; i<4; ++i)
        require(c.xd(0x8520+i)==axes[i], "Report wrapper modified an analog input");
    for (unsigned i=0; i<3; ++i)
        require(c.xd(0x8526+i)==uint8_t(raw>>(8*i)), "Report wrapper modified cached macro input");
    return out;
}

// Physical A/B/X/Y are raw bits 8/9/10/11. The pinned stock Switch table
// maps those to recorded USB bits 3/2/1/0, respectively (guided button capture).
// Use a physical-input model, independent of the extension's report-bit code.
static uint32_t mapped_input(uint32_t raw, unsigned preset) {
    if (preset == 0 || preset > 2) return raw;
    if (preset == 1) {
        return (raw & ~((1u<<16)|(1u<<18))) |
               ((raw & (1u<<16)) << 2) | ((raw & (1u<<18)) >> 2);
    }
    return (raw & ~((1u<<8)|(1u<<9)|(1u<<10)|(1u<<16)|(1u<<18))) |
           ((raw & (1u<<8)) << 2) | ((raw & (1u<<9)) >> 1) |
           ((raw & (1u<<10)) << 8) | ((raw & (1u<<16)) >> 7) |
           ((raw & (1u<<18)) >> 2);
}

static void verify_analog(const Bytes& out, unsigned mode, uint32_t raw,
                          const std::array<uint8_t,4>& axes, uint8_t lt, uint8_t rt) {
    if (mode==3) {
        for (unsigned axis=0; axis<4; ++axis) {
            unsigned i=6+2*axis;
            int actual=int16_t(uint16_t(out[i])|(uint16_t(out[i+1])<<8));
            // Independent numeric model of the stock receiver's 8-bit axes in
            // signed 16-bit XInput fields: center 0, endpoints -32768/+32512.
            require(actual==(int(axes[axis])-128)*256, "XInput analog axis mismatch");
        }
        require(out[4]==((raw&(1u<<7)) ? 255 : lt), "XInput ZL/left-trigger mismatch");
        require(out[5]==((raw&(1u<<6)) ? 255 : rt), "XInput ZR/right-trigger mismatch");
    } else {
        require(out[6]==axes[0] && out[7]==255-axes[1] &&
                out[8]==axes[2] && out[9]==255-axes[3], "PS3 analog axis mismatch");
        require(bool(out[3]&1)==bool(raw&(1u<<7)) && bool(out[3]&2)==bool(raw&(1u<<6)),
                "PS3 ZL/ZR button mismatch");
        require(out[18]==((raw&(1u<<7)) ? 255 : 0) && out[19]==((raw&(1u<<6)) ? 255 : 0),
                "PS3 ZL/ZR pressure mismatch");
    }
}

static void tick(CPU& c, uint32_t raw) {
    inputs(c,raw,{128,128,128,128});
    c.run(0x264b); // Stock detector, hold counter, branch hook, and continuation.
    ++macro_iterations;
}

static void hold(CPU& c, uint32_t raw=chord) {
    tick(c,raw); // First observation initializes the stock hold counter to zero.
    for (unsigned i=0; i<hold_ticks; ++i) tick(c,raw);
}

static void check_macro(const Bytes& stock, const Bytes& changed) {
    for (unsigned mode : {2u,3u}) for (unsigned preset : {1u,2u}) {
        const uint32_t selected_chord = start_button | (preset==1 ? right_button : up_button);
        CPU c(changed);
        c.xd(0x8542)=mode; c.d[0x51]=1;
        tick(c,selected_chord);
        for (unsigned i=0; i<hold_ticks-1; ++i) tick(c,selected_chord);
        require(c.xd(state_address)==0, "Preset fired before full hold threshold");
        tick(c,selected_chord);
        require(c.xd(state_address)==preset, preset==1 ? "Start+Right failed" : "Start+Up failed");
        for (unsigned i=0; i<70000; ++i) tick(c,selected_chord);
        require(c.xd(state_address)==preset, "Held chord repeated or counter wrapped");
        require(c.d[0x4c]==255 && c.d[0x4d]==255, "Stock hold counter failed to saturate");
        require(c.d[0x51]==1 && c.d[0x52]==0, "PC shortcut changed legacy layout state");
        require(c.modeled_nv_saves==0, "PC preset attempted a nonvolatile settings write");
        tick(c,start_button); // Releasing just the direction is sufficient.
        hold(c,selected_chord);
        require(c.xd(state_address)==0, "Second hold failed to restore stock mapping");
        tick(c,0);
        for (unsigned i=0; i<400; ++i) tick(c,selected_chord);
        tick(c,0);
        for (unsigned i=0; i<400; ++i) tick(c,selected_chord);
        require(c.xd(state_address)==0, "Separate short holds accumulated");
        tick(c,0);
        hold(c,selected_chord);
        require(c.xd(state_address)==preset, "Preset did not rearm after release");
        const uint32_t raw=(1u<<16)|(1u<<8)|(1u<<7)|(1u<<12);
        inputs(c,raw,{31,219,17,231},13,29);
        auto after=output(c,mode);
        auto expected=report(stock,mode,0,mapped_input(raw,preset),{31,219,17,231},13,29);
        require(after==expected, "Macro state did not reach the USB report dispatcher");
        verify_analog(after,mode,raw,{31,219,17,231},13,29);
        c.run(0x376e,0x1d24);
        require(c.xd(state_address)==0, "Cold start did not restore stock mapping");
        c.xd(0x8542)=mode; c.d[0x51]=1;
        inputs(c,1u<<16,{128,128,128,128});
        require(output(c,mode)==report(stock,mode,0,1u<<16,{128,128,128,128},0,0),
                "Post-reset report differs from stock");
    }
    // Every directed transition, including switching directions while keeping
    // Start held, selects an entire preset rather than accumulating toggles.
    for (unsigned mode : {2u,3u}) for (unsigned initial : {0u,1u,2u}) {
        for (unsigned target : {1u,2u}) {
            CPU c(changed); c.xd(0x8542)=mode; c.d[0x51]=1;
            if (initial) hold(c,start_button|(initial==1 ? right_button : up_button));
            require(c.xd(state_address)==initial, "Initial preset selection failed");
            if (initial==target) tick(c,start_button);
            hold(c,start_button|(target==1 ? right_button : up_button));
            require(c.xd(state_address)==(initial==target ? 0 : target), "Presets stacked or transition failed");
            require(c.modeled_nv_saves==0, "Preset transition wrote nonvolatile settings");
        }
        for (uint32_t other : {start_button,right_button,up_button,
                              chord|(1u<<12),chord|up_button,chord|(1u<<15),
                              start_button|up_button|(1u<<12),start_button|up_button|(1u<<15)}) {
            CPU rejected(changed); rejected.xd(0x8542)=mode; rejected.xd(state_address)=initial;
            for (unsigned i=0; i<1500; ++i) tick(rejected,other);
            require(rejected.xd(state_address)==initial, "Unrelated or diagonal shortcut changed preset");
        }
    }
    // Both displaced shortcuts still run their original save paths in non-PC profiles.
    for (unsigned mode : {0u,1u}) for (unsigned preset : {1u,2u}) {
        CPU before(stock), after(changed);
        before.xd(0x8542)=mode; after.xd(0x8542)=mode;
        before.d[0x51]=after.d[0x51]=1;
        before.d[0x52]=after.d[0x52]=0x40;
        after.xd(state_address)=2;
        uint32_t selected_chord=start_button|(preset==1 ? right_button : up_button);
        hold(before,selected_chord); hold(after,selected_chord);
        require(after.xd(state_address)==2, "Non-PC shortcut modified PC preset state");
        require(before.d[0x51]==(preset==1 ? 4 : 2) && before.d[0x51]==after.d[0x51],
                "Legacy layout changed");
        require(before.modeled_nv_saves==1 && after.modeled_nv_saves==1,
                "Legacy shortcut no longer follows stock settings-save path");
        for (unsigned i=0x4c; i<=0x52; ++i)
            require(before.d[i]==after.d[i], "Legacy macro state changed");
    }
    for (uint8_t initial : {0u,1u,2u,85u,255u}) {
        CPU c(changed); c.x.fill(0xa5); c.xd(state_address)=initial;
        c.run(0x376e,0x1d24);
        require(std::all_of(c.x.begin(),c.x.end(),[](uint8_t v){return v==0;}),
                "Startup memory clear did not cover the allocated state");
    }
}

static void check_physical_layout(const Bytes& stock, const Bytes& changed) {
    // Independently spell out each physical face button's expected stock output
    // identity. For SEGA: A takes X, B takes A, C takes B, X takes stock Z,
    // Y stays Y and Z takes stock C. This includes the Street Fighter C/Z routing.
    const unsigned physical[]={8,9,16,10,11,18}; // A B C X Y Z
    const unsigned targets[][6]={{8,9,16,10,11,18},{8,9,18,10,11,16},{10,8,9,18,11,16}};
    for (unsigned mode : {2u,3u}) for (unsigned preset : {0u,1u,2u})
        for (uint8_t options : {0u,0x40u}) for (unsigned i=0;i<6;++i) {
            require(report(changed,mode,preset,1u<<physical[i],{128,128,128,128},0,0,options)==
                    report(stock,mode,0,1u<<targets[preset][i],{128,128,128,128},0,0,options),
                    "Physical button layout mismatch");
        }
    // Corrupt/uninitialized values must not accidentally enable a partial preset.
    for (unsigned mode : {2u,3u}) for (uint8_t invalid : {3u,85u,255u})
        require(report(changed,mode,invalid,0x010100,{0,255,31,219},17,43)==
                report(stock,mode,0,0x010100,{0,255,31,219},17,43), "Unknown preset did not preserve stock");
}

int main(int argc, char** argv) {
    try {
        require(argc==3, "Usage: verify_polymega_toggle STOCK_DECODED CANDIDATE_DECODED");
        auto read=[](const char* p){std::ifstream f(p,std::ios::binary);require(bool(f),"File open failed");return Bytes(std::istreambuf_iterator<char>(f),{});};
        auto stock=read(argv[1]), changed=read(argv[2]);
        require(stock.size()==32768 && changed.size()==32768,"Wrong ROM size");
        check_macro(stock,changed);
        check_physical_layout(stock,changed);
        const unsigned bits[]={8,9,10,11,16,18,7,6,17,19,20,22,21};
        const uint32_t dpad[]={1u<<14,(1u<<14)|(1u<<13),1u<<13,(1u<<13)|(1u<<15),
                               1u<<15,(1u<<15)|(1u<<12),1u<<12,(1u<<12)|(1u<<14),0};
        const unsigned xhat[]={1,9,8,10,2,6,4,5,0};
        uint64_t comparisons=0, analog_reports=0;
        for (unsigned mask=0; mask<(1u<<13); ++mask) {
            uint32_t raw=0;
            for(unsigned i=0;i<13;++i)if(mask&(1u<<i))raw|=1u<<bits[i];
            for (unsigned hat=0; hat<9; ++hat) {
                uint32_t input=raw|dpad[hat];
                std::array<uint8_t,4> axes={uint8_t(mask),uint8_t(mask>>3),uint8_t(mask*37+hat),uint8_t(mask*13-hat)};
                uint8_t lt=mask*17+hat, rt=mask*31+hat;
                for (unsigned mode : {2u,3u}) for (uint8_t options : {0u,0x40u}) {
                    for (uint8_t preset : {0u,1u,2u}) {
                        auto expected=report(stock,mode,0,mapped_input(input,preset),axes,lt,rt,options);
                        auto after=report(changed,mode,preset,input,axes,lt,rt,options);
                        require(after==expected, "Report differs from physical preset model");
                        if (mode==3) require((after[2]&15)==xhat[hat], "Independent D-pad changed");
                        verify_analog(after,mode,input,axes,lt,rt);
                        ++comparisons; ++analog_reports;
                    }
                }
            }
        }
        // All 65,536 left-stick X/Y pairs. Right stick sweeps independently; D-pad
        // is held right even when either stick points left. No axis is digitized.
        uint64_t xy_reports=0;
        for (unsigned x=0; x<256; ++x) for (unsigned y=0; y<256; ++y) {
            std::array<uint8_t,4> axes={uint8_t(x),uint8_t(y),uint8_t(255-y),uint8_t(255-x)};
            for (unsigned mode : {2u,3u}) for (uint8_t preset : {0u,1u,2u}) {
                auto out=report(changed,mode,preset,right_button,axes,uint8_t(x),uint8_t(y));
                verify_analog(out,mode,right_button,axes,uint8_t(x),uint8_t(y));
                require(mode==2 ? bool(out[2]&0x20) : (out[2]&15)==8, "D-pad lost during analog sweep");
                ++xy_reports; ++analog_reports;
            }
        }
        std::cout << "{\"status\":\"passed\",\"report_comparisons\":" << comparisons
                  << ",\"analog_report_checks\":" << analog_reports
                  << ",\"xy_sweep_reports\":" << xy_reports
                  << ",\"macro_iterations\":" << macro_iterations
                  << ",\"hardware_tested\":false,\"scope\":\"Actual report dispatcher, macro detector/hook, and startup RAM-clear instructions. PS3 template copy and legacy NVM save modeled.\"}\n";
    } catch (const std::exception& e) { std::cerr<<e.what()<<"\n"; return 1; }
}
