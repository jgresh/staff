import time
import board
import digitalio
import busio
import adafruit_mpr121
import adafruit_midi
import usb_midi
import rotaryio
from adafruit_midi.note_off import NoteOff
from adafruit_midi.note_on import NoteOn
from time import sleep
import asyncio

DIATONIC = [2, 2, 1, 2, 2, 2, 1]
CIRCLE5 = ['C', 'G', 'D', 'A', 'E', 'B', 'F#', 'C#', 'Ab', 'Eb', 'Bb', 'F']

class Key:
    def __init__(self, name):
        self.name = name
        self.rotation = 3 * self.count()
    
    def count(self):
        mapping = {'C': 0, 'G': 1, 'D': 2, 'A': 3, 'E': 4, 'B': 5, 'F#': 6, 'C#': 7}
        mapping.update({'F': -1, 'Bb': -2, 'Eb': -3, 'Ab': -4, 'Db': -5, 'Gb': -6, 'Cb': -7})
        return mapping[self.name]
    
    def c_is_sharp(self):
        self.count() > 1
    
class State:
    def __init__(self, keyname):
        self.notesOn = [False for i in range(12)]
        self.base = 60 # middle c - 60, low e - 40
        self.key = Key(keyname)
        if self.key.c_is_sharp():
            self.base += 1
        self.scale = rotate(DIATONIC, self.key.rotation)
        
SDA = board.GP8
SCL = board.GP9

UP = digitalio.DigitalInOut(board.GP26)
UP.switch_to_input(pull=digitalio.Pull.DOWN)
DOWN = digitalio.DigitalInOut(board.GP27)
DOWN.switch_to_input(pull=digitalio.Pull.DOWN)

i2c = busio.I2C(SCL, SDA)
if(i2c.try_lock()):
    print("i2c.scan(): " + str(i2c.scan()))
    i2c.unlock()
print("i2c ready")

mpr121 = adafruit_mpr121.MPR121(i2c)

usb_midi = adafruit_midi.MIDI(
    midi_out=usb_midi.ports[1],
    out_channel=0
    )

encoder = rotaryio.IncrementalEncoder(board.GP2, board.GP3, divisor=8)


def rotate(seq, n):
    n = n % len(seq)
    return seq[n:] + seq[:n]

def getNote(x, state):
    # reverse input pins
    #x = 12 - x
    
    accidental = 0
    if UP.value:
        accidental = 1

    if DOWN.value:
        accidental = -1
    
    ret = state.base
    for i in range(x):
        ret += state.scale[i % len(DIATONIC)]
    
    return ret + accidental
        
async def midiNoteOn(x):
    usb_midi.send(NoteOn(x, 127))
    
async def midiNoteOff(x):
    usb_midi.send(NoteOff(x, 127))
                
async def main():
    state = State('C')
    last_position = encoder.position % 12
    while True:
        for i in range(12):
            if mpr121[i].value:
                if not state.notesOn[i]:
                    note_task = asyncio.create_task(midiNoteOn(getNote(i, state)))
                    state.notesOn[i] = True
                    print("{} on".format(i))
            elif state.notesOn[i]:
                state.notesOn[i] = False
                asyncio.create_task(midiNoteOff(getNote(i, state)))
                print("{} off".format(i))
             
        if last_position != encoder.position % 12:
            state = State(CIRCLE5[last_position])
            print(CIRCLE5[last_position])
            last_position = encoder.position % 12
            
        await asyncio.sleep(0)
    
asyncio.run(main())

