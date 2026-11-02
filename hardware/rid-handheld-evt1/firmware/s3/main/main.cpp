#include "rid_core.hpp"
#include "board_pins.hpp"
#include "driver/uart.h"
#include "driver/gpio.h"
#include "driver/usb_serial_jtag.h"
#include "esp_check.h"
#include "esp_log.h"
#include "esp_timer.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "sdkconfig.h"
#include <cstdio>
#include <cstring>

namespace {
constexpr char tag[]="RID_EVT1";
std::uint64_t frames[2]{};
rid::FrameParser parsers[2];
bool ready[2]{};
std::uint64_t last_rx_ms[2]{};
#if CONFIG_EVT1_BOARD_REVIEWED
void configure_radio(uart_port_t port,int tx,int rx,int control) {
  gpio_set_level(static_cast<gpio_num_t>(control),1);
  gpio_set_direction(static_cast<gpio_num_t>(control),GPIO_MODE_OUTPUT);
  uart_config_t cfg{};cfg.baud_rate=921600;cfg.data_bits=UART_DATA_8_BITS;
  cfg.parity=UART_PARITY_DISABLE;cfg.stop_bits=UART_STOP_BITS_1;
  cfg.flow_ctrl=UART_HW_FLOWCTRL_DISABLE;cfg.source_clk=UART_SCLK_DEFAULT;
  ESP_ERROR_CHECK(uart_param_config(port,&cfg));
  ESP_ERROR_CHECK(uart_set_pin(port,tx,rx,UART_PIN_NO_CHANGE,UART_PIN_NO_CHANGE));
  ESP_ERROR_CHECK(uart_driver_install(port,4096,0,0,nullptr,0));
}
#endif
void send_line(const char* s) {
  usb_serial_jtag_write_bytes(s,std::strlen(s),pdMS_TO_TICKS(50));
}
}
extern "C" void app_main() {
  usb_serial_jtag_driver_config_t usb=USB_SERIAL_JTAG_DRIVER_CONFIG_DEFAULT();
  ESP_ERROR_CHECK(usb_serial_jtag_driver_install(&usb));
  ESP_LOGI(tag,"EVT1-A0 bringup; logs UART0, structured status native USB");
#if CONFIG_EVT1_BOARD_REVIEWED
  configure_radio(UART_NUM_1,evt1::C5_24_TX_FROM_S3,evt1::C5_24_RX_TO_S3,evt1::RADIO_24_CONTROL);
  configure_radio(UART_NUM_2,evt1::C5_58_TX_FROM_S3,evt1::C5_58_RX_TO_S3,evt1::RADIO_58_CONTROL);
  ready[0]=ready[1]=true;
#endif
  std::uint64_t last_health=0;
  while(true) {
    const auto now=static_cast<std::uint64_t>(esp_timer_get_time()/1000);
    std::uint8_t bytes[256];
    for(int i=0;i<2;++i) {
      if(!ready[i])continue;
      if(last_rx_ms[i] && now-last_rx_ms[i]>100) {
        parsers[i].reset_partial();last_rx_ms[i]=0;
      }
      int n=uart_read_bytes(static_cast<uart_port_t>(i+1),bytes,sizeof(bytes),0);
      if(n>0)last_rx_ms[i]=now;
      for(int j=0;j<n;++j) {
        auto frame=parsers[i].push(bytes[j]);
        if(frame) {
          ++frames[i];
          char hex[1025];constexpr char digits[]="0123456789abcdef";
          for(std::size_t at=0;at<frame->size;++at) {
            hex[2*at]=digits[frame->payload[at]>>4];hex[2*at+1]=digits[frame->payload[at]&15];
          }
          hex[frame->size*2]=0;
          char line[1200];
          std::snprintf(line,sizeof(line),"{\"type\":\"raw_frame\",\"radio\":%d,\"transport\":%u,\"bytes\":%u,\"payloadHex\":\"%s\",\"decoded\":false}\n",i,static_cast<unsigned>(frame->transport),static_cast<unsigned>(frame->size),hex);
          send_line(line);
        }
      }
    }
    if(now-last_health>=1000) {
      last_health=now;char line[512];
      std::snprintf(line,sizeof(line),
        "{\"type\":\"health\",\"revision\":\"EVT1-A0\",\"uptimeMs\":%llu,\"boardIoEnabled\":%s,\"rawFrames\":[%llu,%llu],\"gnss\":\"not_initialized\",\"imu\":\"not_initialized\",\"compass\":\"not_initialized\",\"ble\":\"not_implemented\",\"lcd\":\"interface_review_pending\",\"charger\":\"not_initialized\",\"simulated\":false}\n",
        static_cast<unsigned long long>(now),ready[0]?"true":"false",
        static_cast<unsigned long long>(frames[0]),static_cast<unsigned long long>(frames[1]));
      send_line(line);
    }
    vTaskDelay(pdMS_TO_TICKS(10));
  }
}
