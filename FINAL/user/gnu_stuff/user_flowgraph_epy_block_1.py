import threading
import zmq
import pmt
from gnuradio import gr
import json

class blk(gr.basic_block):
    """
    ZMQ PULL -> GNU Radio PDU (meta=PMT_NIL, data=u8vector)
    Accepts raw bytes/strings from external senders without PMT serialization.
    """

    def __init__(self, endpoint='tcp://127.0.0.1:6665', bind=False, rcv_timeout_ms=100):
        gr.basic_block.__init__(self, name="pyzmq_pull", in_sig=[], out_sig=[])

        # Params (editable in GRC via block args if you expose them)
        self.endpoint = endpoint
        self.bind = bool(bind)
        self.rcv_timeout_ms = int(rcv_timeout_ms)

        # Message out port
        self.message_port_register_out(pmt.intern("out"))

        # ZMQ state
        self._ctx = None
        self._sock = None
        self._thread = None
        self._running = threading.Event()

    # Start/stop are the right places to spin threads/sockets in GNU Radio
    def start(self):
        self._ctx = zmq.Context.instance()
        self._sock = self._ctx.socket(zmq.PULL)

        # Tame shutdown and avoid hangs
        self._sock.setsockopt(zmq.LINGER, 0)
        self._sock.setsockopt(zmq.RCVTIMEO, self.rcv_timeout_ms)
        # Optional HWM if you want tighter buffering:
        # self._sock.setsockopt(zmq.RCVHWM, 100)

        if self.bind:
            # Bind (listener)
            self._sock.bind(self.endpoint)           # e.g., "tcp://*:5555"
        else:
            # Connect (dialer)
            self._sock.connect(self.endpoint)        # e.g., "tcp://127.0.0.1:5555"

        self._running.set()
        self._thread = threading.Thread(target=self._rx_loop, daemon=True)
        self._thread.start()
        return super().start()

    def stop(self):
        self._running.clear()
        try:
            if self._thread:
                self._thread.join(timeout=1.0)
        except Exception:
            pass
        try:
            if self._sock:
                self._sock.close(0)
        except Exception:
            pass
        # Don’t terminate the shared context; other blocks may use it
        self._ctx = None
        self._sock = None
        return super().stop()

    def _rx_loop(self):
        while self._running.is_set():
            try:
                # Receive one ZMQ frame (bytes). Works with send(), send_string(), send_json() etc.
                frame = self._sock.recv()  # bytes; RCVTIMEO makes this return after timeout
            except zmq.Again:
                continue  # timeout, loop again
            except Exception as e:
                print("[pyzmq_pull] recv error:", e)
                break

            if not frame:
                continue
            
            # message = frame.decode("utf-8")
            frame = list(frame)
            print(frame)
            u8 = pmt.init_u8vector(len(frame), frame)
            pdu = pmt.cons(pmt.PMT_NIL, u8)
            self.message_port_pub(pmt.intern("out"), pdu)
