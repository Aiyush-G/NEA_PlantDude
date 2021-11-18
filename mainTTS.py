################################################
###    Aiyush Gupta - NEA Design Technology  ###
###      Web Server - bottle, requests       ###
### Functional - random, time, threading, os ###
### TTS - Pygame, Pyttsx3, gTTS, IBM Watson  ###
################################################

from bottle import route, run, template, static_file, request, Jinja2Template
import requests
# from playsound import playsound Doesn't work on RPI instead using PyGame
from pygame import mixer
from random import randint
import pyttsx3
from time import sleep
from threading import Thread
import os

# For TTS - if online: try IBM except GTTS else: Engine
from gtts import gTTS
global engine

from ibm_watson import TextToSpeechV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator

# DHT11
import Adafruit_DHT

# Buttons
import RPi.GPIO as GPIO

# Button Pins
# DHT PIN = 23
p1 = 17
p2 = 27
p3 = 22

# Variables
plant = "pear" # This is the default - everything else is handled by dataframe - aka. on boot this is default
highQualityTTS = False

# IBM Auth Keys - dont expose - used for TTS

authenticator = IAMAuthenticator('lmdgQT1vHGmBpOZSrsHM_HaeAaAieNO7uC2NLBHMlcVl')
text_to_speech = TextToSpeechV1(
    authenticator=authenticator
)

text_to_speech.set_service_url('https://api.eu-gb.text-to-speech.watson.cloud.ibm.com/instances/326d3ba3-d11d-4851-897b-ce33846e5388')


class updatePd:

    def __init__ (self, plant):
        self.plant = plant

        self.DHT_SENSOR = Adafruit_DHT.DHT11
        self.DHT_PIN = 23

        self.temperatureAndHumidity()
        self.update(plant)

    def temperatureAndHumidity(self):
        self.humidity, self.temperature = Adafruit_DHT.read(self.DHT_SENSOR, self.DHT_PIN)
        if self.humidity is not None and self.temperature is not None:
            print("Temp={0:0.1f}C Humidity={1:0.1f}%".format(self.temperature, self.humidity))
        else:
            print("Sensor failure. Check wiring.")


    def update(self, plant):
        self.plant = plant
        self.response = requests.get(("https://openfarm.cc/api/v1/crops/" + self.plant)) 
        self.name = self.response.json()["data"]["attributes"]["name"]
        self.binomial_name = self.response.json()["data"]["attributes"]["binomial_name"]
        self.description = self.response.json()["data"]["attributes"]["description"]
        self.short_description = str(self.description[ 0 : 250 ]) + "..."
        self.common_names = self.response.json()["data"]["attributes"]["common_names"]
        self.image = self.response.json()["included"][0]["attributes"]["image_url"]

        self.pd = {
            "webTitle": "AG NEA",
            "pageTitle": "Aiyush G - NEA",
            "ff": self.plant,
            "shortDesc": self.short_description,
            "longDesc" : self.description,
            "temperature" : self.temperature,
            "humidity" : self.humidity,
            "LED": True,
            "speaker": False,
            "speakerVolume": 2,
            "image" : self.image,
        }



# How to update plant being used
info = updatePd("apple")

greetingAudio = {
    "1":"audio/greeting/1.mp3",
    "2":"audio/greeting/2.mp3",
    "3":"audio/greeting/3.mp3",
    "4":"audio/greeting/4.mp3",
    "5":"audio/greeting/5.mp3",
    "6":"audio/greeting/6.mp3",
    
}

buttonAudio = {
    "1":"audio/buttonClick/1.mp3",
    "2":"audio/buttonClick/2.mp3",
    "3":"audio/buttonClick/3.mp3",
    "4":"audio/buttonClick/4.mp3"   
}



def volume():
    return int(info.pd["speakerVolume"]) * 0.02

# Initialise the pyttsx and sync volume
engine = pyttsx3.init()
engine.setProperty('volume', volume())
mixer.init()


def TTS(text):

    def GTTS(text):
        tts = gTTS(text=text, lang='en')
        tts.save(filename)

    filename = "temp.mp3"

    if connected():
        if highQualityTTS:
            try:
                with open(filename, 'wb') as audio_file:
                    audio_file.write(
                        text_to_speech.synthesize(
                            (f'<prosody rate="slow" pitch="medium">{ text }</prosody>'),
                            voice='en-GB_JamesV3Voice',
                            accept='audio/mp3'        
                        ).get_result().content)

            except ApiException as ex:
                print(" IBM Method failed with status code " + str(ex.code) + ": " + ex.message)

                GTTS(text)

        else:
            GTTS(text)

        try:
            mixer.music.load(filename)
            mixer.music.play()

            os.remove(filename)
        except:
            print ("TTS Online Both Failed")
    else:
        engine.say(text)
        engine.runAndWait()


