import zenoh
import time
import random

def read_temp():
    return random.randint(15, 30)

if __name__ == "__main__":
    config = zenoh.Config()
    session = zenoh.open(config)

    pub = session.declare_publisher('iot/sensor/temp')

    try:
        while True:
            temp = read_temp()
            print(f"Publishing: {temp}")
            pub.put(str(temp))
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping publisher...")
        pub.undeclare()
        session.close()
