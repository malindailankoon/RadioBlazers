# send_feedback.py
import zmq, json

PORT = 5557  # matches GUI's feedback PULL connect("tcp://localhost:5557")

def main():
    ctx = zmq.Context.instance()
    push = ctx.socket(zmq.PUSH)
    push.linger = 0
    push.bind(f"tcp://*:{PORT}")
    print(f"[send_feedback] Ready on tcp://*:{PORT}")
    print("Enter message_id and status to send ack to the GUI. Ctrl+C to quit.\n")

    try:
        while True:
            mid = input("message_id: ").strip()
            if not mid:
                continue
            ok_str = input("ok? (y/n): ").strip().lower()
            ok = ok_str in ("y", "yes", "true", "1")

            payload = {"type": "tx_ack", "message_id": mid, "ok": ok}
            push.send_json(payload)
            print("Sent:", payload, "\n")
    except KeyboardInterrupt:
        pass
    finally:
        push.close(0)
        ctx.term()

if __name__ == "__main__":
    main()
