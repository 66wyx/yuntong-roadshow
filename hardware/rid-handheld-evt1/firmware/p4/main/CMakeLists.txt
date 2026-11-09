idf_component_register(
    SRCS
        "app_main.c"
        "wifi_raw.c"
        "rid_decoder.c"
        "rid_runtime.c"
        "rid_geo.c"
        "rid_gfx.c"
        "ili9341.c"
        "ui_font.c"
        "ui_font_data.c"
        "rid_ui.c"
    INCLUDE_DIRS "."
    REQUIRES nvs_flash esp_event esp_timer esp_driver_spi esp_driver_gpio
    PRIV_REQUIRES esp_hosted
)

# The UI runs per-pixel float math every frame; keep it fast even in debug builds.
set_source_files_properties(rid_gfx.c rid_ui.c PROPERTIES COMPILE_OPTIONS "-O2")
