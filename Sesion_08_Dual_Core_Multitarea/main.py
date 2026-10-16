# Sesion 8 - multicore
# Camila Rodríguez Rosas
# Jonathan Hernández Lazcano

from machine import Pin, ADC
from utime import ticks_ms, ticks_diff, ticks_add, sleep_ms

# Valores fijos
SENSOR_MS = 2         # tarea sensor: cada 2 ms (~500 Hz)
BUTTON_MS = 10
UI_MS     = 200
LOG_MS    = 1000

WINDOW    = 32        # promedio 

WARN_PCT  = 50        # < 50 %          -> NORMAL  =  verde
ALARM_PCT = 75        # 50 % a < 75 %   -> WARNING =  amarillo
                      # >= 75 %         -> ALARM   =  rojo

# Rango mínimo (en raw) para considerar que ya está calibrado. 3000 raw ≈ 0.15 V.
MIN_SPAN  = 3000

DEBOUNCE_MS   = 30
LONG_PRESS_MS = 1000  # pulsación larga = RESET
VREF          = 3.3

# Prueba stress
STRESS_BLOCK_MS = 0

# Estados
STATES = ('NORMAL', 'WARNING', 'ALARM')

# Pines físicos
adc        = ADC(Pin(26))
led_green  = Pin(16, Pin.OUT)
led_yellow = Pin(17, Pin.OUT)
led_red    = Pin(18, Pin.OUT)
led_blue   = Pin(19, Pin.OUT)
button     = Pin(20, Pin.IN, Pin.PULL_UP)

# Sensor
buf = [0] * WINDOW
idx = 0
count = 0
total = 0
raw = 0
avg = 0
pct10 = 0
state = 0
samples = 0

cal_min = 65535       # se irá ajustando hacia abajo
cal_max = 0           # se irá ajustando hacia arriba
calibrated = False

WARN10 = WARN_PCT * 10
ALARM10 = ALARM_PCT * 10


def sensor_task():
    """Leer , filtrar , auto-calibrar , clasificar."""
    global idx, count, total, raw, avg, pct10, state, samples
    global cal_min, cal_max, calibrated

    # Leer y filtrar
    raw = adc.read_u16()
    total -= buf[idx]
    buf[idx] = raw
    total += raw
    idx += 1
    if idx == WINDOW:
        idx = 0
    if count < WINDOW:
        count += 1
    avg = total // count

    # Auto-calibración con la señal FILTRADA (ignora picos de ruido)
    if avg < cal_min:
        cal_min = avg
    if avg > cal_max:
        cal_max = avg
    span = cal_max - cal_min
    calibrated = span >= MIN_SPAN

    # Porcentaje dentro del rango real (0..1000 décimas)
    if calibrated:
        p = (avg - cal_min) * 1000 // span
        if p < 0:
            p = 0
        elif p > 1000:
            p = 1000
        pct10 = p
    else:
        pct10 = 0

    # Clasificar
    if pct10 < WARN10:
        state = 0
    elif pct10 < ALARM10:
        state = 1
    else:
        state = 2
    samples += 1


def reset_sensor():
    global idx, count, total, samples, cal_min, cal_max, calibrated
    for i in range(WINDOW):
        buf[i] = 0
    idx = 0
    count = 0
    total = 0
    samples = 0
    cal_min = 65535
    cal_max = 0
    calibrated = False


# Procesos secundarios
blink = False
hb = False
last_ui_state = -1
prev_samples = 0
prev_log_t = 0

btn_raw = 1
btn_stable = 1
btn_changed_at = 0
btn_down_at = 0
btn_long_done = False


def due(now, deadline):
    return ticks_diff(now, deadline) >= 0


def do_ack():
    global acked
    if state != 2:
        print('[BTN] ACK ignorado (no hay alarma activa)')
    elif acked:
        print('[BTN] ACK ignorado (alarma ya reconocida)')
    else:
        acked = True
        print('[BTN] ACK: alarma reconocida (LED rojo fijo)')


