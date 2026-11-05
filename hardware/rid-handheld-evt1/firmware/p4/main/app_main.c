#include <inttypes.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

#include "esp_event.h"
#include "esp_hosted.h"
#include "esp_log.h"
#include "esp_timer.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "nvs_flash.h"

#include "ili9341.h"
#include "rid_decoder.h"
#include "rid_geo.h"
#include "rid_runtime.h"
#include "rid_ui.h"
#include "wifi_raw.h"

#define CAPTURE_CHANNEL 6

static const char *TAG = "rid_rx";
static volatile uint32_t s_mgmt_frames;
static volatile uint32_t s_rid_frames;
static volatile uint32_t s_decoded_frames;
static bool s_display_ready;
static rid_target_snapshot_t s_ui_targets[RID_RUNTIME_MAX_TARGETS];

static void print_hex(const uint8_t *data, size_t length)
{
    for (size_t i = 0; i < length; i++) {
        printf("%02x", data[i]);
    }
    printf("\n");
}

static void receive_packet(const wifi_raw_rx_pkt_t *packet)
{
    if (packet->type != 0 || packet->payload_len < 38) {
        return;
    }
    const uint8_t *frame = packet->payload;
    const uint8_t subtype = (frame[0] >> 4) & 0x0F;
    if (subtype != 5 && subtype != 8) {
        return;
    }
    s_mgmt_frames++;

    bool has_rid = false;
    uint8_t vendor_type = 0;
    size_t offset = 36;
    while (offset + 2 <= packet->payload_len) {
        const uint8_t element_id = frame[offset];
        const uint8_t element_length = frame[offset + 1];
        const size_t end = offset + 2 + element_length;
        if (end > packet->payload_len) {
            break;
        }
        if (element_id == 221 && element_length >= 4 &&
            frame[offset + 2] == 0xFA &&
            frame[offset + 3] == 0x0B &&
            frame[offset + 4] == 0xBC &&
            (frame[offset + 5] == 0x0D || frame[offset + 5] == 0xF0)) {
            has_rid = true;
            vendor_type = frame[offset + 5];
            break;
        }
        offset = end;
    }
    if (!has_rid) {
        return;
    }

    s_rid_frames++;
    printf(
        "RID_FRAME type=%02x subtype=%u ch=%u rssi=%d len=%u now_ms=%" PRIu64 " hex=",
        vendor_type,
        subtype,
        packet->channel,
        packet->rssi,
        packet->payload_len,
        (uint64_t)(esp_timer_get_time() / 1000));
    print_hex(frame, packet->payload_len);
    fflush(stdout);

    rid_observation_t observation;
    if (rid_decode_frame(frame,
                         packet->payload_len,
                         packet->rssi,
                         packet->channel,
                         &observation)) {
        const uint64_t now_ms = (uint64_t)(esp_timer_get_time() / 1000);
        s_decoded_frames++;
        rid_runtime_apply(&observation, now_ms);
        /* XYZ is receiver east/north/up; up uses the same WGS84 datum. */
        const rid_enu_t enu =
            rid_geo_to_enu(&rid_receiver_anchor, &observation);
        printf(
            "RID_TARGET protocol=%s id=%s mac=%02x:%02x:%02x:%02x:%02x:%02x "
            "lat=%.7f lon=%.7f alt=%.1f height=%.1f track=%.0f "
            "xyz=%.1f,%.1f,%.1f",
            observation.protocol,
            observation.identity_valid ? observation.uas_id : "-",
            observation.source_mac[0],
            observation.source_mac[1],
            observation.source_mac[2],
            observation.source_mac[3],
            observation.source_mac[4],
            observation.source_mac[5],
            observation.latitude,
            observation.longitude,
            observation.altitude_geo_m,
            observation.height_m,
            observation.direction_valid ? observation.direction_deg : -1.0,
            enu.east_m,
            enu.north_m,
            enu.up_m);
        if (!observation.position_valid) {
            printf(" position=invalid");
        }
        if (!enu.up_valid) {
            printf(" up=unknown");
        }
        printf("\n");
        fflush(stdout);
    }
}

