import time
import board
import busio
import adafruit_mpr121
import adafruit_midi
import usb_midi
from adafruit_midi.note_off import NoteOff
from adafruit_midi.note_on import NoteOn
from time import sleep
import asyncio

class State:
    def __init__(self):
        self.notesOn = [False for i in range(12)]
        
SDA = board.GP8
SCL = board.GP9
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

MAJOR = [2, 1, 2, 2, 1, 2, 2, 2, 1, 2, 2]
A440 = 69

def getNote(x):
    ret = A440
    for i in range(x):
        ret += MAJOR[i]
    
    return ret
        
async def midiNoteOn(x):
    usb_midi.send(NoteOn(getNote(x), 127))
    
async def midiNoteOff(x):
    usb_midi.send(NoteOff(getNote(x), 127))
                
async def main():
    state = State()
    
    while True:
        for i in range(12):
            if mpr121[i].value:
                if not state.notesOn[i]:
                    note_task = asyncio.create_task(midiNoteOn(i))
                    state.notesOn[i] = True
                    print("Input {} touched!".format(i))
            elif state.notesOn[i]:
                state.notesOn[i] = False
                asyncio.create_task(midiNoteOff(i))
                print("Turning off ".format(i))
                
        await asyncio.sleep(0)
    
asyncio.run(main())
