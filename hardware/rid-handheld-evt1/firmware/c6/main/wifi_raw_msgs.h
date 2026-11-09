/*
 * Shared P4 <-> C6 raw Wi-Fi command and event definitions.
 */

#ifndef WIFI_RAW_MSGS_H
#define WIFI_RAW_MSGS_H

#include <stdint.h>

#define WIFI_RAW_MSG_SET_PROMISCUOUS 0x0100
#define WIFI_RAW_MSG_SET_CHANNEL     0x0101
#define WIFI_RAW_MSG_SET_FILTER      0x0102
#define WIFI_RAW_MSG_80211_TX        0x0103

#define WIFI_RAW_MSG_CMD_RESPONSE    0x0180
#define WIFI_RAW_MSG_PROMISC_PKT     0x0200

typedef struct {
    uint8_t enable;
} __attribute__((packed)) wifi_raw_cmd_set_promiscuous_t;

typedef struct {
    uint8_t primary;
    uint8_t second;
} __attribute__((packed)) wifi_raw_cmd_set_channel_t;

typedef struct {
    uint32_t filter_mask;
} __attribute__((packed)) wifi_raw_cmd_set_filter_t;

typedef struct {
    uint8_t ifx;
    uint8_t en_sys_seq;
    uint16_t data_len;
    uint8_t data[];
} __attribute__((packed)) wifi_raw_cmd_80211_tx_t;

typedef struct {
    uint16_t cmd_msg_id;
    int32_t status;
} __attribute__((packed)) wifi_raw_cmd_response_t;

typedef struct {
    uint32_t type;
    int8_t rssi;
    uint8_t channel;
    uint8_t rate;
    uint8_t sig_mode;
    uint32_t rx_state;
    uint16_t data_len;
    uint8_t data[];
} __attribute__((packed)) wifi_raw_promisc_pkt_t;

#endif
