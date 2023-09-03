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

octave = 1
keys_pressed = {}

async def midiNoteOn(x):
    if x not in keys_pressed:
        usb_midi.send(NoteOn(x, 127))
        keys_pressed[x] = True
        await asyncio.sleep(1)
        usb_midi.send(NoteOff(x, 127))
        del(keys_pressed[x])
    
async def midiNoteOff(x):
    usb_midi.send(NoteOff(x, 127))
                
async def main():
    # Loop forever testing each input and printing when they're touched.
    while True:
        # Loop through all 12 inputs (0-11).
        for i in range(12):
            # Call is_touched and pass it then number of the input.  If it's touched
            # it will return True, otherwise it will return False.
            if mpr121[i].value:
                print("Input {} touched!".format(i))
                note_task = asyncio.create_task(midiNoteOn(65 + i))
         
        await asyncio.sleep(0)
    
asyncio.run(main())