import rtmidi
from rtmidi.midiutil import open_midiinput
import time
import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                           QPushButton, QLabel, QGridLayout, QLineEdit)
from PyQt6.QtCore import Qt
import keyboard
import json

from MidiKey import MidiKey
from threading import Thread


class KeyMapperWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Keyboard Mapper")
        self.setGeometry(100, 100, 400, 300)
        
        # Main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # Grid Layout for mapping entries
        self.grid_layout = QGridLayout()
        
        # Labels
        self.grid_layout.addWidget(QLabel("MIDI Key"), 0, 0)
        self.grid_layout.addWidget(QLabel("Keyboard Key"), 0, 1)
        
        # Dictionary for key mappings
        self.key_pairs = {}
        self.input_pairs = [] 
        
        # Create initial mapping pair
        self.add_mapping_row()
        
        # Buttons
        self.add_button = QPushButton("Add New Mapping")
        self.add_button.clicked.connect(self.add_mapping_row)
        
        self.save_button = QPushButton("Save Mapping")
        self.save_button.clicked.connect(self.save_mappings)
        
        self.start_button = QPushButton("Activate Mapping")
        self.start_button.clicked.connect(self.start_mapping)
        
        # Layout zusammenbauen
        layout.addLayout(self.grid_layout)
        layout.addWidget(self.add_button)
        layout.addWidget(self.save_button)
        layout.addWidget(self.start_button)
        
        # Status Label
        self.status_label = QLabel("")
        layout.addWidget(self.status_label)
        self.test_label = QLabel("")
        layout.addWidget(self.test_label)
        
        #MIDI
        self.midi_in = None
        self.port_name = None
        
        #Threading
        self.translation_thread = Thread(target = self.activate_midi_translation)
        self.stop_translation = False

        # Lade gespeicherte Mappings
        self.load_mappings()
        
        self.mapping_active = False


    def add_mapping_row(self):
        row = len(self.input_pairs) + 1
        
        # Erstelle Eingabefelder
        midi_key = QLineEdit()
        keyboard_key = QLineEdit()
        
        # Make input fields readonly and add click events
        midi_key.setReadOnly(True)
        keyboard_key.setReadOnly(True)
        
        midi_key.mousePressEvent = lambda e, field=midi_key: self.get_midi_key(field) # type: ignore
        keyboard_key.mousePressEvent = lambda e, field=keyboard_key: self.get_key_press(field) # type: ignore
        
        # Add fields to the grid
        self.grid_layout.addWidget(midi_key, row, 0)
        self.grid_layout.addWidget(keyboard_key, row, 1)
        
        # Store the references
        self.input_pairs.append((midi_key, keyboard_key))
        midi_key.text()


    def get_midi_key(self, field):
        self.status_label.setText("Press a MIDI key...")
        QApplication.processEvents()
        
        key = self.read_midi_input(0)
        if key:
            field.setText(str(key))
            self.status_label.setText("")


    def get_key_press(self, field):
        self.status_label.setText("Press a key...")
        QApplication.processEvents()
        
        event = keyboard.read_event(suppress=True)
        if event.event_type == keyboard.KEY_DOWN:
            field.setText(event.name)
            self.status_label.setText("")


    def save_mappings(self):
        mappings = {}
        for midi_key, keyboard_key in self.input_pairs:
            if midi_key.text() and keyboard_key.text():
                mappings[midi_key.text()] = keyboard_key.text()
        
        with open('key_mappings.json', 'w') as f:
            json.dump(mappings, f)
        
        self.status_label.setText("Mappings saved!")


    def load_mappings(self):
        try:
            with open('key_mappings.json', 'r') as f:
                mappings = json.load(f)
                
            for midi_key, keyboard_key in mappings.items():
                # Add new row
                self.add_mapping_row()
                # Set the values
                current_row = len(self.input_pairs) - 1
                self.input_pairs[current_row][0].setText(midi_key)
                self.input_pairs[current_row][1].setText(keyboard_key)
                
        except FileNotFoundError:
            pass


    def start_mapping(self):
        if not self.mapping_active:
            if self.activate_midi_translation():
                self.mapping_active = True
                self.status_label.setText("Mapping activated!")
                self.start_button.setText("Deactivate Mapping")
            else:
                self.status_label.setText("No MIDI device found.")
        else:
            # Deactivate all mappings
            self.deactivate_midi_translation()
            self.mapping_active = False
            self.status_label.setText("Mapping deactivated!")
            self.start_button.setText("Activate Mapping")


    def activate_midi_translation(self, port_number=None):
        # start midi 
        ports = self.list_midi_ports()
        if not ports:
            print("No MIDI input ports available!")
            return False
        # If no port specified, use the first available port
        if port_number is None:
            port_number = ports[0] # type: ignore
        
        # fill key pairs
        self.key_pairs = {}
        for midi_key_Q, keyboard_key_Q in self.input_pairs:
            self.key_pairs[midi_key_Q.text()] = keyboard_key_Q.text()
        print("key pairs filled: " + str(self.key_pairs))

        # Open the MIDI input port
        self.midi_in, self.port_name = open_midiinput(port = port_number)
        print(f"Listening on [ {self.port_name} ] ...")
        self.midi_in.set_callback(MidiInputHandler(self.key_pairs))
        print(f"Callback set for [ {self.port_name} ]")
        return True


    def deactivate_midi_translation(self):
        self.key_pairs = {}
        if self.midi_in:
            self.midi_in.close_port()  # type: ignore
            del self.midi_in
            print(f"Closed connection to [ {self.port_name} ]") 


    def read_midi_input(self, port_number=None) -> MidiKey | None:
        key = MidiKey("0,0,0")
        midi_in = None
        port_name = None
        try:
            ports = self.list_midi_ports()
            if not ports:
                print("No MIDI input ports available!")
            # If no port specified, use the first available port
            if port_number is None:
                port_number = ports[0] # type: ignore
            # Open the MIDI input port
            midi_in, port_name = open_midiinput(port = port_number)
            print(f"Listening on [ {port_name} ] ...")

            msg = None
            while not msg:
                msg = midi_in.get_message()
                if msg:
                    message, delta_time = msg
                    key = MidiKey(message)
                    print(f"MIDI message: {message}")
                time.sleep(0.05)  # Small sleep to prevent CPU overuse
        except:
            print("No MIDI device found.")
            self.status_label.setText("No MIDI device found.")
        finally:
            if midi_in:
                midi_in.close_port() # type: ignore
                del midi_in
                print(f"Closed connection to [ {port_name} ]")
                return key


    def list_midi_ports(self):
        try:
            # List all available MIDI input ports
            midi_in = rtmidi.MidiIn() # type: ignore
            ports = midi_in.get_ports()
            
            print("Available MIDI input ports:")
            for i, port in enumerate(ports):
                print(f"[{i}] {port}")
            return ports
        except:
            print("No MIDI device found.")
            self.status_label.setText("No MIDI device found.")



class MidiInputHandler(object):
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


def main():
    app = QApplication(sys.argv)
    window = KeyMapperWindow()
    window.show()
    sys.exit(app.exec())
    window.close_midi_in()

if __name__ == '__main__':
    main()
