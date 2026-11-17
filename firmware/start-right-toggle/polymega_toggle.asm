; Generated from build_polymega_toggle.py; addresses are decoded ROM offsets.
; Stock Start+Right/Up hold detection enters hooks at 0x26b6/0x26e1.
; State 0x85ff is volatile and cleared by the stock 0x8000..0x8fff startup loop.
; Analog axes/triggers use the unchanged stock report builders.
6000            toggle:
6000  90 85 42      mov dptr,# 0x8542
6003  e0            movx a,@dptr
6004  b4 02 02      cjne a,#0x02,toggle_check_xinput
6007  80 03         sjmp toggle_pc
6009            toggle_check_xinput:
6009  b4 03 19      cjne a,#0x03,toggle_legacy
600c            toggle_pc:
600c  90 85 27      mov dptr,# 0x8527
600f  e0            movx a,@dptr
6010  54 f0         anl a,#0xf0
6012  b4 20 0d      cjne a,#0x20,toggle_resume
6015  90 85 ff      mov dptr,# 0x85ff
6018  e0            movx a,@dptr
6019  b4 01 03      cjne a,#0x01,toggle_select
601c  e4            clr a
601d  80 02         sjmp toggle_store
601f            toggle_select:
601f  74 01         mov a,#1
6021            toggle_store:
6021  f0            movx @dptr,a
6022            toggle_resume:
6022  02 26 c1      ljmp 0x26c1
6025            toggle_legacy:
6025  75 51 04      mov 0x51,#4
6028  02 26 b9      ljmp 0x26b9
602b            toggle_sega:
602b  90 85 42      mov dptr,# 0x8542
602e  e0            movx a,@dptr
602f  b4 02 02      cjne a,#0x02,toggle_sega_check_xinput
6032  80 03         sjmp toggle_sega_pc
6034            toggle_sega_check_xinput:
6034  b4 03 19      cjne a,#0x03,toggle_sega_legacy
6037            toggle_sega_pc:
6037  90 85 27      mov dptr,# 0x8527
603a  e0            movx a,@dptr
603b  54 f0         anl a,#0xf0
603d  b4 40 0d      cjne a,#0x40,toggle_sega_resume
6040  90 85 ff      mov dptr,# 0x85ff
6043  e0            movx a,@dptr
6044  b4 02 03      cjne a,#0x02,toggle_sega_select
6047  e4            clr a
6048  80 02         sjmp toggle_sega_store
604a            toggle_sega_select:
604a  74 02         mov a,#2
604c            toggle_sega_store:
604c  f0            movx @dptr,a
604d            toggle_sega_resume:
604d  02 26 ec      ljmp 0x26ec
6050            toggle_sega_legacy:
6050  75 51 02      mov 0x51,#2
6053  02 26 e4      ljmp 0x26e4
6056            xinput_report:
6056  12 2e 58      lcall 0x2e58
6059  90 85 ff      mov dptr,# 0x85ff
605c  e0            movx a,@dptr
605d  60 0e         jz xinput_done
605f  b4 01 11      cjne a,#0x01,xinput_check_sega
6062  90 84 33      mov dptr,# 0x8433
6065  e0            movx a,@dptr
6066  54 03         anl a,#0x03
6068  60 03         jz xinput_done
606a  b4 03 01      cjne a,#0x03,xinput_exchange
606d            xinput_done:
606d  22            ret
606e            xinput_exchange:
606e  e0            movx a,@dptr
606f  64 03         xrl a,#0x03
6071  f0            movx @dptr,a
6072  22            ret
6073            xinput_check_sega:
6073  b4 02 f7      cjne a,#0x02,xinput_done
6076  e5 52         mov a,0x52
6078  54 40         anl a,#0x40
607a  60 33         jz xinput_sega
607c            xinput_sega_flipped:
607c  90 84 33      mov dptr,# 0x8433
607f  e0            movx a,@dptr
6080  ff            mov r7,a
6081  54 4c         anl a,#0x4c
6083  fe            mov r6,a
6084  ef            mov a,r7
6085  54 01         anl a,#0x01
6087  60 03         jz xinput_flipped_skip_0
6089  43 06 10      orl 0x06,#0x10
608c            xinput_flipped_skip_0:
608c  ef            mov a,r7
608d  54 02         anl a,#0x02
608f  60 03         jz xinput_flipped_skip_1
6091  43 06 01      orl 0x06,#0x01
6094            xinput_flipped_skip_1:
6094  ef            mov a,r7
6095  54 20         anl a,#0x20
6097  60 03         jz xinput_flipped_skip_5
6099  43 06 80      orl 0x06,#0x80
609c            xinput_flipped_skip_5:
609c  ef            mov a,r7
609d  54 10         anl a,#0x10
609f  60 03         jz xinput_flipped_skip_4
60a1  43 06 20      orl 0x06,#0x20
60a4            xinput_flipped_skip_4:
60a4  ef            mov a,r7
60a5  54 80         anl a,#0x80
60a7  60 03         jz xinput_flipped_skip_7
60a9  43 06 02      orl 0x06,#0x02
60ac            xinput_flipped_skip_7:
60ac  ee            mov a,r6
60ad  f0            movx @dptr,a
60ae  22            ret
60af            xinput_sega:
60af  90 84 33      mov dptr,# 0x8433
60b2  e0            movx a,@dptr
60b3  ff            mov r7,a
60b4  54 8c         anl a,#0x8c
60b6  fe            mov r6,a
60b7  ef            mov a,r7
60b8  54 01         anl a,#0x01
60ba  60 03         jz xinput_sega_skip_0
60bc  43 06 20      orl 0x06,#0x20
60bf            xinput_sega_skip_0:
60bf  ef            mov a,r7
60c0  54 02         anl a,#0x02
60c2  60 03         jz xinput_sega_skip_1
60c4  43 06 01      orl 0x06,#0x01
60c7            xinput_sega_skip_1:
60c7  ef            mov a,r7
60c8  54 10         anl a,#0x10
60ca  60 03         jz xinput_sega_skip_4
60cc  43 06 40      orl 0x06,#0x40
60cf            xinput_sega_skip_4:
60cf  ef            mov a,r7
60d0  54 20         anl a,#0x20
60d2  60 03         jz xinput_sega_skip_5
60d4  43 06 10      orl 0x06,#0x10
60d7            xinput_sega_skip_5:
60d7  ef            mov a,r7
60d8  54 40         anl a,#0x40
60da  60 03         jz xinput_sega_skip_6
60dc  43 06 02      orl 0x06,#0x02
60df            xinput_sega_skip_6:
60df  ee            mov a,r6
60e0  f0            movx @dptr,a
60e1  22            ret
60e2            ps3_report:
60e2  12 23 7d      lcall 0x237d
60e5  90 85 ff      mov dptr,# 0x85ff
60e8  e0            movx a,@dptr
60e9  60 23         jz ps3_done
60eb  b4 01 21      cjne a,#0x01,ps3_check_sega
60ee  90 84 33      mov dptr,# 0x8433
60f1  e0            movx a,@dptr
60f2  54 0c         anl a,#0x0c
60f4  60 09         jz ps3_pressure
60f6  b4 0c 02      cjne a,#0x0c,ps3_exchange
60f9  80 04         sjmp ps3_pressure
60fb            ps3_exchange:
60fb  e0            movx a,@dptr
60fc  64 0c         xrl a,#0x0c
60fe  f0            movx @dptr,a
60ff            ps3_pressure:
60ff  90 84 44      mov dptr,# 0x8444
6102  e0            movx a,@dptr
6103  ff            mov r7,a
6104  a3            inc dptr
6105  e0            movx a,@dptr
6106  fe            mov r6,a
6107  ef            mov a,r7
6108  f0            movx @dptr,a
6109  90 84 44      mov dptr,# 0x8444
610c  ee            mov a,r6
610d  f0            movx @dptr,a
610e            ps3_done:
610e  22            ret
610f            ps3_check_sega:
610f  b4 02 fc      cjne a,#0x02,ps3_done
6112            ps3_sega:
6112  90 84 33      mov dptr,# 0x8433
6115  e0            movx a,@dptr
6116  ff            mov r7,a
6117  54 83         anl a,#0x83
6119  fe            mov r6,a
611a  ef            mov a,r7
611b  54 04         anl a,#0x04
611d  60 03         jz ps3_sega_skip_2
611f  43 06 40      orl 0x06,#0x40
6122            ps3_sega_skip_2:
6122  ef            mov a,r7
6123  54 08         anl a,#0x08
6125  60 03         jz ps3_sega_skip_3
6127  43 06 04      orl 0x06,#0x04
612a            ps3_sega_skip_3:
612a  ef            mov a,r7
612b  54 10         anl a,#0x10
612d  60 03         jz ps3_sega_skip_4
612f  43 06 08      orl 0x06,#0x08
6132            ps3_sega_skip_4:
6132  ef            mov a,r7
6133  54 20         anl a,#0x20
6135  60 03         jz ps3_sega_skip_5
6137  43 06 10      orl 0x06,#0x10
613a            ps3_sega_skip_5:
613a  ef            mov a,r7
613b  54 40         anl a,#0x40
613d  60 03         jz ps3_sega_skip_6
613f  43 06 20      orl 0x06,#0x20
6142            ps3_sega_skip_6:
6142  ee            mov a,r6
6143  f0            movx @dptr,a
6144  90 84 44      mov dptr,# 0x8444
6147  e0            movx a,@dptr
6148  ff            mov r7,a
6149  90 84 45      mov dptr,# 0x8445
614c  e0            movx a,@dptr
614d  90 84 44      mov dptr,# 0x8444
6150  f0            movx @dptr,a
6151  90 84 46      mov dptr,# 0x8446
6154  e0            movx a,@dptr
6155  90 84 45      mov dptr,# 0x8445
6158  f0            movx @dptr,a
6159  90 84 47      mov dptr,# 0x8447
615c  e0            movx a,@dptr
615d  90 84 46      mov dptr,# 0x8446
6160  f0            movx @dptr,a
6161  90 84 48      mov dptr,# 0x8448
6164  e0            movx a,@dptr
6165  90 84 47      mov dptr,# 0x8447
6168  f0            movx @dptr,a
6169  90 84 48      mov dptr,# 0x8448
616c  ef            mov a,r7
616d  f0            movx @dptr,a
616e  22            ret
