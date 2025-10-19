import tkinter as tk
from tkinter import ttk
import queue, threading, time, json, uuid
import zmq



STATUS_QUEUED = "queued"
STATUS_SENDING = "sending"
STATUS_SENT = "sent"
STATUS_FAILED = "failed"



class ClientSideGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("RadioBlazers - Base Station")
        self.root.geometry("800x600")

        # --- ZMQ setup ---
        self.context = zmq.Context.instance()

        # Outgoing messages -> GNU Radio
        self.push_sock = self.context.socket(zmq.PUSH)
        self.push_sock.connect("tcp://localhost:6665")

        # Feedback from GNU Radio (tx success/failure)
        self.feedback_pull = self.context.socket(zmq.PULL)
        self.feedback_pull.connect("tcp://localhost:6667")

        # Incoming chat messages from GNU Radio
        self.incoming_pull = self.context.socket(zmq.PULL)
        self.incoming_pull.connect("tcp://localhost:6556")

        self.base_addr = "00"
        # MODIFY THIS FOR DIFFERENT USERS------------
        self.client_addr = "01"
        self.client_name = "User 1"
        #-------------------------------------------

        # --- Outgoing processing queue (PriorityQueue supports “front/back” via priority) ---
        # item: (priority:int, seq:int, message_dict)
        self.outgoing_queue = queue.PriorityQueue()
        self._seq = 0  # FIFO tie-breaker for same priority

        # message_id -> message_dict (track & update status)
        self.messages = {}

        self.message_ui = {}  # message_id -> {"user": str, "status_tag": str}

        

        # Thread controls
        self._stop = threading.Event()

        self.setup_ui()
        self.start_threads()


        # graceful close
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    

    def setup_ui(self):
        # Main grid weights for responsiveness
        self.root.rowconfigure(0, weight=0)
        self.root.rowconfigure(1, weight=1)
        self.root.columnconfigure(0, weight=1)


        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.grid(row=0, column=0, sticky="ew")
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.columnconfigure(2, weight=0)
        main_frame.columnconfigure(3, weight=0)

        title = ttk.Label(main_frame, text=f"RadioBlazers Client: {self.client_name}", font=('Arial', 16, 'bold'))
        title.grid(row=0, column=0, columnspan=4, pady=(0,10), sticky="w")


        # uncertain code-----------------------
        chat_frame = ttk.Frame(self.root, padding=10)
        chat_frame.rowconfigure(0, weight=1)
        chat_frame.columnconfigure(0, weight=1)
        chat_frame.grid(row=1, column=0, pady=(0,10), sticky="nsew")

        self.chat_widget = tk.Text(chat_frame, wrap="word", state="disabled", spacing1=4, spacing3=6)
        vsb = ttk.Scrollbar(chat_frame, orient="vertical", command=self.chat_widget.yview)
        self.chat_widget.configure(yscrollcommand=vsb.set)
        self.chat_widget.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")

        # tags: left for received, right for sent, and small-status
        self.chat_widget.tag_configure("recv", justify="left", lmargin1=6, lmargin2=12, rmargin=60)
        self.chat_widget.tag_configure("sent", justify="right", lmargin1=60, lmargin2=60, rmargin=6)
        self.chat_widget.tag_configure("status", font=("Arial", 8, "italic"))



        compose = ttk.LabelFrame(main_frame, text="Compose Message", padding=10)
        compose.grid(row=1, column=0, columnspan=4, sticky="ew")
        for c in range(4):
            compose.columnconfigure(c, weight=1 if c in (1,) else 0)
        

        ttk.Label(compose, text="Message:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.message_entry = ttk.Entry(compose, width=50)
        self.message_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=5)

        self.send_button = ttk.Button(compose, text="Send Message", command=self.send_message)
        self.send_button.grid(row=1, column=2, padx=5, pady=5, sticky="e")

        self.send_button_urgent = ttk.Button(compose, text="Send Urgent Message", command=self.send_priority)
        self.send_button_urgent.grid(row=1, column=3, padx=5, pady=5, sticky="e")

        #------------------------------

    
    # ----- UI helpers -----
    def _append_sent_message(self, message_id: str, msg_text: str, status: str):
        """Insert a right-aligned bubble + a status line with a unique tag for later in-place updates."""
        def _do():
            self.chat_widget.configure(state="normal")

            # insert message (right aligned)
            self.chat_widget.insert("end", msg_text + "\n", "sent")


            # insert status with a unique tag we can later replace in-place
            status_tag = f"status_{message_id}"
            status_str = f"[{status}]\n\n"
            self.chat_widget.insert("end", status_str, ("status", "sent", status_tag))

            # save for later updates
            self.message_ui[message_id] = {"status_tag": status_tag}

            self.chat_widget.see("end")
            self.chat_widget.configure(state="disabled")
        self.root.after(0, _do)


    def _append_received_message(self, msg_text: str):
        def _do():
            self.chat_widget.configure(state="normal")
            self.chat_widget.insert("end", msg_text + "\n\n", "recv")
            self.chat_widget.see("end")
            self.chat_widget.configure(state="disabled")
        self.root.after(0, _do)

    
    def _set_status(self, message_id: str, new_status: str):
        """Replace the existing status text [old] with [new_status] using the stored tag."""
        ui = self.message_ui.get(message_id)
        msg = self.messages.get(message_id)

        if not ui or not msg:
            return
        
        user_name = self.client_name
        status_tag = ui["status_tag"]


        def _do():
            ranges = self.chat_widget.tag_ranges(status_tag)
            if len(ranges) == 2:
                start, end = ranges
                self.chat_widget.configure(state="normal")
                self.chat_widget.delete(start, end)
                self.chat_widget.insert(start, f"[{new_status}]\n\n", ("status", "sent", status_tag))
                self.chat_widget.configure(state="disabled")
                self.chat_widget.see("end")
        self.root.after(0, _do)

    

    # --- Public (button) actions ---
    def send_message(self):
        self._enqueue_message(priority=1) 



    def send_priority(self):
        self._enqueue_message(priority=0)


    def _enqueue_message(self, priority: int):
        text_val = self.message_entry.get().strip()
        if not text_val:
            return
        
        message_id = str(uuid.uuid4)
        msg = {
            "message_id": message_id,
            "from_addr": self.base_addr,
            "text": text_val,
            "status": STATUS_QUEUED,
            "ts": time.time()
        }
        self.messages[message_id] = msg

        self._seq += 1
        self.outgoing_queue.put((priority, self._seq, msg))

        # Insert bubble + initial status
        self._append_sent_message(message_id, text_val, STATUS_QUEUED)

        self.message_entry.delete(0, "end")
    

    # --- threads ----
    def start_threads(self):
        # worker thread for sending queue
        self.worker_thread = threading.Thread(target=self._process_queue_loop, daemon=True)
        self.worker_thread.start()

        # Feedback listener (reused by worker with blocking wait, but also buffers)
        self.feedback_buffer = {}  # message_id -> {"ok":bool}
        self.feedback_lock = threading.Lock()
        self.feedback_thread = threading.Thread(target=self._feedback_listener_loop, daemon=True)
        self.feedback_thread.start()

        # incoming chat listener
        self.incoming_thread = threading.Thread(target=self._incoming_listener_loop, daemon=True)
        self.incoming_thread.start()


    def _process_queue_loop(self):
        """send next message and wait indefinitely for its feedback before proceeding"""
        while not self._stop.is_set():
            try:
                priority, _, msg = self.outgoing_queue.get(timeout=0.2)
            except queue.Empty:
                continue

            message_id = msg["message_id"]
            
            msg["status"] = STATUS_SENDING
            self._set_status(message_id, STATUS_SENDING)


            # send over zmq push
            payload = msg["text"]

            try:
                self.push_sock.send_string(payload, flags=0)
            except Exception:
                msg["status"] = STATUS_FAILED
                self._set_status(message_id, STATUS_FAILED)
                continue

            
            # WAIT INDEFINITELY for feedback (sent/failed). if none, remain 'sending'.
            ok = self._wait_for_feedback(message_id)
            if ok is None:
                # stopping, leave as is
                continue
            elif ok is True:
                msg["status"] = STATUS_SENT
                self._set_status(message_id, STATUS_SENT)
            else:
                msg["status"] = STATUS_FAILED
                self._set_status(message_id, STATUS_FAILED)
            
    

    def _wait_for_feedback(self, message_id: str) -> bool | None:
        """block in worker thread until feedback for message_id arrives. returns True/False on feedback, or None if we're stopping."""

        while not self._stop.is_set():
            with self.feedback_lock:
                data = self.feedback_buffer.pop(message_id, None)
            if data is not None:
                return bool(data["ok"])
            time.sleep(0.05)
        return None
    


    def _feedback_listener_loop(self):
        """continuously read feedback and stash it for the worker"""
        poller = zmq.Poller()
        poller.register(self.feedback_pull, zmq.POLLIN)

        while not self._stop.is_set():
            socks = dict(poller.poll(timeout=200))  # ms
            if self.feedback_pull in socks and socks[self.feedback_pull] == zmq.POLLIN:
                try:
                    msg = self.feedback_pull.recv(flags=zmq.NOBLOCK)
                except zmq.Again:
                    continue

                # Expect: "True" or "False"
                fb = msg.decode("utf-8")
                if fb == "True":
                    with self.feedback_lock:
                        self.feedback_buffer.append({"ok": True})
                if fb == "False":
                    with self.feedback_lock:
                        self.feedback_buffer.append({"ok": False})
                # if msg.get("type") == "tx_ack" and "message_id" in msg:
                #     with self.feedback_lock:
                #         self.feedback_buffer[msg["message_id"]] = {"ok": bool(msg.get("ok"))}
    
    def _incoming_listener_loop(self):
        """Continuously read incoming chat and post to the correct tab"""

        poller = zmq.Poller()
        poller.register(self.incoming_pull, zmq.POLLIN)
        while not self._stop.is_set():
            socks = dict(poller.poll(timeout=200)) # ms
            if self.incoming_pull in socks and socks[self.incoming_pull] == zmq.POLLIN:
                try:
                    msg = self.incoming_pull.recv(flags=zmq.POLLIN)
                except zmq.Again:
                    continue

                # Expect: "message"
                text = msg.decode("utf-8")
                self._append_received_message(text)
                # if msg.get("type") == "rx":
                #     text = msg.get("text", "")
                #     self._append_received_message(text)

    

    def on_close(self):
        self._stop.set()
        try:
            self.push_sock.close(0)
            self.feedback_pull.close(0)
            self.incoming_pull.close(0)
            self.context.term()
        except Exception:
            pass
        self.root.destroy()





# --- main ---
def main():
    root = tk.Tk()
    app = ClientSideGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()