def do_reset():
    global acked, prev_samples
    reset_sensor()
    acked = False
    prev_samples = 0
    print('[BTN] RESET: filtro, contador y calibración reiniciados. Gira el pot de extremo a extremo.')


def button_task(now):
    global btn_raw, btn_stable, btn_changed_at, btn_down_at, btn_long_done

    level = button.value()
    if level != btn_raw:
        btn_raw = level
        btn_changed_at = now
    elif level != btn_stable and ticks_diff(now, btn_changed_at) >= DEBOUNCE_MS:
        btn_stable = level
        if level == 0:
            btn_down_at = now
            btn_long_done = False
        else:
            if not btn_long_done:
                do_ack()

    if btn_stable == 0 and not btn_long_done \
            and ticks_diff(now, btn_down_at) >= LONG_PRESS_MS:
        btn_long_done = True
        do_reset()


def ui_task():
    global hb, blink, acked, last_ui_state

    if STRESS_BLOCK_MS:
        sleep_ms(STRESS_BLOCK_MS)           # bloqueo intencional - pruebas

    hb = not hb
    led_blue.value(hb)

    led_green.value(state == 0)
    led_yellow.value(state == 1)

    if state == 2:
        if acked:
            led_red.value(1)
        else:
            blink = not blink
            led_red.value(blink)
    else:
        blink = False
        acked = False                       # al salir de ALARM se rearma el ACK
        led_red.value(0)

    if state != last_ui_state:
        if last_ui_state != -1:
            print('[EVENT] {} -> {}'.format(STATES[last_ui_state], STATES[state]))
        last_ui_state = state


def log_task(now):
    global prev_samples, prev_log_t

    dt = ticks_diff(now, prev_log_t)
    dn = samples - prev_samples
    if dn < 0:
        dn = samples
    fs = (dn * 1000 // dt) if dt > 0 else 0
    prev_samples = samples
    prev_log_t = now

    voltage = avg * VREF / 65535            # voltaje real en GP26
    if calibrated:
        cal_txt = '{}..{}'.format(cal_min, cal_max)
    else:
        cal_txt = 'CALIBRANDO (gira el pot de extremo a extremo)'
    print('raw={} avg={} pct={:.1f}% voltage={:.2f}V state={} fs={}Hz ack={} cal={}'.format(
        raw, avg, pct10 / 10, voltage, STATES[state], fs,
        'SI' if acked else 'NO', cal_txt))


# Main
print('Sensor {} ms | UI {} ms | log {} ms | ventana={}'.format(
    SENSOR_MS, UI_MS, LOG_MS, WINDOW))
print('Umbrales: WARNING >= {} % | ALARM >= {} % (sobre el rango real del pot)'.format(
    WARN_PCT, ALARM_PCT))
print('Gira el potenciómetro de un extremo al otro para calibrar.')
print('Botón: corto = ACK, largo (1 s) = RESET + recalibrar')
if STRESS_BLOCK_MS:
    print('!! STRESS_BLOCK_MS={} activo: la UI bloquea TODO el núcleo'.format(STRESS_BLOCK_MS))

t0 = ticks_ms()
prev_log_t = t0
next_sensor = t0
next_button = t0
next_ui = t0
next_log = ticks_add(t0, LOG_MS)

try:
    while True:
        now = ticks_ms()

        if due(now, next_sensor):
            sensor_task()
            next_sensor = ticks_add(now, SENSOR_MS)

        if due(now, next_button):
            button_task(now)
            next_button = ticks_add(now, BUTTON_MS)

        if due(now, next_ui):
            ui_task()
            next_ui = ticks_add(ticks_ms(), UI_MS)

        if due(now, next_log):
            log_task(now)
            next_log = ticks_add(now, LOG_MS)

        sleep_ms(1)

except KeyboardInterrupt:
    print('Deteniendo...')

finally:
    for led in (led_green, led_yellow, led_red, led_blue):
        led.value(0)