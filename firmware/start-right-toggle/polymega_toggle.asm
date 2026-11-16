; Generated from build_polymega_toggle.py; addresses are decoded ROM offsets.
; Existing Start+Right detection/hold timing enters toggle via LJMP at 0x26b6.
; State 0x85ff is volatile and cleared by the stock 0x8000..0x8fff startup loop.
; Analog axes/triggers use the unchanged stock report builders.
6000            toggle:
6000  90 85 42      mov dptr,# 0x8542
6003  e0            movx a,@dptr
6004  b4 02 02      cjne a,#0x02,check_xinput
6007  80 03         sjmp toggle_pc
6009            check_xinput:
6009  b4 03 13      cjne a,#0x03,legacy_shortcut
600c            toggle_pc:
600c  90 85 27      mov dptr,# 0x8527
600f  e0            movx a,@dptr
6010  54 f0         anl a,#0xf0
6012  b4 20 07      cjne a,#0x20,resume_macro
6015  90 85 ff      mov dptr,# 0x85ff
6018  e0            movx a,@dptr
6019  64 01         xrl a,#0x01
601b  f0            movx @dptr,a
601c            resume_macro:
601c  02 26 c1      ljmp 0x26c1
601f            legacy_shortcut:
601f  75 51 04      mov 0x51,#0x04
6022  02 26 b9      ljmp 0x26b9
6025            xinput_report:
6025  12 2e 58      lcall 0x2e58
6028  90 85 ff      mov dptr,# 0x85ff
602b  e0            movx a,@dptr
602c  60 0b         jz xinput_done
602e  90 84 33      mov dptr,# 0x8433
6031  e0            movx a,@dptr
6032  54 03         anl a,#0x03
6034  60 03         jz xinput_done
6036  b4 03 01      cjne a,#0x03,xinput_exchange
6039            xinput_done:
6039  22            ret
603a            xinput_exchange:
603a  e0            movx a,@dptr
603b  64 03         xrl a,#0x03
603d  f0            movx @dptr,a
603e  22            ret
603f            ps3_report:
603f  12 23 7d      lcall 0x237d
6042  90 85 ff      mov dptr,# 0x85ff
6045  e0            movx a,@dptr
6046  60 20         jz ps3_done
6048  90 84 33      mov dptr,# 0x8433
604b  e0            movx a,@dptr
604c  54 0c         anl a,#0x0c
604e  60 09         jz ps3_pressure
6050  b4 0c 02      cjne a,#0x0c,ps3_exchange
6053  80 04         sjmp ps3_pressure
6055            ps3_exchange:
6055  e0            movx a,@dptr
6056  64 0c         xrl a,#0x0c
6058  f0            movx @dptr,a
6059            ps3_pressure:
6059  90 84 44      mov dptr,# 0x8444
605c  e0            movx a,@dptr
605d  ff            mov r7,a
605e  a3            inc dptr
605f  e0            movx a,@dptr
6060  fe            mov r6,a
6061  ef            mov a,r7
6062  f0            movx @dptr,a
6063  90 84 44      mov dptr,# 0x8444
6066  ee            mov a,r6
6067  f0            movx @dptr,a
6068            ps3_done:
6068  22            ret
