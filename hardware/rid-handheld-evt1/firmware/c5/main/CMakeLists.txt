idf_component_register(SRCS "main.cpp" INCLUDE_DIRS "." REQUIRES rid_core esp_wifi esp_event esp_netif nvs_flash esp_driver_uart)
target_compile_features(${COMPONENT_LIB} PUBLIC cxx_std_17)
