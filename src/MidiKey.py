class MidiKey():
    def __init__(self, message):
        if type(message) == str:
            message = message.split(',')
        self.message = message
        self.note = [message[0], message[1]]
        self.strength = message[2]
        
    def __str__(self) -> str:
        return ''.join(str(x)+"," for x in self.note)[:-1]

    def __hash__(self):
        # hash(custom_object)
        return hash(str(self))
    
    def __eq__(self, other):
        if type(other) != MidiKey:
            return False
        return hash(self) == hash(other)
    
    