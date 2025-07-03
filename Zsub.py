import zenoh
import time

def listener(sample):
    payload = bytes(sample.payload).decode("utf-8")
    print(f"Received on '{sample.key_expr}': {payload}")

if __name__ == "__main__":
    config = zenoh.Config()
    session = zenoh.open(config)

    sub_1 = session.declare_subscriber('global/*', listener)
    sub_2 = session.declare_subscriber('camera/*', listener)

    try:
        print("Subscriber running. Press Ctrl+C to stop.")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")
        sub_1.undeclare()
        sub_2.undeclare()
        session.close()