# Redundant
def speak(text):
    tts = gTTS(text=text, lang='en')
    filename = "temp.mp3"
    tts.save(filename)

    # Sound doesn't support mp3??
    #sound = mixer.Sound(filename)
    #sound.set_volume(0.1)
    #sound.play()

    mixer.music.load(filename)
    mixer.music.play()

    os.remove(filename)
  
# Changes the functionality available  
def connected(url='http://google.com'):
    timeout = 5
    try:
            request = requests.get(url, timeout=timeout)
            print("Connected to the Internet")
            return True
    except (requests.ConnectionError, requests.Timeout) as exception:
            print("No internet connection.")
            return False
    


def intro():
    text = """I'm Plant Dude - your personal plant assistant - I've been dedicated a custom plant, and I'll tell you all about it and share some awesome facts!
                    To learn more click the left red button. To access the web client where I've hidden some Easter Eggs then access the app!"""
    TTS(text)
    
def greeting():
    # playsound(greetingAudio[track]) DEPRECEATED
    
    
    track = greetingAudio[str(randint(1,6))]
    mixer.music.load(track)
    mixer.music.play()
    sleep(1)
    
def learn():
    text = """Hi, using me is pretty simple. Use the switch on the side to turn me on or off.
               Use the buttons on the top to: 1. read these instruction again, 2. learn about the
               plant and surroundings, 3. Find about the termpature and humidity!"""

    TTS(text)


def temperature(temp):

    warmWeatherGreeting = {
        "1":"Nice",
        "2":"Woah",
        "3":"Yay",
        "4":"Awesome"   
    }

    coldWeatherGreeting = {
        "1":"Oh no",
        "2":"Unfortunately",
        "3":"That is not summer weather",
        "4":"I wish it was warmer"   
    }

    warmSyn = {
        "1":"warm",
        "2":"hot",
        "3":"quite warm",
        "4":"boiling"   
    }

    coldSyn = {
        "1":"Nice",
        "2":"Woah",
        "3":"Yay",
        "4":"Awesome"   
    }

    warmWeatherGreetingAcc = warmWeatherGreeting[str(randint(1,4))]
    coldWeatherGreetingAcc = coldWeatherGreeting[str(randint(1,4))]
    warmSynAcc = warmSyn[str(randint(1,4))]
    coldSynAcc = coldSyn[str(randint(1,4))]

    
    if temp > 20:
        text = f"{warmWeatherGreetingAcc}, it is { temp } degrees celcius: that is {warmSynAcc}. Did you know that fruits such as Mangos, apple & pears can grow in this environment!"
        print(text)

        TTS(text)

    if temp < 20:
        text = f"{coldWeatherGreetingAcc}, it is { temp } degrees celcius: that is {coldSynAcc}. Did you know that plants such as Lavender, Chives and lettuce can grow at this temperature!"
        print(text)

        TTS(text)

def buttonAcknowledgement():
    track = buttonAudio[str(randint(1,4))]
    mixer.music.load(track)
    mixer.music.play()
    sleep(1)

def getPlantInfo(plant):
    response = requests.get(("https://openfarm.cc/api/v1/crops/" + plant))
    
    name = response.json()["data"]["attributes"]["name"]
    binomial_name = response.json()["data"]["attributes"]["binomial_name"]
    description = response.json()["data"]["attributes"]["description"]
    common_names = response.json()["data"]["attributes"]["common_names"]


    intro = {
        "1" : "I'm going to tell you about the",
        "2" : "Well, this is what I found on the",
        "3" : "Well that is interesting! Here is what I found about the",
        "4" : "Awesome, I've always wanted to know more about the"
        }

    facts = {
        "1" : "I did a quick search and this is what I found about the",
        "2" : "Using an intelligent algorithm this is what I found about the",
        "3" : "Using my cool processor this is what I found about the",
        "4" : "Brilliant! This is what I found about thee"
        }

    introSeq = intro[(str(randint(1,4)))]
    factsSeq = facts[(str(randint(1,4)))]

    print(name)
    print(binomial_name)
    print(description)
    print(common_names)

    finalMessage=[]

    if name != None:
        message = f"""

        {introSeq} {name} species. 
        """
    
        finalMessage.append(message)
        #engine.say(message)
        #engine.runAndWait()
    else:
        #engine.say(f"Hmm.. I couldn't find anything about {plant}, try a different one!")
        #engine.runAndWait()

        message = f"Hmm.. I couldn't find anything about {plant}, try a different one!"
        finalMessage.append(message)
        
    if binomial_name != None:
        message = f"""
                    Or should I say {binomial_name} as it is binomially named.
                """

        finalMessage.append(message)
        #engine.say(message)
        #engine.runAndWait()
        
    if description != None:
        message = f"""
                    {factsSeq} {name}! {description}
                """

        finalMessage.append(message)
        #engine.say(message)
        #engine.runAndWait()
    else:
        message = f"Oh no! I couldn't find any cool facts on {plant}, maybe try a different one?"
        finalMessage.append(message)
        #engine.say(f"Oh no! I couldn't find any cool facts on {plant}, maybe try a different one?")
        #engine.runAndWait()

    text = " ".join(str(x) for x in finalMessage)

    TTS(text)
        
