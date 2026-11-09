#include <string.h>

#include "driver/gpio.h"
#include "driver/spi_master.h"
#include "esp_heap_caps.h"
#include "esp_log.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

#include "ili9341.h"

#define PIN_SCK 26
#define PIN_MOSI 23
#define PIN_MISO 32
#define PIN_CS 20
#define PIN_DC 22
#define PIN_RST 21
#define PIN_BL 27

#define LCD_HOST SPI2_HOST
#define SPI_CLOCK_HZ (20 * 1000 * 1000)
#define TRANSFER_CHUNK 16384

static const char *TAG = "ili9341";
static spi_device_handle_t s_spi;
static uint8_t *s_framebuffer;
static gfx_canvas_t s_canvas;

static void spi_send(const uint8_t *data, size_t length)
{
    while (length) {
        size_t chunk = length > TRANSFER_CHUNK ? TRANSFER_CHUNK : length;
        spi_transaction_t transaction = {
            .length = chunk * 8,
            .tx_buffer = data,
        };
        ESP_ERROR_CHECK(spi_device_polling_transmit(s_spi, &transaction));
        data += chunk;
        length -= chunk;
    }
}

static void lcd_command(uint8_t command,
                        const uint8_t *data,
                        size_t data_length)
{
    gpio_set_level(PIN_CS, 0);
    gpio_set_level(PIN_DC, 0);
    spi_send(&command, 1);
    if (data && data_length) {
        gpio_set_level(PIN_DC, 1);
        spi_send(data, data_length);
    }
    gpio_set_level(PIN_CS, 1);
}

static void delay_ms(unsigned milliseconds)
{
    vTaskDelay(pdMS_TO_TICKS(milliseconds));
}

static void init_sequence(void)
{
    static const uint8_t power_control[] = {0x00, 0xC1, 0x30};
    static const uint8_t power_sequence[] = {0x64, 0x03, 0x12, 0x81};
    static const uint8_t driver_timing[] = {0x85, 0x00, 0x78};
    static const uint8_t power_control_2[] = {0x39, 0x2C, 0x00, 0x34, 0x02};
    static const uint8_t pump_ratio[] = {0x20};
    static const uint8_t driver_timing_2[] = {0x00, 0x00};
    static const uint8_t power_control_3[] = {0x13};
    static const uint8_t power_control_4[] = {0x13};
    static const uint8_t vcom_control[] = {0x22, 0x35};
    static const uint8_t vcom_control_2[] = {0xBD};
    static const uint8_t memory_access[] = {0x08};
    static const uint8_t interface_control[] = {0x0A, 0xA2};
    static const uint8_t pixel_format[] = {0x55};
    static const uint8_t interface_control_2[] = {0x01, 0x30};
    static const uint8_t frame_rate[] = {0x00, 0x1B};
    static const uint8_t enable_3g[] = {0x00};
    static const uint8_t gamma_disable[] = {0x01};
    static const uint8_t positive_gamma[] = {
        0x0F, 0x35, 0x31, 0x0C, 0x0B, 0x0E, 0x06, 0x49,
        0xA7, 0x33, 0x07, 0x0F, 0x03, 0x0C, 0x0A, 0x00,
    };
    static const uint8_t negative_gamma[] = {
        0x00, 0x0E, 0x0A, 0x0F, 0x04, 0x11, 0x08, 0x36,
        0x58, 0x4D, 0x07, 0x10, 0x0C, 0x32, 0x34, 0x0F,
    };

    gpio_set_level(PIN_RST, 1);
    delay_ms(50);
    gpio_set_level(PIN_RST, 0);
    delay_ms(100);
    gpio_set_level(PIN_RST, 1);
    delay_ms(50);

    lcd_command(0xCF, power_control, sizeof(power_control));
    lcd_command(0xED, power_sequence, sizeof(power_sequence));
    lcd_command(0xE8, driver_timing, sizeof(driver_timing));
    lcd_command(0xCB, power_control_2, sizeof(power_control_2));
    lcd_command(0xF7, pump_ratio, sizeof(pump_ratio));
    lcd_command(0xEA, driver_timing_2, sizeof(driver_timing_2));
    lcd_command(0xC0, power_control_3, sizeof(power_control_3));
    lcd_command(0xC1, power_control_4, sizeof(power_control_4));
    lcd_command(0xC5, vcom_control, sizeof(vcom_control));
    lcd_command(0xC7, vcom_control_2, sizeof(vcom_control_2));
    lcd_command(0x21, NULL, 0);
    lcd_command(0x36, memory_access, sizeof(memory_access));
    lcd_command(0xB6, interface_control, sizeof(interface_control));
    lcd_command(0x3A, pixel_format, sizeof(pixel_format));
    lcd_command(0xF6, interface_control_2, sizeof(interface_control_2));
    lcd_command(0xB1, frame_rate, sizeof(frame_rate));
    lcd_command(0xF2, enable_3g, sizeof(enable_3g));
    lcd_command(0x26, gamma_disable, sizeof(gamma_disable));
    lcd_command(0xE0, positive_gamma, sizeof(positive_gamma));
    lcd_command(0xE1, negative_gamma, sizeof(negative_gamma));
    lcd_command(0x11, NULL, 0);
    delay_ms(120);
    lcd_command(0x29, NULL, 0);
    gpio_set_level(PIN_BL, 1);
}

