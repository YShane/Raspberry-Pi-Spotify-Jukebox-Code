#!/usr/bin/python

#Code to run Dotstar LEDs on your Raspberry Pi running Volumio with physical buttons and a webserver
#Lots of code chunks taken from http://blog.shinium.eu/2015/06/dotstar-leds-with-raspberry-pi-python.html
#Many thanks to him for posting his code for others to use.

import RPi.GPIO as GPIO
import time
import subprocess
import sys, os
import telnetlib
import sys,os
import time
import subprocess

from dotstar import Adafruit_DotStar	
from colour import Color

from random import randint,choice,uniform

from rotary_class import RotaryEncoder

from threading import Thread

#switch and single LED
#switch = 25
#light = 18

powerbutton = 4

#rotary encoder declarations

PIN_A = 12
PIN_B = 21
BUTTON = 20

#LED Strip declarations
datapin = 22
clockpin = 23
numpixels = 32

strip = Adafruit_DotStar(numpixels, datapin, clockpin)

strip.begin()

#volume indicators
global volume
volume = 3.0
disp = 1.0

#color = 0xFF0000

#GPIO setup
prev_input = 0
switch1 = 16
switch2 = 5
switch3 = 26
switch4 = 13

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
#GPIO.setup(light,GPIO.OUT)
GPIO.setup(switch1, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(switch2, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(switch3, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(switch4, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(powerbutton, GPIO.IN, pull_up_down=GPIO.PUD_UP)

#misc variable definitions
bState = {switch1:0, switch2:0, switch3:0, switch4:0, powerbutton:0}
thingHappening = "nothing"

switchstates = [99,99,99,99]
switchcolours = {0:0xFFFF00,1:0xFFFF00,2:0xFFFF00,3:0xFFFF00}

volstates = [99,99,99,99,99,99,99,99,99,99]
volcolor = 0xFFFFFF

phasing = 1
prevphasing = 1

grouplen = 5



#define pulse

def phase(c1,c2,interval,px=None):

	c1 = Color(c1)
	c2 = Color(c2)
	grad = list(c1.range_to(c2,128))

	for c in grad:
		rbg = c.rgb
		red = int(round(255* rbg[0]))
		blue = int(round(255 * rbg[1]))
		green = int(round(255 * rbg[2]))
		if px != None:
			strip.setPixelColor(px,red,blue,green)
		else:
			for n in range(numpixels):
				if n in volstates:
					for i,v in enumerate(volstates):
						if v == n:
							strip.setPixelColor(n,volcolor)
				elif n in switchstates:
					for i,v in enumerate(switchstates):
						if v == n:
							strip.setPixelColor(n,switchcolours[i])
				else:
					strip.setPixelColor(n,red,blue,green)
		strip.show()
		time.sleep(interval)


def brighten(b1,b2,interval):
	grad = range(min(b1,b2),max(b1,b2))
	step = float(interval) / abs(b1-b2)
	if b2 > b1:
		for c in grad:
			strip.setBrightness(c)
			time.sleep(step)
	else:
		grad.reverse()
		for c in grad:
			strip.setBrightness(c)
			time.sleep(step)
		

def phaseStrip(b):
	strip.setBrightness(b)
	phase("#FF0000","#00FF00",0.02)
	phase("#00FF00","#0000FF",0.02)
	phase("#0000FF","#FF0000",0.02)
	time.sleep(0.0001)

def hsv_to_rgb(h,s,v):
	if s == 0.0: v*=255; return (v,v,v)
	i = int(h*6.)
	f = (h*6.)-i; p,q,t = int(255*(v*(1.-s))),int(255*(v*(1.-s*f))), int(255*(v*(1.-s*(1.-f)))); v*=255; i%=6
	if i == 0: return [v,t,p]
	if i == 1: return [q,v,p]
	if i == 2: return [p,v,t]
	if i == 3: return [p,q,v]
	if i == 4: return [t,p,v]
	if i == 5: return [v,p,q]


def randColour():
	h = uniform(0,100)/100
	s = uniform(70,100)/100
	v = uniform(70,100)/100
	rb = hsv_to_rgb(h,s,v)
	r = int(round(rb[0]))
	g = int(round(rb[1]))
	b = int(round(rb[2]))
	col = (r,g,b)
	
	return col


def flashStrip(numflash,int1, int2):
	global bigrainbow
	for r in range(0,numflash):
		rcol = randColour()
		for n in range (numpixels):
			strip.setPixelColor(n,rcol[0],rcol[1],rcol[2])
			print rcol
		strip.show()
		time.sleep(int1)
		for n in range(numpixels):
			strip.setPixelColor(n,0)
		strip.show()
		time.sleep(int2)
	time.sleep(0.05)

def colourWave(num):
	for r in range(num):
		head = 0
		tail = 0 - grouplen
		for n in range(numpixels + grouplen):
			c = randColour()
			strip.setPixelColor(n,c[0],c[1],c[2])
			strip.show()
			time.sleep(0.005)
			strip.setPixelColor(tail,0)
			time.sleep(0.005)
			head += 1
			tail += 1
		
		head = numpixels
		tail = numpixels + grouplen
		
		for n in range(numpixels + grouplen + 2):
			c = randColour()
			strip.setPixelColor(head,c[0],c[1],c[2])
			strip.show()
			time.sleep(0.005)
			strip.setPixelColor(tail,0)
			time.sleep(0.005)
			head -= 1
			tail -= 1



#define turnoff for break

def turnOff(intv):
	c1 = "#" + hex(strip.getPixelColor(0)).ljust(8,"0").replace("0x","")
	phase(c1,"#000000",intv)


#define rotary encoder for volume  \_(0_0)_/
voladjust = 0

def volumeDisp(vol):
	global volstates
	global voladjust
	disp = vol / 10
	disp = round(disp)
	disp = int(disp)
#	print disp
	for i in range(0,disp):
		volstates[i] = 19-i
	for i in range(disp,10):
		volstates[i] = 99
	voladjust = 1
	return
	

def Timer():
	global voladjust
	global volstates
	current = 0
	while True:
		while voladjust == 1:
			current += 1
			if current < 250:
				time.sleep(.01)
			else:
				voladjust = 0
				current = 0		
				volstates = [99,99,99,99,99,99,99,99,99,99]	


def switch_event(event):
	global phasing
	global volume
	phasing = 0
	if event == RotaryEncoder.CLOCKWISE:
		subprocess.call(['mpc', 'volume', '+2'])
		if volume < 100:
			volume = volume + 2
		volumeDisp(volume)
		time.sleep(.1)
	elif event == RotaryEncoder.ANTICLOCKWISE:
		subprocess.call(['mpc', 'volume', '-2'])
		if volume >0:
			volume = volume - 2
		volumeDisp(volume)
		time.sleep(.1)
#	elif event == RotaryEncoder.BUTTONDOWN:
#		tn.write("toggle\n")
#		print "Toggle"
#		strip.setBrightness(100)
#		brighten(100,50,1)
#		colourWave()
	phasing = 1
	return

#define the switch

rswitch = RotaryEncoder(PIN_A,PIN_B,BUTTON,switch_event)


def buttonHandler(pin):
	time.sleep(.05)
	
	if GPIO.input(pin) == 1:
		if bState[pin] == 1:
			bState[pin] = 0
			switchOff(pin)
	else:
		if bState[pin] == 0:
			bState[pin] = 1
			switchOn(pin)

def switchOn(pin):
	global thingHappening
	global switchstates
	global prevThing

	if pin == switch1:
		switchstates[0] = 22
		tn.write("add 2\n")
		tn.write("play\n")
		print "Added Playlist 1"
#		strip.setPixelColor(4,0,255,0)
#		strip.show()

	if pin == switch2:
		switchstates[1] =19
		tn.write("add 3\n")
		tn.write("play\n")
		print "Added Playlist 2"
#		strip.setPixelColor(8,0,255,0)
#		strip.show()
	
	if pin == switch3:
		switchstates[2] = 12
		tn.write("add 4\n")
		tn.write("play\n")
		print "Added Playlist 3"

	if pin == switch4:
		switchstates[3] = 9
		tn.write("add 6\n")
		tn.write("play\n")
		print "Added Playlist 4"
		

def switchOff(pin):
	global switchstates

	if pin == switch1:
		switchstates[0] = 99
	if pin == switch2:
		switchstates[1] = 99
	if pin == switch3:
		switchstates[2] = 99
	if pin == switch4:
		switchstates[3] = 99
	tn.write("qclear\n")
	print "Cleared Queue"

def powerOff():
	print "Begin Shutdown"
	switchstates = [99,99,99,99]
	turnOff(.01)
	strip.setBrightness(0)
	strip.close()
	GPIO.cleanup()
	tn.close()
	print "Shutting Down"
	os.system('sudo shutdown -h now')


#Spotify Monitor
spotifystate = "not"
results = (-1, "None", "text")

def spotifyMonitor():
	global spotifystate	
	while True:
		results = (-1, "None", "text")
		time.sleep(.1)
		tn.write("status\n")
		results = tn.expect(["playing"],.1)
#		print results[0]
	
		if results[0] > -1:
			spotifystate = "playing"
		else:
			spotifystate = "not"

#telnet setup
HOST = "localhost"

tn = telnetlib.Telnet()

#in_state = GPIO.input(25)

#print "%s" % in_state

tn.open(HOST,6602,5)

tn.read_until("spop 0.0.1")
time.sleep(.1)
##                                        NEED TO FIX THE SHUFFLE ON STARTUP - THIS IS SLOPPY AND ONLY WORKS WHEN YOU FIRST BOOT IT UP. ALTHOUGH, IN THE REAL WORLD, THAT MIGHT BE FINE
tn.write("shuffle\n")
time.sleep(.1)



def main():
	global phasing
	global switchstates
	GPIO.add_event_detect(switch1,GPIO.BOTH, callback=buttonHandler, bouncetime=500)
	GPIO.add_event_detect(switch2,GPIO.BOTH, callback=buttonHandler, bouncetime=500)
	GPIO.add_event_detect(switch3,GPIO.BOTH, callback=buttonHandler, bouncetime=500)
	GPIO.add_event_detect(switch4,GPIO.BOTH, callback=buttonHandler, bouncetime=500)
	GPIO.add_event_detect(powerbutton, GPIO.FALLING, bouncetime=500)
	
	colourWave(3)

	while True:
		try:
			time.sleep(.2)
			if spotifystate == "playing":
				phaseStrip(30)
#				time.sleep(.01)
			if spotifystate == "not":
				c1 = "#" + hex(strip.getPixelColor(1)).ljust(8,"0").replace("0x","")
				if c1 != "#000000":
					turnOff(.005)
					time.sleep(.01)
				strip.setPixelColor(30,0,0,15)
				strip.show()
			if GPIO.event_detected(powerbutton):
				print "Shutdown?"
				colourWave(5)
#				time.sleep(3)
				if GPIO.input(powerbutton):
					print "Shutdown Aborted"
				else:
					powerOff()
					break


		except KeyboardInterrupt:
			switchstates = [99,99,99,99]
			turnOff(.005)
			strip.setBrightness(0)
			strip.close()
			GPIO.cleanup()
			tn.close()
			print "Done"
			break
	
	GPIO.cleanup()


if True:

	smon = Thread(target = spotifyMonitor)
	smon.daemon = True
	smon.start()
	
	tmr = Thread(target = Timer)
	tmr.daemon = True
	tmr.start()

	main()
