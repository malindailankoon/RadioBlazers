#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pmt
from gnuradio import gr

class address_check(gr.basic_block):
    """
    Block to check address and strip it if matches
    """
    def __init__(self, my_address=0x01):
        gr.basic_block.__init__(
            self,
            name="address_check",
            in_sig=[],
            out_sig=[]
        )
        self.my_address = my_address
        self.message_port_register_in(pmt.intern("in"))
        self.message_port_register_out(pmt.intern("out"))
        self.set_msg_handler(pmt.intern("in"), self.handle_msg)

    def handle_msg(self, msg):
        if pmt.is_pair(msg):
            meta = pmt.car(msg)
            data = bytearray(pmt.u8vector_elements(pmt.cdr(msg)))
            if data[0] == self.my_address:
                # strip address
                payload = data[1:]
                out_msg = pmt.cons(meta, pmt.init_u8vector(len(payload), payload))
                self.message_port_pub(pmt.intern("out"), out_msg)
            # else drop silently
