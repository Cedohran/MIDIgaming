import keyboard


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
    
    
class MidiKeyEventHandler(object):
    def __init__(self, key_pairs):
        self.key_pairs = key_pairs

    def __call__(self, event, data=None):
            message, deltatime = event
            read_midi_key = MidiKey(message) # type: ignore
            read_midi_key_str = str(read_midi_key)

            if read_midi_key_str in self.key_pairs.keys():
                if read_midi_key.strength == 0:
                    keyboard.release(self.key_pairs[read_midi_key_str])
                    #print(f"releasing {self.key_pairs[read_midi_key_str]}")
                else:
                    keyboard.press(self.key_pairs[read_midi_key_str])                    
                    #print(f"pressing {self.key_pairs[read_midi_key_str]}")