static void render_ui(rid_ui_page_t page, uint64_t now_ms)
{
    const rid_ui_frame_t frame = {
        .page = page,
        .now_ms = now_ms,
        .stats = {
            .channel = CAPTURE_CHANNEL,
            .mgmt_frames = s_mgmt_frames,
            .rid_frames = s_rid_frames,
            .decoded_frames = s_decoded_frames,
        },
        .targets = s_ui_targets,
        .target_count = rid_runtime_snapshot(
            now_ms, s_ui_targets, RID_RUNTIME_MAX_TARGETS),
    };
    rid_ui_draw(ili9341_canvas(), &frame);
    ili9341_flush();
}

static void start_capture(void)
{
    ESP_LOGI(TAG, "Initializing ESP-Hosted");
    ESP_ERROR_CHECK(esp_hosted_init());
    ESP_LOGI(TAG, "Connecting to C6 over SDIO");
    ESP_ERROR_CHECK(esp_hosted_connect_to_slave());

    ESP_ERROR_CHECK(wifi_raw_init());
    wifi_raw_register_rx_cb(receive_packet);

    ESP_LOGI(TAG, "Setting channel %d", CAPTURE_CHANNEL);
    ESP_ERROR_CHECK(wifi_raw_set_channel(CAPTURE_CHANNEL, 0));
    ESP_LOGI(TAG, "Filtering management frames");
    ESP_ERROR_CHECK(wifi_raw_set_filter(1));
    ESP_LOGI(TAG, "Enabling promiscuous mode");
    ESP_ERROR_CHECK(wifi_raw_set_promiscuous(true));
    ESP_LOGI(TAG, "RID capture active on channel %d", CAPTURE_CHANNEL);
}

void app_main(void)
{
    esp_err_t status = nvs_flash_init();
    if (status == ESP_ERR_NVS_NO_FREE_PAGES ||
        status == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        ESP_ERROR_CHECK(nvs_flash_erase());
        status = nvs_flash_init();
    }
    ESP_ERROR_CHECK(status);

    status = esp_event_loop_create_default();
    if (status != ESP_OK && status != ESP_ERR_INVALID_STATE) {
        ESP_ERROR_CHECK(status);
    }

    s_display_ready = ili9341_init();
    if (s_display_ready) {
        /* Show the listening screen while ESP-Hosted connects. */
        render_ui(RID_UI_RADAR, (uint64_t)(esp_timer_get_time() / 1000));
    } else {
        ESP_LOGE(TAG, "Display unavailable; continuing with UART output");
    }
    start_capture();

    uint64_t last_render_ms = 0;
    uint64_t last_page_switch_ms = 0;
    uint64_t last_stats_ms = 0;
    uint32_t last_render_us = 0;
    rid_ui_page_t page = RID_UI_RADAR;
    while (true) {
        const uint64_t now_ms = (uint64_t)(esp_timer_get_time() / 1000);
        if (s_display_ready && now_ms - last_render_ms >= 250) {
            const int64_t render_start_us = esp_timer_get_time();
            render_ui(page, now_ms);
            last_render_us = (uint32_t)(esp_timer_get_time() - render_start_us);
            last_render_ms = now_ms;
        }
        if (now_ms - last_page_switch_ms >= 5000) {
            page = page == RID_UI_RADAR ? RID_UI_HEIGHT : RID_UI_RADAR;
            last_page_switch_ms = now_ms;
        }
        if (now_ms - last_stats_ms >= 5000) {
            ESP_LOGI(
                TAG,
                "stats mgmt=%" PRIu32 " rid=%" PRIu32 " decoded=%" PRIu32
                " ui_us=%" PRIu32,
                s_mgmt_frames,
                s_rid_frames,
                s_decoded_frames,
                last_render_us);
            last_stats_ms = now_ms;
        }
        vTaskDelay(pdMS_TO_TICKS(50));
    }
}
