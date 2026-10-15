# Sesión 07 - ADC
# Lee una señal analógica (GP26), la convierte a voltaje y %,
# la filtra con promedio móvil y activa una alarma por umbrales.
# ---------------------------------------------------------------
# Camila Rodríguez Rosas
# 194100
from machine import Pin, ADC
from time import sleep_ms

# Sensor
SENSORS = {
    "POT": 26,   # GP26 / ADC0 ← SIG del potenciómetro
    "LDR": 27,   # GP27 / ADC1 ← AO de la fotoresistencia
}
ACTIVE_SENSOR = "POT"   # "POT" para usar potenciometro
INVERT = False          # True = invierte la escala (100 % ↔ 0 %)

# Declaración de pines
sensor     = ADC(Pin(SENSORS[ACTIVE_SENSOR]))
led_green  = Pin(13, Pin.OUT)  # NORMAL
led_yellow = Pin(14, Pin.OUT)  # WARNING
led_red    = Pin(15, Pin.OUT)  # ALARM

# Sensor config
VREF        = 3.3     # Voltaje de referencia del ADC
ADC_MAX     = 65535   # Valor máximo de read_u16()
WINDOW_SIZE = 10      # Muestras del promedio móvil
WARNING     = 20      # % a partir del cual hay advertencia
ALARM       = 80      # % a partir del cual hay alarma
SAMPLE_MS   = 300     # Periodo de muestreo en ms

window = []           # Últimas lecturas para el filtro


# Raw
def read_raw():
    """Lectura cruda del ADC: 0 a 65535."""
    return sensor.read_u16()


# Escalado
def to_voltage(raw):
    """Convierte la lectura cruda a voltios (0.0 a 3.3 V)."""
    return raw * VREF / ADC_MAX


def to_percent(raw):
    """Convierte la lectura cruda a porcentaje, limitado a 0-100 %."""
    percent = raw * 100 / ADC_MAX
    if INVERT:
        percent = 100 - percent
    return max(0, min(100, percent))


# Filtrado
def filter_avg(new_value):
    """Promedio móvil de las últimas WINDOW_SIZE lecturas."""
    window.append(new_value)
    if len(window) > WINDOW_SIZE:
        window.pop(0)
    return sum(window) / len(window)


# Clasificación
def classify(percent):
    """Clasifica la señal FILTRADA según los umbrales."""
    if percent >= ALARM:
        return "ALARM"
    elif percent >= WARNING:
        return "WARNING"
    else:
        return "NORMAL"


def update_outputs(state):
    """Enciende solo el LED que corresponde al estado."""
    led_green.value(state == "NORMAL")
    led_yellow.value(state == "WARNING")
    led_red.value(state == "ALARM")


# Print general
def print_status(raw, voltage, percent, filtered_percent, state):
    """Una línea por muestra: fácil de leer y de capturar como evidencia."""
    print("raw={:5d} | V={:.2f} V | {:5.1f} % | filtrado={:5.1f} % | {}".format(
        raw, voltage, percent, filtered_percent, state))


# Main
update_outputs(None)   # Arranque seguro: todos los LEDs apagados
print("Smart Analog Monitor | sensor={} (GP{}) | invertido={} | WARNING >= {} % | ALARM >= {} %".format(
    ACTIVE_SENSOR, SENSORS[ACTIVE_SENSOR], INVERT, WARNING, ALARM))

while True:
    raw              = read_raw()
    filtered_raw     = filter_avg(raw)
    voltage          = to_voltage(raw)
    percent          = to_percent(raw)
    filtered_percent = to_percent(filtered_raw)

    state = classify(filtered_percent)   # Decide con la señal filtrada
    update_outputs(state)
    print_status(raw, voltage, percent, filtered_percent, state)

    sleep_ms(SAMPLE_MS)