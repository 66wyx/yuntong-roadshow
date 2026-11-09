idf_component_register(
    SRCS
        "app_main.c"
        "wifi_raw.c"
        "rid_decoder.c"
        "rid_runtime.c"
        "ili9341.c"
        "ui_font.c"
        "rid_ui.c"
    INCLUDE_DIRS "."
    REQUIRES nvs_flash esp_event esp_timer esp_driver_spi esp_driver_gpio
    PRIV_REQUIRES esp_hosted
)