def discoMode():
    mixer.music.load("audio/easterEgg.mp3")
    mixer.music.play()
        
# WEB SERVER
@route('/static/:path#.+#', name='static')
def static(path):
    return static_file(path, root='static')

@route("/<name>")
def new(name):

    info.update(name)
    return template('index.tpl', info.pd)

@route('/')
def index():
    return template('index.tpl', info.pd)

@route('/', method="POST")
def index():
            
    LED = request.forms.get('LED')
    speaker = request.forms.get('speaker')
    speakerVolume = request.forms.get('speakerVolume')
    
    howToUse = request.forms.get('howToUse')
    forcast = request.forms.get('forcast')
    restart = request.forms.get('restart')

    disco = request.forms.get('disco')
    
    print(howToUse, "how to use")
    print(forcast, "forcast")
    

    if True:
        # Change Speaker Volume

        if engine._inLoop:
            engine.endLoop()
    
        print ("Speaker Volume")
        info.pd["speakerVolume"] = speakerVolume
        print(info.pd["speakerVolume"])

        # Conversion is needed since max vol = 1, lowest = 0
        engine.setProperty('volume',(volume()))

    if LED == "Lighting":
        # Change LEDs
        print ("LED")
        info.pd["LED"] =  not info.pd["LED"]
        print (info.pd["LED"], type(info.pd["LED"]))
        return template('index.tpl', info.pd)

    elif restart == "Kill Engine":
        #os.execv(sys.executable, ['python'] + sys.argv)
        engine.stop()
        #engine = pyttsx3.init()

    elif disco == "Music Mode":
        discoMode()
        
    elif forcast == "Local Forcast":
        print ("forcast clicked")
        temp = info.pd["temperature"]

        try:
            
            Thread(target=temperature, args=(temp, )).start()
        except:
            print ("Hmm... I cannot get the temperature")
        

    elif howToUse == "How to Use":
        try:
            Thread(target=learn).start()
        except:
            print ("Hmm I cannot tell you how to use me")
        
        
    elif speaker == "Speaker":
        # Speaker Starts
        print("Speaker")
        info.pd["speaker"] =  not info.pd["speaker"]
        print (info.pd["speaker"], type(info.pd["speaker"]))

        try:
            # Speak about the plant
            #getPlantInfo((pd["ff"]))
            plantInfo = info.pd["ff"]
            Thread(target=getPlantInfo, args=(plantInfo, )).start()
        except:
            print("Hmmm... I couldn't tell you about the plant!")
        
        return template('index.tpl', info.pd)
    

    return template('index.tpl', info.pd)

# buttonAcknowledgement()

# On Plant Info Button Clicked
#getPlantInfo("mango")
#greeting()
#intro()


def startWebserver():
    if connected():
        run(host='0.0.0.0', port=8080, debug=True)
    else:
        print ("AI Speech To Text and Audio is not currently available - please connect to the internet")
        engine.say("You are currently not connected to the internet - you're missing out on some awesome features. For example, real-time weather location, flora and fauna information, weather forcasting and much more.")
        engine.runAndWait()

def ioPins():
    # Check for Button Clicks Here
    # 1. Instructions - learn()
    # 2. Plants
    # 3. Temperature & Humidity
    #### TESTING ####
    def button_callback(channel):
        print("Button was pushed!")

    GPIO.setwarnings(False) # Ignore warning for now
    GPIO.setmode(GPIO.BCM)  # Use physical pin numbering

    GPIO.setup(p1, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) # Set pin 10 to be an input pin and set initial value to be pulled low (off)
    GPIO.setup(p2, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(p3, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

    GPIO.add_event_detect(p1,GPIO.RISING,callback=learn) # Setup event on pin 10 rising edge
    GPIO.add_event_detect(p2,GPIO.RISING,callback=getPlantInfo) # Setup event on pin 10 rising edge
    GPIO.add_event_detect(p3,GPIO.RISING,callback=temperature) # Setup event on pin 10 rising edge

    message = input("Press enter to quit\n\n") # Run until someone presses enter

    GPIO.cleanup() # Clean up

if __name__ == '__main__':
    #greeting()
    #intro()
    Thread(target = startWebserver).start()
    Thread(target = ioPins).start()
