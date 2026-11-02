idf_component_register(SRCS "main.cpp" INCLUDE_DIRS "." REQUIRES rid_core esp_driver_uart esp_driver_gpio esp_driver_usb_serial_jtag esp_timer)
target_compile_features(${COMPONENT_LIB} PUBLIC cxx_std_17)
