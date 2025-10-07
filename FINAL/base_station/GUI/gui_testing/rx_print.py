# rx_print.py
import zmq, json, signal, sys

PORT = 5555  # matches GUI's PUSH connect("tcp://localhost:5555")

def main():
    ctx = zmq.Context.instance()
    pull = ctx.socket(zmq.PULL)
    pull.linger = 0
    pull.bind(f"tcp://*:{PORT}")
    print(f"[rx_print] Listening on tcp://*:{PORT} for GUI TX payloads...")
    print("Press Ctrl+C to quit.\n")

    try:
        while True:
            msg = pull.recv_json()
            print("RX from GUI:", json.dumps(msg, indent=2))
    except KeyboardInterrupt:
        pass
    finally:
        pull.close(0)
        ctx.term()

if __name__ == "__main__":
    main()