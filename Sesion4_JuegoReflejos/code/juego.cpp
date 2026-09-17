#include <stdio.h>
#include "pico/stdlib.h"
#include "hardware/gpio.h"
#include "pico/time.h"

// pines

#define LED_SIGNAL 15
#define LED_WAIT   14
#define BUTTON     16


// estados

#define STATE_WAITING 0
#define STATE_READY   1
#define STATE_DONE    2


// variables globales
volatile int state = STATE_DONE;

volatile uint64_t start_us = 0;
volatile uint64_t reaction_us = 0;

volatile bool result_ready = false;
volatile bool false_start = false;

volatile uint64_t last_irq_us = 0;

int round_number = 0;

// ID del alarma de la ronda actual
alarm_id_t alarm_id;


// muestra señal

int64_t show_signal(alarm_id_t id, void *user_data) {

    gpio_put(LED_SIGNAL, 1);
    gpio_put(LED_WAIT, 0);

    // Guardamos el instante en que apareció la señal
    start_us = time_us_64();

    state = STATE_READY;

    // one-shot.
    return 0;
}


// programar nueva ronda

void schedule_round() {

    round_number++;

    gpio_put(LED_SIGNAL, 0);
    gpio_put(LED_WAIT, 1);

    result_ready = false;
    false_start = false;

    state = STATE_WAITING;


    // Número aleatorio entre 1000 y 10000 ms
    uint32_t delay_ms =
        1000 + (get_rand_32() % 9001);


    printf("\n===============================\n");

    printf("Round %d\n", round_number);

    printf("Espera la señal visual. "
           "No presiones antes.\n");

    printf("Delay aleatorio: %lu ms\n",
           delay_ms);

    printf("=================================\n");


    // Crear alarma de una sola ejecución
    alarm_id = add_alarm_in_ms(
        delay_ms,
        show_signal,
        NULL,
        true
    );
}


// interrupcion del botón

void button_irq(
    uint gpio,
    uint32_t events
) {

    uint64_t now = time_us_64();


    // debounce: ignorar si la interrupción es muy cercana a la anterior
    if ((now - last_irq_us) < 80000) {
        return;
    }

    last_irq_us = now;


    // boton despues de la señal

    if (state == STATE_READY) {

        reaction_us = now - start_us;

        gpio_put(LED_SIGNAL, 0);

        result_ready = true;

        state = STATE_DONE;
    }


    // boton antes de la señal

    else if (state == STATE_WAITING) {

        // Cancelar el alarma
        cancel_alarm(alarm_id);

        false_start = true;

        result_ready = true;

        state = STATE_DONE;
    }
}


// main

int main() {

    // Inicializar el sistema
    stdio_init_all();


    // configurar leds
    gpio_init(LED_SIGNAL);
    gpio_set_dir(LED_SIGNAL, GPIO_OUT);
    gpio_put(LED_SIGNAL, 0);


    gpio_init(LED_WAIT);
    gpio_set_dir(LED_WAIT, GPIO_OUT);
    gpio_put(LED_WAIT, 0);


    // set botón

    gpio_init(BUTTON);

    gpio_set_dir(BUTTON, GPIO_IN);

    // Pull-up interno
    gpio_pull_up(BUTTON);


    // set irq

    gpio_set_irq_enabled_with_callback(
        BUTTON,
        GPIO_IRQ_EDGE_FALL,
        true,
        &button_irq
    );


    printf("JUEGO DE LOS REFLEJOS\n");


    // Primera ronda
    schedule_round();


    // main loop

    while (true) {

        if (result_ready) {

            if (false_start) {

                printf(
                    "SALIDA EN FALSO: "
                    "presionaste antes de la senal\n"
                );

            }
            else {

                // microsegundos a milisegundos
                uint64_t reaction_ms =
                    reaction_us / 1000;

                printf(
                    "Tiempo de reaccion: "
                    "%llu ms\n",
                    reaction_ms
                );
            }


            // Esperar 1.8 segundos
            sleep_ms(1800);

            // Esperar a que se suelte el botón

            while (gpio_get(BUTTON) == 0) {
                sleep_ms(10);
            }
            // Nueva ronda
            schedule_round();
        }
        sleep_ms(20);
    }
}