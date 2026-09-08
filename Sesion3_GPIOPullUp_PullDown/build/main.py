from machine import Pin
from time import sleep_ms

# carros
RED_CAR = 15
YELLOW_CAR = 14
GREEN_CAR = 13

# pedestrians
PED_RED = 12
PED_GREEN = 11

#button
BUTTON = 16

red_car = Pin(RED_CAR, Pin.OUT)
yellow_car = Pin(YELLOW_CAR, Pin.OUT)
green_car = Pin(GREEN_CAR, Pin.OUT)
ped_red = Pin(PED_RED, Pin.OUT)
ped_green = Pin(PED_GREEN, Pin.OUT)
button = Pin(BUTTON, Pin.IN, Pin.PULL_UP)

def  set_lights(car_r, car_y, car_g, ped_r, ped_g):
    red_car.value(car_r)
    yellow_car.value(car_y)
    green_car.value(car_g)
    ped_red.value(ped_r)
    ped_green.value(ped_g)

def cars_go():
    print("S0 REPOSO: AUTOS PASAN, PEATON ESPERA")
    set_lights(0,0,1,1,0)

def cars_prepare_to_stop():
    print("S1: AUTOS PREPARAN ALTO")
    set_lights(0,0,1,1,0)
    for i in range(5):
        green_car.toggle()
        sleep_ms(350)
    set_lights(0,1,0,1,0)
    sleep_ms(1000)

def pedestrians_go():
    sleep_ms(100)
    print("S2: PEATON PUEDE PASAR")
    set_lights(1,0,0,0,1)

def pedestrians_finish():
    print("S3: FIN DE CRUCE")
    set_lights(1,0,0,0,1)
    for i in range(6):
        ped_green.toggle()
        sleep_ms(350)
    ped_green.value(0)
    ped_red.value(1)

def crossing_sequence():
    cars_prepare_to_stop()
    sleep_ms(1500)
    
    pedestrians_go()
    sleep_ms(4000)

    pedestrians_finish()
    sleep_ms(500)

    cars_go()

cars_go()
last = 1

while True:
    now = button.value()

    if last == 1 and now == 0:
        sleep_ms(30)

        if button.value() == 0:
            print("Peticion peatonal !!")
            crossing_sequence()

            while button.value() == 0:
                sleep_ms(10)
        
    last = now
    sleep_ms(10)