*** Sesión 3: Práctica semáforo ***
*** Camila Rodríguez Rosas  - 194100 ***
*** Laboratorio de elementos programables ***
Este código implementa un semáforo para automóviles y peatones utilizando una Raspberry Pi Pico 2W y MicroPython. El sistema controla las luces de los autos y peatones mediante una máquina de estados y permite solicitar el cruce peatonal mediante un botón.

En su estado base, los autos tienen la luz verde y los peatones la luz roja. Cuando se presiona el botón, el sistema hace parpadear la luz verde de los autos, cambia a amarillo y detiene el tráfico. Después, habilita el paso de los peatones mediante la luz verde durante unos segundos. Finalmente, la luz verde peatonal parpadea para indicar el final del cruce y el sistema regresa al estado inicial.

El botón utiliza una resistencia pull-up interna y se incluye un pequeño debounce para evitar detectar múltiples pulsaciones accidentales.