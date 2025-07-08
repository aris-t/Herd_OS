import random
import uuid

class Animal:
    def __init__(self, name = None):
        self.DB_ID = f"animal-{uuid.uuid4().hex[:6]}"
        self.ID = ""

        self.trails = {}

        

        if name is None:
            self.name = self.random_name()
        else:
            self.name = name

    def add_trail(self, trail_name, trail_data):
        self.trails[trail_name] = trail_data

    def random_name(self):
        adjectives = [
            "Fluffy", "Grumpy", "Bouncy", "Mopey", "Zesty", "Soggy", "Puffball",
            "Cranky", "Dopey", "Snuggly", "Lumpy", "Greasy", "Chonky", "Wonky", "Sleepy"
        ]

        nouns = [
            "Toes", "Wool", "Muffin", "Butt", "Socks", "Hoof", "Snout", "Biscuit",
            "Sprout", "Wobble", "Goblin", "Cabbage", "Whisker", "Nugget", "Flop"
        ]

        def generate_sheep_name():
            return f"{random.choice(adjectives)} {random.choice(nouns)}"
