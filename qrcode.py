import json
import warnings
warnings.filterwarnings("ignore")
import gpiozero.pins.mock
from gpiozero import Button, OutputDevice
import cv2
from pyzbar.pyzbar import decode
from datetime import datetime
from time import sleep
import RPi.GPIO as GPIO
import time
import logging
logging.basicConfig(level=logging.ERROR)
import requests
import threading
import multiprocessing
#----------------------------------------------------------------------------------------------------------------------------------

api_key='d10c31e77b686aa'
api_secret='22f59bfe4a84ac9'
base_url='http://192.168.0.100/'



#login_url=f"{base_url}/api/method/login"

headers={
        "Authorization": f"token {api_key}:{api_secret}",
        "Content-Type": "application/json"
        }


#-------------------------------------------------------------------------------------------------------------------------------


GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

relay_pin = 16
button_pin = 19
ir_sensor_pin = 17
buzzer_pin=20
green_led=26
red_led=12
blue_led=4


GPIO.setup(buzzer_pin,GPIO.OUT, initial=GPIO.HIGH)


GPIO.setup(ir_sensor_pin, GPIO.IN)

last_detection_time=0
debounce_time=0.5



relay = OutputDevice(relay_pin)
button = Button(button_pin)
greenon=OutputDevice(green_led)
redon=OutputDevice(red_led)
blue=OutputDevice(blue_led)



def toggle_relay():
    print("---------toggle relay function called -------------")
    relay.on()
    sleep(5)
    relay.off()
    print("---------toggle rela function end---------------")


def red():
	redon.on()
	sleep(1)
	redon.off()

def run():
      blue.on()
      sleep(1)
      blue.off()
      sleep(1)



def buzzer():
	#buzzer.on()
	greenon.on()
	GPIO.output(buzzer_pin, GPIO.LOW)
	sleep(0.5)
	#buzzer.off()
	greenon.off()
	GPIO.output(buzzer_pin, GPIO.HIGH)



def on_button_pressed():
    button_press_time = datetime.now().time()
    button_press_date = datetime.now().date()
    print("\nButton is pressed", button_press_time)
    toggle_relay()
    data2_to_send={
    "doctype":"Buttonlogs",
    "button_status":"Button Pressed",
    "button_pressed_time":button_press_time.strftime("%H:%M"),
    "button_pressed_date":button_press_date.strftime("%Y-%m-%d"),
    }
    api_url=f"{base_url}/api/resource/Buttonlogs"
    response=requests.post(api_url, json=data2_to_send, headers=headers)
    if response.status_code == 200:
        print("Data sent successfully!")

    else:
        print("Error:", response.text)

button.when_pressed = on_button_pressed


def set_pin_high(pin_number):
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(pin_number, GPIO.OUT)

    while True:
        GPIO.output(pin_number, GPIO.HIGH)
        time.sleep(1)



def capture_and_decode():
    # Initialize the camera
    camera = cv2.VideoCapture(0)
    if not camera.isOpened():
        print("Error: Unable to access the camera.")
        return None

    # Give camera time to adjust to light
    sleep(0.5)

    # Capture image
    _, frame = camera.read()
    if frame is None:
        print("Error: Unable to capture frame from camera.")
        camera.release()
        return None

    # Decode QR code from captured image
    decoded_objects = decode(frame)
    camera.release()

    if decoded_objects:
        qr_code_data = decoded_objects[0].data.decode('utf-8')
        return qr_code_data  # Return the decoded QR code data
    else:
        return None




def check_booking_date(start_time_str, end_time_str, booking_date_str):
    # Parse start time, end time, and booking date strings to datetime objects
    start_time = datetime.strptime(start_time_str, "%H:%M").time()
    end_time = datetime.strptime(end_time_str, "%H:%M").time()
    booking_date = datetime.strptime(booking_date_str, "%Y-%m-%d").date()

    # Get current date and time
    current_datetime = datetime.now()
    current_date = current_datetime.date()
    current_time = current_datetime.time()

    # Check if the booking date is today's date
    if booking_date == current_date:
        # Check if the current time is within the booking time range
        if start_time <= current_time <= end_time:
            return True
    return False


# Access values using keys




current_datetime = datetime.now()


def convert_to_dictionary(string):
    try:
        dictionary = eval(string)
        if isinstance(dictionary, dict):
            return dictionary
        else:
            return None
    except json.JSONDecodeError as e:
        print("error occured:", e)
        return None


def system_status():
    button_press_time=datetime.now().time()
    button_press_date=datetime.now().date()
    print("-------Status Running-----")
    #strat_time=time()
    #intervals=60
    while True:
        #current_time=time()
        #elapsed_time=current_time-start_time
        #if elapsed_time>=intervals:
            data3_to_send={
            "doctype":"Sytemstatus",
            "status":"Running",
	    "time":button_press_time.strftime("%H:%M"),
            "date":button_press_date.strftime("%Y-%m-%d"),
            }
            api_url=f"{base_url}/api/resource/Systemstatus"
            response=requests.post(api_url, json=data3_to_send,headers=headers)
            if response.status_code==200:
                print("---Status running Succesfully----")
            else:
                print("Error:", response.text)
            sleep(600)






def main():
    while True:
        blue.on()
        if GPIO.input(ir_sensor_pin)==GPIO.LOW:
            if time.time() - last_detection_time > debounce_time:
                print("objectdetected")
                qr_code_data = capture_and_decode()
                print(qr_code_data)
                print(type(qr_code_data))
                if(qr_code_data):
                    if('Novel_office' in qr_code_data):
                        if(qr_code_data):
                            dict = convert_to_dictionary(qr_code_data)
                            print(dict)
                            id1 = dict['id']
                            location = dict['location']
                            booking_date = dict['booking_date']
                            booking_start_time = dict['booking_start_time']
                            booking_end_time = dict['booking_end_time']
                            room_type = dict['room_type']
                            room = dict['room']
                            if('1771' in id1):
                                if(location == "NTP - Kudlu Gate" and room_type=="Conference Room" and room=="NTP - Kudlu Gate - Conference Room - 01" ):
                                    if check_booking_date(booking_start_time, booking_end_time, booking_date):
                                        print("Access granted")
                                        buzzer()
                                        threading.Thread(target=toggle_relay).start()
                                        data_to_send={
                                                "doctype":"qr_logs",
                                                "id":id1,
                                                "location": location,
                                                "booking_date": booking_date,
                                                "start_time":booking_start_time,
                                                "end_time": booking_end_time,
                                                "room_type": room_type,
                                                "room": room,}
                                        api_url=f"{base_url}/api/resource/qr_logs"
                                        response=requests.post(api_url, json=data_to_send, headers=headers)
                                        if response.status_code == 200:
                                            print("data sent successfully!")
                                        else:
                                            print("Error:", "response.text")
                                    else:
                                        print("invalid time and date")
                                        red()
                                else:
                                    print("Invalid data")
                                    red()
                            else:
                                print("Invalid id")
                                red()
                    else:
                        print("invalid Qr code")
                        red()
    blue.off()

if __name__ == "__main__":
    secondary_thread=threading.Thread(target=system_status)
    secondary_thread.daemon=True
    secondary_thread.start()
    main()
    process_other.start()




