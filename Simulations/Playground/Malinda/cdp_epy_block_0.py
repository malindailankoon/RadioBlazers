#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pmt
from gnuradio import gr

class address_add(gr.basic_block):
    """
    Block to prepend an address byte to a PDU payload
    """
    def __init__(self, address=0x01):
        gr.basic_block.__init__(
            self,
            name="address_add",
            in_sig=[],
            out_sig=[]
        )
        self.address = address
        self.message_port_register_in(pmt.intern("in"))
        self.message_port_register_out(pmt.intern("out"))
        self.set_msg_handler(pmt.intern("in"), self.handle_msg)

    def handle_msg(self, msg):
        if pmt.is_pair(msg):
            meta = pmt.car(msg)
            data = bytearray(pmt.u8vector_elements(pmt.cdr(msg)))
            # prepend address
            data.insert(0, self.address)
            out_msg = pmt.cons(meta, pmt.init_u8vector(len(data), data))
            self.message_port_pub(pmt.intern("out"), out_msg)
