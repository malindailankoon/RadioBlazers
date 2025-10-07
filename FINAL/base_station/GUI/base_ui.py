import tkinter as tk
from tkinter import ttk
import queue, threading, time, json, uuid
import zmq
from collections import defaultdict

STATUS_QUEUED = "queued"
STATUS_SENDING = "sending"
STATUS_SENT = "sent"
STATUS_FAILED = "failed"

class BaseStationGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("RadioBlazers - Base Station")
        self.root.geometry("800x600")

        # --- ZMQ setup ---
        self.context = zmq.Context.instance()

        # Outgoing messages -> GNU Radio
        self.push_sock = self.context.socket(zmq.PUSH)
        self.push_sock.connect("tcp://localhost:5555")

        # Feedback from GNU Radio (tx success/failure)
        self.feedback_pull = self.context.socket(zmq.PULL)
        self.feedback_pull.connect("tcp://localhost:5557")

        # Incoming chat messages from GNU Radio
        self.incoming_pull = self.context.socket(zmq.PULL)
        self.incoming_pull.connect("tcp://localhost:5556")

        # --- Users / addresses ---
        self.users = {
            "User 1": "0x0001",
            "User 2": "0x0002",
            "User 3": "0x0003",
        }
        self.addr_to_user = {v: k for k, v in self.users.items()}

        # --- Outgoing processing queue (PriorityQueue supports “front/back” via priority) ---
        # item: (priority:int, seq:int, message_dict)
        self.outgoing_queue = queue.PriorityQueue()
        self._seq = 0  # FIFO tie-breaker for same priority

        # message_id -> message_dict (track & update status)
        self.messages = {}

        self.message_ui = {}  # message_id -> {"user": str, "status_tag": str}

        # per-user chat widgets
        self.chat_widgets = {}

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

        title = ttk.Label(main_frame, text="Base Station", font=('Arial', 16, 'bold'))
        title.grid(row=0, column=0, columnspan=4, pady=(0,10), sticky="w")

        compose = ttk.LabelFrame(main_frame, text="Compose Message", padding=10)
        compose.grid(row=1, column=0, columnspan=4, sticky="ew")
        for c in range(4):
            compose.columnconfigure(c, weight=1 if c in (1,) else 0)

        ttk.Label(compose, text="Recipient:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.recipient_var = tk.StringVar(value="User 1")
        recipient_combo = ttk.Combobox(
            compose, textvariable=self.recipient_var,
            values=list(self.users.keys()), width=15, state="readonly"
        )
        recipient_combo.grid(row=0, column=1, sticky="w", padx=5, pady=5)

        ttk.Label(compose, text="Message:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.message_entry = ttk.Entry(compose, width=50)
        self.message_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=5)

        self.send_button = ttk.Button(compose, text="Send Message", command=self.send_message)
        self.send_button.grid(row=1, column=2, padx=5, pady=5, sticky="e")

        self.send_button_urgent = ttk.Button(compose, text="Send Urgent Message", command=self.send_priority)
        self.send_button_urgent.grid(row=1, column=3, padx=5, pady=5, sticky="e")

        # Notebook with user chats
        self.notebook = ttk.Notebook(self.root)
        self.notebook.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0,10))

        for uname in self.users.keys():
            frame = ttk.Frame(self.notebook, padding=10)
            frame.rowconfigure(0, weight=1)
            frame.columnconfigure(0, weight=1)
            self.notebook.add(frame, text=uname)

            # WhatsApp-style-ish chat: Text widget with left/right tags and a scrollbar
            text = tk.Text(frame, wrap="word", state="disabled", spacing1=4, spacing3=6)
            vsb = ttk.Scrollbar(frame, orient="vertical", command=text.yview)
            text.configure(yscrollcommand=vsb.set)
            text.grid(row=0, column=0, sticky="nsew")
            vsb.grid(row=0, column=1, sticky="ns")

            # Tags: left for received, right for sent, and small-status
            text.tag_configure("recv", justify="left", lmargin1=6, lmargin2=12, rmargin=60)
            text.tag_configure("sent", justify="right", lmargin1=60, lmargin2=60, rmargin=6)
            text.tag_configure("status", font=("Arial", 8, "italic"))

            self.chat_widgets[uname] = text

    # --- UI helpers ---
    def _append_sent_message(self, user_name: str, message_id: str, msg_text: str, status: str):
        """Insert a right-aligned bubble + a status line with a unique tag for later in-place updates."""
        def _do():
            text = self.chat_widgets[user_name]
            text.configure(state="normal")

            # Insert message (right-aligned)
            text.insert("end", msg_text + "\n", "sent")

            # Insert status with a unique tag we can later replace in-place
            status_tag = f"status_{message_id}"
            start_index = text.index("end")
            status_str = f"[{status}]\n\n"
            text.insert("end", status_str, ("status", "sent", status_tag))
            end_index = text.index("end")

            # Save for later updates
            self.message_ui[message_id] = {"user": user_name, "status_tag": status_tag}

            text.see("end")
            text.configure(state="disabled")
        self.root.after(0, _do)

    def _append_received_message(self, user_name: str, msg_text: str):
        def _do():
            text = self.chat_widgets[user_name]
            text.configure(state="normal")
            text.insert("end", msg_text + "\n\n", "recv")
            text.see("end")
            text.configure(state="disabled")
        self.root.after(0, _do)


    def _set_status(self, message_id: str, new_status: str):
        """Replace the existing status text [old] with [new_status] using the stored tag."""
        ui = self.message_ui.get(message_id)
        msg = self.messages.get(message_id)
        if not ui or not msg:
            return

        user_name = ui["user"]
        status_tag = ui["status_tag"]

        def _do():
            text = self.chat_widgets[user_name]
            ranges = text.tag_ranges(status_tag)
            if len(ranges) == 2:
                start, end = ranges
                text.configure(state="normal")
                # Replace the old "[...]\n\n" with the new one, and re-apply the tag to the new range
                text.delete(start, end)
                text.insert(start, f"[{new_status}]\n\n", ("status", "sent", status_tag))
                text.configure(state="disabled")
                text.see("end")
        self.root.after(0, _do)



    # --- Public (button) actions ---
    def send_message(self):
        self._enqueue_message(priority=1)  # normal

    def send_priority(self):
        self._enqueue_message(priority=0)  # urgent

    def _enqueue_message(self, priority: int):
        user = self.recipient_var.get()
        text_val = self.message_entry.get().strip()
        if not text_val:
            return

        message_id = str(uuid.uuid4())
        msg = {
            "message_id": message_id,
            "to_user": user,
            "to_addr": self.users[user],
            "text": text_val,
            "status": STATUS_QUEUED,
            "ts": time.time()
        }
        self.messages[message_id] = msg

        self._seq += 1
        self.outgoing_queue.put((priority, self._seq, msg))

        # Insert bubble + initial status [queued]
        self._append_sent_message(user, message_id, text_val, STATUS_QUEUED)

        self.message_entry.delete(0, "end")


    # --- Threads ---
    def start_threads(self):
        # Worker thread for sending queue
        self.worker_thread = threading.Thread(target=self._process_queue_loop, daemon=True)
        self.worker_thread.start()

        # Feedback listener (re-used by worker with blocking wait, but also buffers)
        self.feedback_buffer = {}  # message_id -> {"ok":bool}
        self.feedback_lock = threading.Lock()
        self.feedback_thread = threading.Thread(target=self._feedback_listener_loop, daemon=True)
        self.feedback_thread.start()

        # Incoming chat listener
        self.incoming_thread = threading.Thread(target=self._incoming_listener_loop, daemon=True)
        self.incoming_thread.start()

    
    def _process_queue_loop(self):
        """Send next message and wait indefinitely for its feedback before proceeding."""
        while not self._stop.is_set():
            try:
                priority, _, msg = self.outgoing_queue.get(timeout=0.2)
            except queue.Empty:
                continue

            message_id = msg["message_id"]
            user = msg["to_user"]

            # mark sending
            msg["status"] = STATUS_SENDING
            self._set_status(message_id, STATUS_SENDING)

            # send over ZMQ PUSH
            payload = {
                "type": "tx",
                "message_id": message_id,
                "to_addr": msg["to_addr"],
                "text": msg["text"]
            }
            try:
                self.push_sock.send_json(payload, flags=0)
            except Exception:
                msg["status"] = STATUS_FAILED
                self._set_status(message_id, STATUS_FAILED)
                continue

            # WAIT INDEFINITELY for feedback (sent/failed). If none, remain 'sending'.
            ok = self._wait_for_feedback(message_id)  # blocks until feedback or stop
            if ok is None:
                # stopping; leave as-is
                continue
            elif ok is True:
                msg["status"] = STATUS_SENT
                self._set_status(message_id, STATUS_SENT)
            else:
                msg["status"] = STATUS_FAILED
                self._set_status(message_id, STATUS_FAILED)

    def _wait_for_feedback(self, message_id: str) -> bool | None:
        """Block in worker thread until feedback for message_id arrives.
        Returns True/False on feedback, or None if we're stopping.
        """
        while not self._stop.is_set():
            with self.feedback_lock:
                data = self.feedback_buffer.pop(message_id, None)
            if data is not None:
                return bool(data["ok"])
            time.sleep(0.05)
        return None

    

    def _feedback_listener_loop(self):
        """Continuously read feedback and stash it for the worker."""
        poller = zmq.Poller()
        poller.register(self.feedback_pull, zmq.POLLIN)
        while not self._stop.is_set():
            socks = dict(poller.poll(timeout=200))  # ms
            if self.feedback_pull in socks and socks[self.feedback_pull] == zmq.POLLIN:
                try:
                    msg = self.feedback_pull.recv_json(flags=zmq.NOBLOCK)
                except zmq.Again:
                    continue
                # Expect: {"type":"tx_ack","message_id":"...","ok":true/false}
                if msg.get("type") == "tx_ack" and "message_id" in msg:
                    with self.feedback_lock:
                        self.feedback_buffer[msg["message_id"]] = {"ok": bool(msg.get("ok"))}

    def _incoming_listener_loop(self):
        """Continuously read incoming chat and post to the correct tab."""
        poller = zmq.Poller()
        poller.register(self.incoming_pull, zmq.POLLIN)
        while not self._stop.is_set():
            socks = dict(poller.poll(timeout=200))  # ms
            if self.incoming_pull in socks and socks[self.incoming_pull] == zmq.POLLIN:
                try:
                    msg = self.incoming_pull.recv_json(flags=zmq.NOBLOCK)
                except zmq.Again:
                    continue
                # Expect: {"type":"rx","from_addr":"0x0002","text":"hello"}
                if msg.get("type") == "rx":
                    from_addr = msg.get("from_addr")
                    text = msg.get("text", "")
                    user = self.addr_to_user.get(from_addr, None)
                    if user:
                        self._append_received_message(user, text)

    def on_close(self):
        self._stop.set()
        try:
            # Close sockets
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
    app = BaseStationGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
