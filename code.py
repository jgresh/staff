import time
from collections import deque
import board
import digitalio
import busio
import adafruit_mpr121
import adafruit_midi
import usb_midi
from adafruit_midi.note_off import NoteOff
from adafruit_midi.note_on import NoteOn
from time import sleep
import asyncio

DIATONIC = [2, 2, 1, 2, 2, 2, 1]

class Key:
    def __init__(self, sharp=True, count=0):
        self.sharp = sharp
        self.count = count
        self.rotation = 3 * count
        if not sharp:
            self.rotation *= -1
        
    def c_is_sharp(self):
        self.sharp and self.count >= 2
            
class State:
    def __init__(self, sharp, count):
        self.notesOn = [False for i in range(12)]
        self.base = 60 # middle c - 60, low e - 40
        self.key = Key(sharp, count)
        if self.key.c_is_sharp():
            self.base += 1
        self.clef = rotate(DIATONIC, self.key.rotation)
        
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

def rotate(seq, n):
    n = n % len(seq)
    return seq[n:] + seq[:n]

def getNote(x, state):
    # reverse input pins
    x = 12 - x
    
    accidental = 0
    if UP.value:
        accidental = 1

    if DOWN.value:
        accidental = -1
    
    ret = state.base
    for i in range(x):
        ret += state.clef[i % len(DIATONIC)]
    
    return ret + accidental
        
async def midiNoteOn(x):
    usb_midi.send(NoteOn(x, 127))
    
async def midiNoteOff(x):
    usb_midi.send(NoteOff(x, 127))
                
async def main():
    state = State(False, 2)
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
                
        await asyncio.sleep(0)
    
asyncio.run(main())
