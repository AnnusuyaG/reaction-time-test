#reaction time test, press button to start, respond to red led
from board import GP10, GP11, GP12, GP20, GP21, GP28
from time import monotonic as now #timestamp
from digitalio import DigitalInOut, Direction
from neopixel import NeoPixel #for blinky control
import random # random interval for the alarm to go off
import usb_cdc  # for data transfer thru usb

"""buttonsbuttonsbuttons"""
class Button1: #GP20, reaction test button
    def __init__(self, pin): #constructor, to initialize
        self.input = DigitalInOut(pin) #button acts as an input and we're asking it to track itself
        self.input.direction = Direction.INPUT
        self.last_state = not self.input.value # what was the button doing since we last checked?
        self.last_time = now() #when did the state last change
        
    def print(self): #for debugging 
        out = str(self.last_state) + " " + str(self.last_time)
        print(out)
        
    def state (self): #reverse logic so that button press= true and not false like it is initially
        return not self.input.value 

    def poll(self):#to see if the state has changes, poll counts state change/ returns none if not
        #button= input -> output= boolean
        current_state = self.state()
        if not self.last_state and current_state: 
            self.last_state = current_state
            self.last_time = now()
            return "Pressed"
        if self.last_state and not current_state:
            self.last_state = current_state
            self.last_time = now()
            return "Released"
        return None

class Button2: #GP21, START/STOP
    def __init__(self, pin, interval): #debounce interval
        self.input = DigitalInOut(pin)
        self.input.direction = Direction.INPUT
        self.last_state = not self.input.value
        self.interval = interval
        self.last_time = now()
        self.mode = "Stopped"  #initial state = Stopped
        
    def state(self): #flip the logic for intuitive understanding, on = true now
        return not self.input.value
    
    def poll(self): 
        current_state = self.state()
        if (now() - self.last_time) > self.interval: #debounce time passed
            if not self.last_state and current_state:
                self.last_state = current_state
                self.last_time = now()
                return "Pressed"
            if self.last_state and not current_state:
                self.last_state = current_state
                self.last_time = now()
                return "Released"
        else:
            return None
        
    def toggle_state(self):  # Toggles between Start and Stop
        if self.mode == "Stopped":
            self.mode = "Started"
        else:
            self.mode = "Stopped"
        print(f"Button2 State Changed to: {self.mode}")
        #WE DID ALLLLLLL THAAAT to define the buttons and its attributes

"""observation"""  
class Obs:
    def __init__(self, start_time):
        self.start_time = start_time # Store the start time of the observation/ when it started
        self.duration = None # Placeholder for duration (to be recorded later)
        self.rt= None #rt= reaction time, none because placeholder for reaction time (to be recorded later)
        
    def record(self, duration, rt): #uses randomalarm (which is a class originally) as an OBJECT and uses it to keep track of time
        self.duration= duration # Store the duration of the alarm, how long does it last for
        self.rt = rt
        
    def serialize (self): #convert observation data to string for easy storage
        return str(self.start_time) + "," + str(self.duration) + "," + str(self.rt) #str is a typecast, using it to convert numbers to string so they can be written together, without str there would be an error

"""random blinky "alarm" to test reaction time"""
class RandomAlarm: 
    def __init__ (self, min_time, max_time):
        self.min_time = min_time #generate random duration
        self.max_time = max_time
        self.duration = None #placeholders
        self.start_time = None
        self.alarm_time = None
        
    def start(self): #start alarm w/ random duration
        self.duration = random.uniform(self.min_time, self.max_time)
        self.start_time = now()
        
    def reset(self):
        self.start() #read: reset= start again
        
    def alarm (self): #should the alarm should go off or na
        if now() - self.start_time >= self.duration:
            self.alarm_time = now()
            return True
        else:
            return False

"""transfer data thru usb"""
def write_to_usb(data):
    if usb_cdc.data:
        usb_cdc.data.write((data + "\n").encode("utf-8")) #send data as bytes
        print(f"Data sent over USB: {data}")

"""main function"""
def main():
    state = "Stopped" 
    btn_1 = Button1(GP20)
    btn_2 = Button2(GP21, 0.01) #pin, interval
    signal = RandomAlarm(min_time = 0.5, max_time =  1.5) #max/min time interval the alarm will go off in
    obs = None #no observation for now, will update as data is being recorded
    
    pixels = NeoPixel(GP28, 30) 
    pixels[0] = (0, 0, 0) # Turn off LED initially
    
    while True:
        event1 = btn_1.poll()  # Reaction time input
        event2 = btn_2.poll()  # Start/Stop control

        if event2 == "Pressed":
            if btn_2.mode == "Stopped":
                btn_2.toggle_state()
                signal.start() #start alarm
                obs = Obs(start_time=now()) #new observation
                print("Reaction time test started.")
                state = "Wait"
            else:
                btn_2.toggle_state()
                state = "Stopped"
                pixels[0] = (0, 0, 0)  #turn off LED
                print("Reaction time test stopped.")

        if state == "Wait" and signal.alarm(): #BRRRIIIINNNGGGRINGG
            print("Alarm!")
            pixels[0] = (50, 0, 0)  #red LED
            state = "React"

        if state == "React" and event1 == "Pressed":
            obs.record(signal.duration, now() - signal.alarm_time)
            data = obs.serialize()
            print(data)
            write_to_usb(data)  #send data to USB
            signal.reset()
            obs = Obs(start_time=now())
            pixels[0] = (0, 0, 0)  #turn off LED
            state = "Wait"

main()
