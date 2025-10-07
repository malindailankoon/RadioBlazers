# send_incoming.py
import zmq, json

PORT = 5556  # matches GUI's incoming PULL connect("tcp://localhost:5556")

# helpful defaults — change as needed
KNOWN_USERS = {
    "User 1": "0x0001",
    "User 2": "0x0002",
    "User 3": "0x0003",
}

def main():
    ctx = zmq.Context.instance()
    push = ctx.socket(zmq.PUSH)
    push.linger = 0
    push.bind(f"tcp://*:{PORT}")
    print(f"[send_incoming] Ready on tcp://*:{PORT}")
    print("Type messages that should appear as RECEIVED in the GUI. Ctrl+C to quit.\n")
    print("Known addrs:", KNOWN_USERS, "\n")

    try:
        while True:
            from_addr = input("from_addr (e.g., 0x0002): ").strip() or KNOWN_USERS["User 2"]
            text = input("text: ").strip()
            if not text:
                continue

            payload = {"type": "rx", "from_addr": from_addr, "text": text}
            push.send_json(payload)
            print("Sent incoming:", payload, "\n")
    except KeyboardInterrupt:
        pass
    finally:
        push.close(0)
        ctx.term()

if __name__ == "__main__":
    main()
