## Sesión 5: PWM

**Alumno:** Camila Rodríguez Rosas
**Actividad:** Control de velocidad y dirección de un motor mediante PWM
**Plataforma:** Raspberry Pi Pico 2W

---

## Descripción

En esta práctica se implementó el control de un motor utilizando una señal **PWM (Pulse Width Modulation)** con una Raspberry Pi Pico 2W.

El programa permite controlar la velocidad y dirección de giro del motor mediante un driver de motor. Se implementaron dos modos de funcionamiento: manual y automático*

En el modo manual, la dirección del motor se controla mediante tres botones para avanzar, retroceder y detenerse, al igual que un potenciómetro permite modificar la velocidad del motor entre 0 % y 100 %.

En el modo automático, el motor realiza una secuencia programada de avance, cambio seguro de dirección, reversa y paro. Para evitar cambios bruscos, se utilizan rampas de aceleración y desaceleración, haciendo que la velocidad aumente o disminuya lentamente.