bool ili9341_init(void)
{
    const gpio_config_t output_config = {
        .pin_bit_mask = (1ULL << PIN_CS) |
                        (1ULL << PIN_DC) |
                        (1ULL << PIN_RST) |
                        (1ULL << PIN_BL),
        .mode = GPIO_MODE_OUTPUT,
        .pull_up_en = GPIO_PULLUP_DISABLE,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .intr_type = GPIO_INTR_DISABLE,
    };
    ESP_ERROR_CHECK(gpio_config(&output_config));
    gpio_set_level(PIN_CS, 1);
    gpio_set_level(PIN_DC, 1);
    gpio_set_level(PIN_BL, 0);

    const spi_bus_config_t bus_config = {
        .mosi_io_num = PIN_MOSI,
        .miso_io_num = PIN_MISO,
        .sclk_io_num = PIN_SCK,
        .quadwp_io_num = -1,
        .quadhd_io_num = -1,
        .max_transfer_sz = TRANSFER_CHUNK,
    };
    esp_err_t status = spi_bus_initialize(LCD_HOST, &bus_config, SPI_DMA_CH_AUTO);
    if (status != ESP_OK) {
        ESP_LOGE(TAG, "SPI bus initialization failed: %s", esp_err_to_name(status));
        return false;
    }

    const spi_device_interface_config_t device_config = {
        .clock_speed_hz = SPI_CLOCK_HZ,
        .mode = 0,
        .spics_io_num = -1,
        .queue_size = 1,
    };
    status = spi_bus_add_device(LCD_HOST, &device_config, &s_spi);
    if (status != ESP_OK) {
        ESP_LOGE(TAG, "SPI device initialization failed: %s", esp_err_to_name(status));
        return false;
    }

    s_framebuffer = heap_caps_malloc(
        ILI9341_WIDTH * ILI9341_HEIGHT * 2,
        MALLOC_CAP_SPIRAM | MALLOC_CAP_8BIT);
    if (!s_framebuffer) {
        s_framebuffer = heap_caps_malloc(
            ILI9341_WIDTH * ILI9341_HEIGHT * 2,
            MALLOC_CAP_8BIT);
    }
    if (!s_framebuffer) {
        ESP_LOGE(TAG, "Framebuffer allocation failed");
        return false;
    }

    s_canvas = (gfx_canvas_t){
        .pixels = s_framebuffer,
        .width = ILI9341_WIDTH,
        .height = ILI9341_HEIGHT,
    };
    gfx_clear(&s_canvas, 0);

    init_sequence();
    ESP_LOGI(TAG, "ILI9341 ready at %d MHz", SPI_CLOCK_HZ / 1000000);
    return true;
}

gfx_canvas_t *ili9341_canvas(void)
{
    return &s_canvas;
}

void ili9341_flush(void)
{
    uint8_t column_data[] = {
        0,
        0,
        (ILI9341_WIDTH - 1) >> 8,
        (ILI9341_WIDTH - 1) & 0xFF,
    };
    uint8_t row_data[] = {
        0,
        0,
        (ILI9341_HEIGHT - 1) >> 8,
        (ILI9341_HEIGHT - 1) & 0xFF,
    };
    lcd_command(0x2A, column_data, sizeof(column_data));
    lcd_command(0x2B, row_data, sizeof(row_data));
    lcd_command(0x2C, NULL, 0);

    gpio_set_level(PIN_CS, 0);
    gpio_set_level(PIN_DC, 1);
    spi_send(s_framebuffer, ILI9341_WIDTH * ILI9341_HEIGHT * 2);
    gpio_set_level(PIN_CS, 1);
}
