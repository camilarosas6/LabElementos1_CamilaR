# Camila Rodríguez Rosas
# Laboratorio de Elementos Programables
# Sesion 5: PWM
from machine import Pin, PWM, ADC
from time import sleep_ms, ticks_ms, ticks_diff

MODO = "AUTO"

IN1 = Pin(2, Pin.OUT)
IN2 = Pin(3, Pin.OUT)
ENA = PWM(Pin(4))
ENA.freq(1000)

btn_forward = Pin(14, Pin.IN, Pin.PULL_UP)
btn_reverse = Pin(15, Pin.IN, Pin.PULL_UP)
btn_stop = Pin(16, Pin.IN, Pin.PULL_UP)

pot = ADC(26)

def set_speed(percent):
    percent = max(0, min(100, percent))
    duty = int(percent * 65535 / 100)
    ENA.duty_u16(duty)

def forward():
    IN1.value(1)
    IN2.value(0)

def reverse():
    IN1.value(0)
    IN2.value(1)

def stop():
    set_speed(0)
    IN1.value(0)
    IN2.value(0)

def ramp_to(start, end, step=10, delay_ms=100):
    start = max(0, min(100, start))
    end = max(0, min(100, end))

    if start <= end:
        sequence = range(start, end + 1, step)
        etiqueta = "Acelerando"
    else:
        sequence = range(start, end - 1, -step)
        etiqueta = "Desacelerando"

    speed = start
    for speed in sequence:
        set_speed(speed)
        print(etiqueta, speed, "%")
        sleep_ms(delay_ms)

    if speed != end:
        set_speed(end)
        print(etiqueta, end, "%")
        sleep_ms(delay_ms)

def change_direction(new_dir, current_speed):
    print("Cambio seguro de direccion: bajando a 0 % primero")
    ramp_to(current_speed, 0)
    stop()
    sleep_ms(300)
    new_dir()

def speed_test():
    print("-----Prueba-----")
    forward()
    for p in [25, 50, 75, 100]:
        set_speed(p)
        print("Prueba velocidad:", p, "%")
        sleep_ms(1500)
    ramp_to(100, 0)
    stop()
    print("MOTOR STOP")

def modo_auto():
    stop()
    print("MOTOR STOP")
    sleep_ms(1000)

    speed_test()
    sleep_ms(1000)

    while True:
        print("--- AVANZAR ---")
        forward()
        ramp_to(0, 100)
        print("Mantener 100 %")
        sleep_ms(2000)

        change_direction(reverse, 100)
        print("--- REVERSA ---")
        ramp_to(0, 75)
        print("Mantener 75 %")
        sleep_ms(2000)

        ramp_to(75, 0)
        stop()
        print("MOTOR STOP")
        sleep_ms(2000)

pedido = 0
ultimo_click = ticks_ms() - 150 # Asegurarse de que el primer click sea válido

def boton_irq(pin):
    global pedido, ultimo_click

    ahora = ticks_ms()

    if ticks_diff(ahora, ultimo_click) < 150:
        return

    ultimo_click = ahora

    if pin == btn_forward: # comprueba que la irq fue activada por el botón de avanzar
        pedido = 1
    elif pin == btn_reverse: # comprobar reversa
        pedido = -1
    else:
        pedido = 0

def leer_pot_percent():
    return int(pot.read_u16() * 100 / 65535)

def modo_manual():
    btn_forward.irq(trigger=Pin.IRQ_FALLING, handler=boton_irq)
    btn_reverse.irq(trigger=Pin.IRQ_FALLING, handler=boton_irq)
    btn_stop.irq(trigger=Pin.IRQ_FALLING, handler=boton_irq)

    direction = 0
    velocity = 0
    PASO = 2
    ultimo_print = ""

    stop()
    print("MODO MANUAL: F = forward, R = reverse, S = stop, pot = velocidad")

    while True:
        if pedido != direction:
            objetivo = 0
        elif direction == 0:
            objetivo = 0
        else:
            objetivo = leer_pot_percent()

        if velocity < objetivo:
            velocity = min(velocity + PASO, objetivo)
        elif velocity > objetivo:
            velocity = max(velocity - PASO, objetivo)

        set_speed(velocity)

        if velocity == 0 and pedido != direction:
            direction = pedido

            if direction == 1:
                forward()
            elif direction == -1:
                reverse()
            else:
                stop()

        nombre = {1: "FORWARD", -1: "REVERSE", 0: "STOP"}[direction]
        estado = nombre + " " + str(velocity) + " %"

        if estado != ultimo_print:
            print(estado)
            ultimo_print = estado

        sleep_ms(40)

if MODO == "MANUAL":
    modo_manual()
else:
    modo_auto()