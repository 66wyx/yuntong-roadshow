#include <stdbool.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

#include "esp_err.h"
#include "esp_log.h"
#include "esp_wifi.h"
#include "freertos/FreeRTOS.h"
#include "freertos/event_groups.h"

#include "esp_hosted_peer_data.h"
#include "wifi_raw_msgs.h"
#include "wifi_raw_slave.h"

static const char *TAG = "wifi_raw_slave";
static EventGroupHandle_t s_ready_event;
static esp_err_t s_wifi_status = ESP_ERR_INVALID_STATE;
static bool s_promiscuous;

#define WIFI_RAW_READY_BIT BIT0

static esp_err_t wait_wifi_ready(void)
{
    if (!s_ready_event) {
        return ESP_ERR_INVALID_STATE;
    }

    EventBits_t bits = xEventGroupWaitBits(
        s_ready_event, WIFI_RAW_READY_BIT, pdFALSE, pdTRUE,
        pdMS_TO_TICKS(4500));
    if (!(bits & WIFI_RAW_READY_BIT)) {
        ESP_LOGE(TAG, "Wi-Fi initialization timed out");
        return ESP_ERR_TIMEOUT;
    }
    return s_wifi_status;
}

static void send_status(uint32_t cmd_msg_id, esp_err_t status)
{
    wifi_raw_cmd_response_t response = {
        .cmd_msg_id = (uint16_t)cmd_msg_id,
        .status = status,
    };
    esp_err_t ret = esp_hosted_send_custom_data(
        WIFI_RAW_MSG_CMD_RESPONSE,
        (const uint8_t *)&response,
        sizeof(response));
    if (ret != ESP_OK) {
        ESP_LOGE(TAG,
                 "Failed to send status for 0x%04x: %s",
                 cmd_msg_id,
                 esp_err_to_name(ret));
    }
}

static void promiscuous_rx(void *buffer, wifi_promiscuous_pkt_type_t type)
{
    if (!buffer || !s_promiscuous) {
        return;
    }

    const wifi_promiscuous_pkt_t *packet =
        (const wifi_promiscuous_pkt_t *)buffer;
    const uint32_t length = packet->rx_ctrl.dump_len
                                ? packet->rx_ctrl.dump_len
                                : packet->rx_ctrl.sig_len;
    if (packet->rx_ctrl.rx_state != 0 || length < 24 || length > 2304) {
        return;
    }

    size_t total = sizeof(wifi_raw_promisc_pkt_t) + length;
    wifi_raw_promisc_pkt_t *event = malloc(total);
    if (!event) {
        return;
    }

    event->type = (uint32_t)type;
    event->rssi = (int8_t)packet->rx_ctrl.rssi;
    event->channel = (uint8_t)packet->rx_ctrl.channel;
    event->rate = (uint8_t)packet->rx_ctrl.rate;
    event->sig_mode = 0;
    event->rx_state = packet->rx_ctrl.rx_state;
    event->data_len = (uint16_t)length;
    memcpy(event->data, packet->payload, length);

    esp_err_t ret = esp_hosted_send_custom_data(
        WIFI_RAW_MSG_PROMISC_PKT, (const uint8_t *)event, total);
    if (ret != ESP_OK) {
        ESP_LOGW(TAG, "Dropping packet: %s", esp_err_to_name(ret));
    }
    free(event);
}

static void on_set_promiscuous(uint32_t msg_id,
                               const uint8_t *data,
                               size_t data_len)
{
    esp_err_t ret = wait_wifi_ready();
    if (ret == ESP_OK) {
        if (data_len != sizeof(wifi_raw_cmd_set_promiscuous_t)) {
            ret = ESP_ERR_INVALID_SIZE;
        } else {
            const wifi_raw_cmd_set_promiscuous_t *cmd =
                (const wifi_raw_cmd_set_promiscuous_t *)data;
            if (cmd->enable) {
                ret = esp_wifi_set_promiscuous_rx_cb(promiscuous_rx);
                if (ret == ESP_OK) {
                    ret = esp_wifi_set_promiscuous(true);
                }
                s_promiscuous = ret == ESP_OK;
            } else {
                s_promiscuous = false;
                ret = esp_wifi_set_promiscuous(false);
            }
        }
    }
    ESP_LOGI(TAG,
             "promiscuous enable=%d status=%s",
             data_len ? data[0] : -1,
             esp_err_to_name(ret));
    send_status(msg_id, ret);
}

