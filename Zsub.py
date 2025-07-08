import zenoh

def listener(sample):
     print(f"Received: {bytes(sample.payload).decode('utf-8')}")

def main():
    config = zenoh.Config()
    session = zenoh.open(config)

    topics = [
        "global/IFF",
        "global/COMMAND",
        "camera/*"
    ]

    for topic in topics:
        session.declare_subscriber(topic, listener)

    print("Subscribed. Waiting for messages...")
    while True:
        pass  # Keep the app alive

if __name__ == "__main__":
    main()
