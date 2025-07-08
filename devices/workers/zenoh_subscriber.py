import zenoh
import time

class Zenoh_Subscriber():
    def __init__(self, device):
        self.device = device

        topics = ["global/IFF",
                  f"global/COMMAND/{self.device.device_id}"]

        config = zenoh.Config()
        session = zenoh.open(config)

        self.subscribers = []
        for topic in topics:
            sub = session.declare_subscriber(topic, listener)
            self.subscribers.append(sub)

    def stop(self):
        """Undeclare the subscriber and clean up."""
        for sub in self.subscribers:
            sub.undeclare()
            print(f"Unsubscribed from '{sub.key_expr}'")

    def close(self):
        """Close the Zenoh session."""
        self.session.close()
        print("Zenoh session closed.")

    def listener(self, sample):
        payload = bytes(sample.payload).decode("utf-8")
        print(f"Received on '{sample.key_expr}': {payload}")

class Command:
    def __init__(self, auth, target, verb, content):
        self.auth = auth
        self.target = target
        self.verb = verb
        self.content = content

    


