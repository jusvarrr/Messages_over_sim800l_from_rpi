#! /usr/bin/env python

import serial
import argparse
import time
# Define the parser
parser = argparse.ArgumentParser(description='Short sample app')
parser.add_argument('--room-nr', action="store", dest='roomnr', default=0)
parser.add_argument('--soundlvl', action="store", dest='soundlvl', default=0)
parser.add_argument('--phone-nr', action="store", dest='phone', default=0)
args = parser.parse_args()

port = serial.Serial("/dev/ttyAMA0",
    baudrate=115200,
    bytesize=8,
    parity='N',
    timeout=1,
    stopbits=1,
    rtscts=False,
    dsrdtr=False
)

try:
    response=''
    print(args.roomnr)
    print(args.phone)

    port.write(b"AT+CREG?\r\n")
    time.sleep(0.1)
    port.write(b"AT+CMGF=1\r\n")
    time.sleep(0.1)
    port.write(f'AT+CMGS="{args.phone}"\r\n'.encode())
    port.write(f'High sound level detected at {args.roomnr}!\r\n'.encode())
    time.sleep(0.1)
    port.write(bytes([26]))
    time.sleep(1)
finally:
    print("Something went wrong!")
port.close()
