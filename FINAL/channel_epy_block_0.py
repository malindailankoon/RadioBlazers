

import numpy as np
from gnuradio import gr
import pmt
import zmq
import threading
import queue
import time
import random

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

    def __init__(self, UiMsgOutPort='tcp://127.0.0.1:5556',
                 UiFeedbackPort='tcp://127.0.0.1:5557',
                 NumberOfRetransmissions=10,
                 PropegationTime=0.5,
                 TransmissionTime=0.2):  
        """arguments to this function show up as parameters in GRC"""
        gr.sync_block.__init__(
            self,
            name='Base_Station_Processor',   
            in_sig=[],
            out_sig=[]
        )

        self.number_of_retransmissions = NumberOfRetransmissions
        self.propegation_time = PropegationTime
        self.transmission_time = TransmissionTime
        self.UiFeedbackPort = UiFeedbackPort
        self.UiMsgOutPort = UiMsgOutPort
        


        # ui sockets
        self.context = zmq.Context.instance()

        self.feedback_push_sock = self.context.socket(zmq.PUSH)
        try:
            self.feedback_push_sock.bind(self.UiFeedbackPort)
        except Exception as e:
            print(f"custom_error: cant connect to socket: {e}")

        self.msg_to_ui_sock = self.context.socket(zmq.PUSH)
        try:
            self.msg_to_ui_sock.bind(self.UiMsgOutPort)
        except Exception as e:
            print(f"custom_error: cant connect to socket: {e}")
        

        
        
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
        # self.message_port_register_out(pmt.intern('Msg_out'))
        # self.message_port_register_out(pmt.intern('feedback'))
        self.message_port_register_out(pmt.intern('Pkt_out'))
        self.message_port_register_in(pmt.intern('Pkt_in'))

        self.set_msg_handler(pmt.intern('Pkt_in'), self.inbound_pdu_handler)
        self.set_msg_handler(pmt.intern('Msg_in'), self.inbound_msg_handler)

        
        # setting up threads
        self._stop = threading.Event()
        self.lock = threading.Lock()

        self.inbound_pkt_buffer = queue.Queue() # holds byte arrays
        self.rx_thread = threading.Thread(target=self.rx_handler)

        self.inbound_msg_buffer = queue.Queue()
        self.tx_thread = threading.Thread(target=self.tx_handler)
        

        self.rx_thread.start()
        self.tx_thread.start()
    
    

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


    def rx_handler(self):
        while not self._stop.is_set():
            # assuming the packet is a uint
            try:
                pkt_bytes = self.inbound_pkt_buffer.get(timeout=0.1)
            except queue.Empty:
                continue
            
            pkt_bitstring = byte_list_to_bitstring(pkt_bytes)

            pkt_type = pkt_bitstring[:2]
            pkt_dest_addr = pkt_bitstring[2:4]
            pkt_src_addr = pkt_bitstring[4:6]
            pkt_seq_num = pkt_bitstring[6:8]
            pkt_payload = pkt_bitstring[8:]

            seq_num_int = int(pkt_seq_num, 2)


            if (pkt_type == self.pkt_data): # the pkt received is a data packet
                if (pkt_dest_addr == self.my_address):
                    new_seq_num = f"{(seq_num_int+1):02b}"
                    pkt_str = self.create_packet(self.pkt_ack, pkt_src_addr, pkt_dest_addr, new_seq_num)
                    
                    with self.lock:
                        self.transmit(pkt_str)

                    
                    payload_text = bitstring_to_text(pkt_payload)
                    
                    text = pkt_src_addr + ":" + payload_text

                    # creating the pdu to send to UI
                    # text_b = text.encode("utf-8")
                    # pdu = pmt.cons(pmt.PMT_NIL, pmt.init_u8vector(len(text_b), bytearray(text_b)))
                    # self.message_port_pub(pmt.intern('Msg_out'), pdu)

                    # send message to ui
                    self.msg_to_ui_sock.send_string(text)


                else:
                    # the packet is not meant for me
                    continue
            elif (pkt_type == self.pkt_ack): # the pkt received is a ack packet
                if (pkt_dest_addr == self.my_address):
                    self.current_receiver = pkt_src_addr
                    self.received_ack_seq_number = pkt_seq_num
                    self.ack_received = True
                    if (pkt_payload != ''):
                        raise ValueError(f"malinda's custom error: an acknowledgement packet cannot have a payload")
                else:
                    # the packet is not meant for me
                    # POSSIBLE ERROR PLACE, PLEASE CHECK WHEN TESING
                    continue
            else:
                raise ValueError(f"malinda's custom error: {pkt_type} is not a valid type")
    

    def tx_handler(self):
        while not self._stop.is_set():
            try:
                try:
                    msg_bytes = self.inbound_msg_buffer.get(timeout=0.1)
                except queue.Empty:
                    continue
            
                msg_string = msg_bytes.decode("utf-8", errors="strict")
                dest_addr, text = msg_string.split(":")


                msg_bitstring = msg_string_to_bitstring(text)
                current_seq_num = 0
                seq_num_str = f"{current_seq_num:02b}"
                current_pkt = self.create_packet(self.pkt_data, dest_addr, self.my_address, seq_num_str, msg_bitstring)

                K = 0
                success = False
                abort = False
                while (success != True and abort != True):
                    with self.lock:
                        self.transmit(current_pkt)
                    
                    time.sleep(2 * self.propegation_time)

                    if (self.ack_received == True):
                        with self.lock:
                            self.ack_received = False
                        if (self.received_ack_seq_number > current_seq_num):
                            if (self.current_receiver != dest_addr):
                                raise ValueError("malinda's custom error: the base got an unintended ack packet!")
                            
                            # send feedback to ui
                            self.feedback_push_sock.send_string("True")
                            success = True
                            continue
                    
                    K += 1
                    if (K > self.number_of_retransmissions):
                        self.feedback_push_sock.send_string("False")
                        abort = True
                        continue

                    R = random.getrandbits(K)

                    Tb = R * self.propegation_time
                    time.sleep(Tb)
                    continue


            
            except Exception as e:
                print(f"[custom_handler TX handler error: {e}")
            
                


    def inbound_msg_handler(self, pdu):
        try:
            if pmt.is_pair(pdu):
                data = pmt.cdr(pdu)

                msg_bytes = bytes(pmt.u8vector_elements(data))
                self.inbound_msg_buffer.put(msg_bytes)
        
        except Exception as e:
            print(f"[custom_error: Error handling Msg_in: {e}")
    
    def inbound_pdu_handler(self, pdu):
        try:
            if pmt.is_pair(pdu):
                data = pmt.cdr(pdu)

                rx_bytes = bytes(pmt.u8vector_elements(data))
                self.inbound_pkt_buffer.put(rx_bytes)

        
        except Exception as e:
            print(f"[custom_error: Error handling pdu_in: {e}")
    

    def on_close(self):
        self._stop.set()
        if self.rx_thread.is_alive():
            self.rx_thread.join()