static void on_set_channel(uint32_t msg_id,
                           const uint8_t *data,
                           size_t data_len)
{
    esp_err_t ret = wait_wifi_ready();
    if (ret == ESP_OK) {
        if (data_len != sizeof(wifi_raw_cmd_set_channel_t)) {
            ret = ESP_ERR_INVALID_SIZE;
        } else {
            const wifi_raw_cmd_set_channel_t *cmd =
                (const wifi_raw_cmd_set_channel_t *)data;
            ret = esp_wifi_set_channel(
                cmd->primary, (wifi_second_chan_t)cmd->second);
        }
    }
    ESP_LOGI(TAG,
             "channel primary=%d second=%d status=%s",
             data_len >= 1 ? data[0] : -1,
             data_len >= 2 ? data[1] : -1,
             esp_err_to_name(ret));
    send_status(msg_id, ret);
}

static void on_set_filter(uint32_t msg_id,
                          const uint8_t *data,
                          size_t data_len)
{
    esp_err_t ret = wait_wifi_ready();
    if (ret == ESP_OK) {
        if (data_len != sizeof(wifi_raw_cmd_set_filter_t)) {
            ret = ESP_ERR_INVALID_SIZE;
        } else {
            const wifi_raw_cmd_set_filter_t *cmd =
                (const wifi_raw_cmd_set_filter_t *)data;
            wifi_promiscuous_filter_t filter = {
                .filter_mask = cmd->filter_mask,
            };
            ret = esp_wifi_set_promiscuous_filter(&filter);
        }
    }
    ESP_LOGI(TAG, "filter status=%s", esp_err_to_name(ret));
    send_status(msg_id, ret);
}

static void on_80211_tx(uint32_t msg_id,
                        const uint8_t *data,
                        size_t data_len)
{
    esp_err_t ret = wait_wifi_ready();
    if (ret == ESP_OK) {
        if (data_len < sizeof(wifi_raw_cmd_80211_tx_t)) {
            ret = ESP_ERR_INVALID_SIZE;
        } else {
            const wifi_raw_cmd_80211_tx_t *cmd =
                (const wifi_raw_cmd_80211_tx_t *)data;
            if (cmd->data_len == 0 ||
                data_len < sizeof(*cmd) + cmd->data_len) {
                ret = ESP_ERR_INVALID_SIZE;
            } else {
                ret = esp_wifi_80211_tx(
                    (wifi_interface_t)cmd->ifx,
                    data + sizeof(*cmd),
                    cmd->data_len,
                    cmd->en_sys_seq != 0);
            }
        }
    }
    ESP_LOGI(TAG, "80211_tx status=%s", esp_err_to_name(ret));
    send_status(msg_id, ret);
}

static esp_err_t initialize_wifi(void)
{
    wifi_init_config_t config = WIFI_INIT_CONFIG_DEFAULT();
    esp_err_t ret = esp_wifi_init(&config);
    if (ret != ESP_OK) {
        return ret;
    }

    ret = esp_wifi_set_storage(WIFI_STORAGE_RAM);
    if (ret == ESP_OK) {
        ret = esp_wifi_set_mode(WIFI_MODE_STA);
    }
    if (ret == ESP_OK) {
        ret = esp_wifi_set_ps(WIFI_PS_NONE);
    }
    if (ret == ESP_OK) {
        ret = esp_wifi_start();
    }
    return ret;
}

esp_err_t wifi_raw_slave_init(void)
{
    s_ready_event = xEventGroupCreate();
    if (!s_ready_event) {
        return ESP_ERR_NO_MEM;
    }

    esp_err_t ret = esp_hosted_register_custom_callback(
        WIFI_RAW_MSG_SET_PROMISCUOUS, on_set_promiscuous);
    if (ret == ESP_OK) {
        ret = esp_hosted_register_custom_callback(
            WIFI_RAW_MSG_SET_CHANNEL, on_set_channel);
    }
    if (ret == ESP_OK) {
        ret = esp_hosted_register_custom_callback(
            WIFI_RAW_MSG_SET_FILTER, on_set_filter);
    }
    if (ret == ESP_OK) {
        ret = esp_hosted_register_custom_callback(
            WIFI_RAW_MSG_80211_TX, on_80211_tx);
    }
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Callback registration failed: %s", esp_err_to_name(ret));
        s_wifi_status = ret;
        xEventGroupSetBits(s_ready_event, WIFI_RAW_READY_BIT);
        return ret;
    }

    ESP_LOGI(TAG, "Raw Wi-Fi handlers registered");
    s_wifi_status = initialize_wifi();
    xEventGroupSetBits(s_ready_event, WIFI_RAW_READY_BIT);
    if (s_wifi_status != ESP_OK) {
        ESP_LOGE(TAG, "Wi-Fi initialization failed: %s",
                 esp_err_to_name(s_wifi_status));
        return s_wifi_status;
    }

    ESP_LOGI(TAG, "Raw Wi-Fi ready in station mode");
    return ESP_OK;
}
