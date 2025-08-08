import rtmidi
from rtmidi.midiutil import open_midiinput
import time
import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                           QPushButton, QLabel, QGridLayout, QLineEdit, QComboBox)
import keyboard
import json

from MidiKey import MidiKey
from MidiKey import MidiKeyEventHandler


class KeyMapperWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Keyboard Mapper")
        self.setGeometry(100, 100, 400, 300)

        ################
        ###########      MIDI
        ################
        
        # variables
        self.mapping_active = False
        self.midi_in = None
        self.port_name = None
        self.port_number = 0

        # MIDI dropdown menu
        self.midi_device_dropdown = QComboBox(self)
        self.midi_device_dropdown.move(50, 30)
        self.ports = self.list_midi_ports()
        # Add items to the dropdown
        for port_number, port_name in self.ports.items():
            self.midi_device_dropdown.addItem(port_name, port_number)
        if len(self.ports) == 0:
            self.midi_device_dropdown.addItem("No MIDI device found", 0)

        # MIDI refresh button
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.midi_device_refresh)

        # MIDI select dive layout
        self.select_midi_device_grid = QGridLayout()
        self.select_midi_device_grid.addWidget(self.midi_device_dropdown, 0, 0)
        self.select_midi_device_grid.addWidget(self.refresh_button, 0, 1)


        # Dictionary for key mappings
        self.key_pairs = {}
        self.input_pairs = [] 
        
        # Main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # Grid Layout for mapping entries
        self.grid_layout = QGridLayout()
        
        # Labels
        self.grid_layout.addWidget(QLabel("MIDI Key"), 0, 0)
        self.grid_layout.addWidget(QLabel("Keyboard Key"), 0, 1)
        
        # Create initial mapping pair
        self.add_mapping_row()

        # Connect the selection change event
        self.midi_device_dropdown.currentIndexChanged.connect(self.select_midi_device)
        
        # Buttons
        self.add_button = QPushButton("Add New Mapping")
        self.add_button.clicked.connect(self.add_mapping_row)
        
        self.save_button = QPushButton("Save Mapping")
        self.save_button.clicked.connect(self.save_mappings)
        
        self.start_button = QPushButton("Activate Mapping")
        self.start_button.clicked.connect(self.start_mapping)
        
        # build layout
        layout.addLayout(self.select_midi_device_grid)
        layout.addLayout(self.grid_layout)
        layout.addWidget(self.add_button)
        layout.addWidget(self.save_button)
        layout.addWidget(self.start_button)
        
        # status labels
        self.status_label = QLabel("")
        layout.addWidget(self.status_label)
        self.test_label = QLabel("")
        layout.addWidget(self.test_label)

        # load saved mappings
        self.load_mappings()


    def midi_device_refresh(self):
        self.midi_device_dropdown.clear()
        self.ports = self.list_midi_ports()
        # Add items to the dropdown
        for port_number, port_name in self.ports.items():
            self.midi_device_dropdown.addItem(port_name, port_number)
        if len(self.ports) == 0:
            self.midi_device_dropdown.addItem("No MIDI device found", 0)

    def select_midi_device(self, index):
        self.port_number = self.midi_device_dropdown.currentData()
        self.status_label.setText(f"Selected: {self.midi_device_dropdown.currentText()}")

    def add_mapping_row(self):
        row = len(self.input_pairs) + 1
        
        # input fields
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
        
        key = self.read_midi_input(self.port_number)
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
            if self.activate_midi_translation(self.port_number):
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
        # fill key pairs
        self.key_pairs = {}
        for midi_key_Q, keyboard_key_Q in self.input_pairs:
            self.key_pairs[midi_key_Q.text()] = keyboard_key_Q.text()
        print("key pairs filled: " + str(self.key_pairs))

        # Open the MIDI input port
        self.midi_in, self.port_name = open_midiinput(port = port_number)
        print(f"Listening on [ {self.port_name} ] ...")
        self.midi_in.set_callback(MidiKeyEventHandler(self.key_pairs))
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


    def list_midi_ports(self) -> dict[int, str]:
        try:
            # List all available MIDI input ports
            midi_in = rtmidi.MidiIn() # type: ignore
            ports = midi_in.get_ports()
            ports_list : dict[int, str] = {}
            print("Available MIDI input ports:")
            for i, port in enumerate(ports):
                print(f"[{i}] {port}")
                ports_list.update({i: port})
            return ports_list
        except:
            print("No MIDI device found.")
            self.status_label.setText("No MIDI device found.")
            return {0: "no MIDI device available"}


def main():
    app = QApplication(sys.argv)
    window = KeyMapperWindow()
    window.show()
    sys.exit(app.exec())
    window.close_midi_in()

if __name__ == '__main__':
    main()
