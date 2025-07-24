import zenoh
import time
import queue
import threading


class Zenoh_Local_Pub_Sub():
    def __init__(self, device):
        self.device = device

class Zenoh_Global_Pub_Sub():
    def __init__(self, device, publish_topics, subscribe_topics, local_only=False):
        self.device = device

        self.publish_topics = publish_topics
        self.subscribe_topics = subscribe_topics

        config = zenoh.Config()
        if local_only:
            # Configure for local-only communication
            config.insert_json5("scouting/multicast/enabled", "false")
            config.insert_json5("scouting/gossip/enabled", "false")
            config.insert_json5("listen/endpoints", '["tcp/127.0.0.1:0"]')  # Only listen on localhost
            config.insert_json5("connect/endpoints", "[]")  # Don't connect to remote endpoints
        
        zenoh_client = zenoh.open(config)

        self.publishers = []
        for topic in publish_topics:
            pub = zenoh_client.declare_publisher(topic)
            self.publishers.append(pub)
            print(f"Publisher declared for topic '{topic}'")

        self.subscribers = []
        for topic in subscribe_topics:
            sub = zenoh_client.declare_subscriber(topic, self.listener)
            self.subscribers.append(sub)


    def stop(self):
        """Undeclare the subscriber and clean up."""
        for sub in self.subscribers:
            sub.undeclare()
            print(f"Unsubscribed from '{sub.key_expr}'")

        for pub in self.publishers:
            pub.undeclare()
            print(f"Publisher undeclared for topic '{pub.key_expr}'")

    def close(self):
        """Close the Zenoh session."""
        self.session.close()
        print("Zenoh session closed.")

    def listener(self, sample):
        payload = bytes(sample.payload).decode("utf-8")
        print(f"Received on '{sample.key_expr}': {payload}")


class Zenoh_Subscriber():
    def __init__(self, device):
        self.device = device

        topics = ["global/IFF", f"global/COMMAND/{self.device.device_id}"]

        config = zenoh.Config()
        self.session = zenoh.open(config)  # Store as instance variable

        # Use dictionary for easier management
        self.subscribers = {}
        for topic in topics:
            try:
                sub = self.session.declare_subscriber(topic, self.listener)
                self.subscribers[topic] = sub
                print(f"Subscribed to '{topic}'")
            except Exception as e:
                print(f"Failed to subscribe to '{topic}': {e}")

        self.message_queue = queue.Queue()
        self.worker_thread = threading.Thread(target=self._process_messages, daemon=True)
        self.worker_thread.start()

    def _handle_command(self, sample):
        payload = bytes(sample.payload).decode("utf-8")
        self.message_queue.put(payload)

    def stop(self):
        """Undeclare subscribers and clean up."""
        for topic, sub in self.subscribers.items():
            sub.undeclare()
            print(f"Unsubscribed from '{topic}'")
        self.subscribers.clear()

    def close(self):
        """Close the Zenoh session."""
        self.session.close()
        print("Zenoh session closed.")


class Command:
    def __init__(self, auth, target, verb, content):
        self.auth = auth
        self.target = target
        self.verb = verb
        self.content = content

    


