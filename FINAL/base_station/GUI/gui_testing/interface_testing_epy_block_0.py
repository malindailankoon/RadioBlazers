
import numpy as np
from gnuradio import gr
import pmt
import json


class blk(gr.basic_block): 
    

    def __init__(self):  
        gr.basic_block.__init__(
            self,
            name='zmq_message_debug',
            in_sig=[],
            out_sig=[]
        )
        
        self.message_port_register_in(pmt.intern("in"))
        self.set_msg_handler(pmt.intern("in"), self.handle_msg)
        


    def handle_msg(self, msg):
        
        
        data = pmt.cdr(msg)
        

        print(data)

        

        

        
        

