#include "rid_core.hpp"
#include "driver/uart.h"
#include "esp_wifi.h"
#include "esp_event.h"
#include "esp_netif.h"
#include "esp_log.h"
#include "freertos/FreeRTOS.h"
#include "freertos/queue.h"
#include "freertos/task.h"
#include "nvs_flash.h"
#include "sdkconfig.h"
#include <algorithm>
#include <cstring>

namespace {
QueueHandle_t queue;
#if CONFIG_EVT1_ENABLE_WIFI_CAPTURE
volatile unsigned dropped=0;
void receive(void* raw,wifi_promiscuous_pkt_type_t type) {
  if(type!=WIFI_PKT_MGMT)return;
  auto* p=static_cast<wifi_promiscuous_pkt_t*>(raw);
  const auto* data=p->payload;
  const std::size_t n=p->rx_ctrl.sig_len;
  if(n<40 || (data[0]!=0x80 && data[0]!=0x50))return;
  // Beacon / Probe Response: 24-byte MAC header, 12 fixed bytes, trailing FCS.
  const auto end=n-4;
  for(std::size_t at=36;at+2<=end;) {
    std::size_t len=data[at+1];
    if(at+2+len>end)return;
    const auto* ie=data+at;
    if(ie[0]==221 && len>=4 && ie[2]==0xfa && ie[3]==0x0b && ie[4]==0xbc
       && (ie[5]==0x0d||ie[5]==0xf0)) {
      rid::RadioFrame f;f.transport=2;
      const std::uint16_t frequency=CONFIG_EVT1_WIFI_CHANNEL<=13?
        2407+5*CONFIG_EVT1_WIFI_CHANNEL:5000+5*CONFIG_EVT1_WIFI_CHANNEL;
      f.payload[0]=static_cast<std::uint8_t>(p->rx_ctrl.rssi);
      f.payload[1]=static_cast<std::uint8_t>(frequency);f.payload[2]=frequency>>8;
      std::memcpy(f.payload.data()+3,data+10,6); // transmitter address
      const auto bytes=std::min<std::size_t>(len+2,512-9);
      std::memcpy(f.payload.data()+9,ie,bytes);f.size=bytes+9;
      if(xQueueSend(queue,&f,0)!=pdTRUE)++dropped;
    }
    at+=len+2;
  }
}
#endif
}
extern "C" void app_main() {
  uart_config_t uart{};uart.baud_rate=921600;uart.data_bits=UART_DATA_8_BITS;
  uart.parity=UART_PARITY_DISABLE;uart.stop_bits=UART_STOP_BITS_1;
  uart.flow_ctrl=UART_HW_FLOWCTRL_DISABLE;uart.source_clk=UART_SCLK_DEFAULT;
  ESP_ERROR_CHECK(uart_param_config(UART_NUM_0,&uart));
  ESP_ERROR_CHECK(uart_set_pin(UART_NUM_0,11,12,UART_PIN_NO_CHANGE,UART_PIN_NO_CHANGE));
  ESP_ERROR_CHECK(uart_driver_install(UART_NUM_0,1024,2048,0,nullptr,0));
  queue=xQueueCreate(32,sizeof(rid::RadioFrame));
  if(!queue)abort();
#if CONFIG_EVT1_ENABLE_WIFI_CAPTURE
  if(CONFIG_EVT1_WIFI_CHANNEL!=6&&CONFIG_EVT1_WIFI_CHANNEL!=149) {
    ESP_LOGE("RID_C5","Initial bringup supports reviewed channels 6 or 149 only");return;
  }
  ESP_ERROR_CHECK(nvs_flash_init());
  ESP_ERROR_CHECK(esp_netif_init());ESP_ERROR_CHECK(esp_event_loop_create_default());
  wifi_init_config_t init=WIFI_INIT_CONFIG_DEFAULT();ESP_ERROR_CHECK(esp_wifi_init(&init));
  ESP_ERROR_CHECK(esp_wifi_set_mode(WIFI_MODE_STA));
  ESP_ERROR_CHECK(esp_wifi_set_country_code(CONFIG_EVT1_COUNTRY_CODE,true));
  ESP_ERROR_CHECK(esp_wifi_set_band_mode(CONFIG_EVT1_WIFI_CHANNEL==149?WIFI_BAND_MODE_5G_ONLY:WIFI_BAND_MODE_2G_ONLY));
  ESP_ERROR_CHECK(esp_wifi_start());
  ESP_ERROR_CHECK(esp_wifi_set_channel(CONFIG_EVT1_WIFI_CHANNEL,WIFI_SECOND_CHAN_NONE));
  wifi_promiscuous_filter_t filter{};filter.filter_mask=WIFI_PROMIS_FILTER_MASK_MGMT;
  ESP_ERROR_CHECK(esp_wifi_set_promiscuous_filter(&filter));
  ESP_ERROR_CHECK(esp_wifi_set_promiscuous_rx_cb(receive));
  ESP_ERROR_CHECK(esp_wifi_set_promiscuous(true));
#else
  ESP_LOGW("RID_C5","Capture disabled pending board review. No synthetic broadcasts or tracks.");
#endif
  while(true) {
    rid::RadioFrame frame;
    if(xQueueReceive(queue,&frame,pdMS_TO_TICKS(1000))==pdTRUE) {
      std::uint8_t wire[520];auto n=rid::encode_frame(frame,wire,sizeof(wire));
      if(n)uart_write_bytes(UART_NUM_0,wire,n);
    }
  }
}
