#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import RPi.GPIO as GPIO                    #Import GPIO library
import time                                #Import time library
import firebase_admin
import os
import sys
import threading
from firebase_admin import credentials
from firebase_admin import db
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)                     #Set GPIO pin numbering
TRIG = 23                                  #Associate pin 23 to TRIG
ECHO = 24                                  #Associate pin 24 to ECHO
IND = 25
ALARM = 12
Motor1A = 2 # set GPIO-02 as Input 1 of the controller IC
Motor1B = 3 # set GPIO-03 as Input 2 of the controller IC
Motor1E = 4 # set GPIO-04 as Enable pin 1 of the controller IC

GPIO.setup(TRIG,GPIO.OUT)                  #Set pin as GPIO out
GPIO.setup(ECHO,GPIO.IN)
GPIO.setup(IND, GPIO.OUT)
GPIO.setup(ALARM,GPIO.OUT)
GPIO.setup(Motor1A,GPIO.OUT)
GPIO.setup(Motor1B,GPIO.OUT)
GPIO.setup(Motor1E,GPIO.OUT)
GPIO.setup(15, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(14, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
global quantity, initial, spent_feul, flag
flag = 0
pwm=GPIO.PWM(4,100) # configuring Enable pin means GPIO-04 for PWM

#def motor_start():


vlog_id=''


def button_callback(channel):
    global flag
    flag = 1
    global initial
    print("abc")
    initial = quantity
    print(initial)
    switch_vehicle_on()

def caller_two(channel):
    global flag
    print("def")
    spent_feul = quantity-initial
    print(spent_feul)
    flag = 0
    switch_vehicle_off(str(spent_feul))



mydbUrl='https://v-monitoring-app.firebaseio.com/'
myTrack_Id='67'
isFirst=True

# Fetch the service account key JSON file contents
cred = credentials.Certificate('/home/pi/VmonitoringKey.json')
# Initialize the app with a service account, granting admin privileges
firebase_admin.initialize_app(cred, {
    'databaseURL': mydbUrl
})

primaryKey=''
ref = db.reference('USERS')
snapshot = ref.order_by_child('track_Id').equal_to(myTrack_Id).get()
for value in snapshot.items():
    primaryKey=value[0]
    #print('\n\n\t{0}'.primaryKey)



def update_feul_level(fuel_value):
    print(fuel_value)
    ref2 = db.reference('USERS/'+primaryKey+'/mileage')
    snapshot = ref2.update({'current_fuel':fuel_value})

def switch_vehicle_on():
    global flag
    global vlog_id
    ref2 = db.reference('VLOGS/'+primaryKey)
    new_post_ref = ref2.push()
    new_post_ref.set({
        'fuel_spent': '',
        'location_off': '',
        'location_on': '',
        'switch_offtime': 0,
        'switch_ontime': 1,
        'travel_distance': ''
    })
    vlog_id=new_post_ref.key

def switch_vehicle_off(fuel_spent):
    print("Bahar off hai")
    global vlog_id
    ref2 = db.reference('VLOGS/'+primaryKey+'/'+vlog_id)
    snapshot = ref2.update({
        'switch_offtime': 1,
        'fuel_spent': fuel_spent   # please send the total fuel spent in trip when sending switch off status
    })
    vlog_id=''


GPIO.add_event_detect(15,GPIO.RISING,callback=button_callback, bouncetime=2000)
GPIO.add_event_detect(14,GPIO.RISING,callback=caller_two, bouncetime=2000)


try:
    while True:
        GPIO.output(TRIG, False)                 #Set TRIG as LOW
        print("Waiting For Sensor To Settle")
        time.sleep(2)                            #Delay of 2 seconds

        GPIO.output(TRIG, True)                  #Set TRIG as HIGH
        time.sleep(0.00001)                      #Delay of 0.00001 seconds
        GPIO.output(TRIG, False)                 #Set TRIG as LOW

        while GPIO.input(ECHO)==0:               #Check whether the ECHO is LOW
            pulse_start = time.time()              #Saves the last known time of LOW pulse

        while GPIO.input(ECHO)==1:               #Check whether the ECHO is HIGH
            pulse_end = time.time()                #Saves the last known time of HIGH pulse

        pulse_duration = pulse_end - pulse_start
        distance = pulse_duration * 17150        #Multiply pulse duration by 17150 to get distance
        distance = round(distance, 0)            #Round to two decimal points

        print ("Distance:", distance, "cm")

        if flag == 1:
            print("FLAG ONE HAI,,")
            pwm.start(70)
            GPIO.output(Motor1A,GPIO.HIGH)
            GPIO.output(Motor1B,GPIO.LOW)
            GPIO.output(Motor1E,GPIO.HIGH)

        elif flag == 0:
            GPIO.output(Motor1E,GPIO.LOW)
            pwm.stop()

        if distance > 12.5 or distance < 6:
            GPIO.output(IND, GPIO.HIGH)
            GPIO.output(ALARM, GPIO.HIGH)
            time.sleep(2)
            GPIO.output(IND,GPIO.LOW)
            GPIO.output(ALARM,GPIO.LOW)
        quantity = ((13 - distance)*470)
        print("Quantity: ", quantity)
        quantity = round(quantity,1)
        update_feul_level(str(quantity))


except KeyboardInterrupt:
    print("Cleaning up")
    GPIO.cleanup()