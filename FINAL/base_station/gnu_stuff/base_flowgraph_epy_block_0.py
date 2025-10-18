

import numpy as np
from gnuradio import gr
import pmt
import zmq

def byte_list_to_bitstring(int_arr):
    return ''.join(f'{b:08b}' for b in int_arr)

def bit_string_to_byte_list(bits):
    if len(bits) % 8 != 0:
        raise ValueError("length not multiple of 8")
    return [int(bits[i:i+8], 2) for i in range(0, len(bits), 8)]

def msg_string_to_bitstring(msg_str):
    bits = ''.join(f'{b:08b}' for b in msg_str.encode('utf-8'))
    return bits

def bitstring_to_text(bits, encoding='utf-8'):
    if len(bits) % 8 != 0:
        raise ValueError("Bitstring length must be a multiple of 8")
    data = bytes(int(bits[i:i+8], 2) for i in range(0, len(bits), 8))
    return data.decode(encoding)

class blk(gr.basic_block):  

    def __init__(self, example_param=1.0):  
        """arguments to this function show up as parameters in GRC"""
        gr.sync_block.__init__(
            self,
            name='Base_Station_Processor',   
            in_sig=[],
            out_sig=[]
        )

        # ui sockets
        self.context = zmq.Context.instance()

        self.feedback_push_sock = self.context.socket(zmq.PUSH)
        self.feedback_push_sock.bind("tcp://localhost:5557")

        self.msg_to_ui_sock = self.context.socket(zmq.PUSH)
        self.msg_to_ui_sock.bind("tcp://localhost:5556")

        # misc
        self.transmit_func_busy = False
        
        # types
        self.pkt_data = '00'
        self.pkt_ack = '11'

        # my address
        self.my_address = '00'

        # user node addresses
        self.addrs = {"User 1": '01', "User 2": '10', "User 3": '11'}
        self.users = {'01': 'user1', '10': 'user2', '11': 'user3'}

        # for ack purposes
        self.ack_received = False # the TX will know that an ack was received using this variable, then it reads the received_seq_number
        self.received_ack_seq_number = 0
        self.current_receiver = '' # use this for debug purposes 

        

        # defining ports
        self.message_port_register_in(pmt.intern('Msg_in'))
        self.message_port_register_out(pmt.intern('Msg_out'))
        self.message_port_register_out(pmt.intern('feedback'))
        self.message_port_register_out(pmt.intern('Pkt_out'))
        self.message_port_register_in(pmt.intern('Pkt_in'))

        self.set_msg_handler(pmt.intern('Pkt_in'), self.inbound_pkt_handler)
    
    def crc_check(self, bitstring):
        pass

    def create_packet(self, tpe, dest_addr, src_addr, seq_no, payload=""):
        packet_str = tpe + dest_addr + src_addr + seq_no + payload
        return packet_str
    
    def transmit(self, pkt_string):
        try:
            int_arr = bit_string_to_byte_list(pkt_string)
            vec = pmt.init_u8vector(len(int_arr), int_arr)
            pdu = pmt.cons(pmt.PMT_NIL, vec)

            self.message_port_pub(pmt.intern('Pkt_out'), pdu)
        except Exception as e:
            print(f"Custom_error: Error transmitting packet: {e}")


    def inbound_pkt_handler(self, pkt):
        # assuming the packet is a uint
        if not pmt.is_pair(pkt):
            return
        vec = pmt.cdr(pkt)
        if not pmt.is_u8vector(vec):
            return
        
        data_arr = pmt.u8vector_elements(vec)
        pkt_bitstring = byte_list_to_bitstring(data_arr)

        pkt_type = pkt_bitstring[:2]
        pkt_dest_addr = pkt_bitstring[2:4]
        pkt_src_addr = pkt_bitstring[4:6]
        pkt_seq_num = pkt_bitstring[6:8]
        pkt_payload = pkt_bitstring[8:]

        if (pkt_type == self.pkt_data): # the pkt received is a data packet
            if (pkt_dest_addr == self.my_address):
                pkt_str = self.create_packet(self.pkt_ack, pkt_src_addr, pkt_dest_addr, pkt_seq_num + 1)
                while (self.transmit_func_busy == True):
                    print("base_RX: waiting for transmit to free")
                    continue
                self.transmit_func_busy = True
                self.transmit(pkt_str)
                self.transmit_func_busy = False
                payload_text = bitstring_to_text(pkt_payload)
                
                
                text = self.users[pkt_src_addr] + payload_text

                # creating the pdu to send to UI
                # text_b = text.encode("utf-8")
                # pdu = pmt.cons(pmt.PMT_NIL, pmt.init_u8vector(len(text_b), bytearray(text_b)))
                # self.message_port_pub(pmt.intern('Msg_out'), pdu)

                # send message to ui
                self.msg_to_ui_sock.send_string(text)

                # sending feedback to ui
                self.feedback_push_sock.send_string("True")

            else:
                # the packet is not meant for me
                return
        elif (pkt_type == self.pkt_ack): # the pkt received is a ack packet
            if (pkt_dest_addr == self.my_address):
                self.current_receiver = self.users[pkt_src_addr]
                self.received_ack_seq_number = pkt_seq_num
                self.ack_received = True
                if (pkt_payload != ''):
                    raise ValueError(f"malinda's custom error: an acknowledgement packet cannot have a payload")
            else:
                # the packet is not meant for me
                # POSSIBLE ERROR PLACE, PLEASE CHECK WHEN TESING
                return
        else:
            raise ValueError(f"malinda's custom error: {pkt_type} is not a valid type")
        
    
    



