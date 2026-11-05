"""Decode a text/JSONL capture of raw IEEE 802.11 Beacon/Probe Response frames."""

import argparse
import json
import sys

import rid_decoder
import rid_state


def parse_line(line):
    text = line.strip()
    if not text:
        return None
    if text.startswith("{"):
        return json.loads(text)
    return {"frameHex": text}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", help="hex/JSONL file, or - for stdin")
    parser.add_argument("--rssi", type=int, default=None)
    parser.add_argument("--channel", type=int, default=None)
    args = parser.parse_args()

    stream = open(args.input, encoding="utf-8") if args.input != "-" else sys.stdin
    store = rid_state.TargetStore()
    default_time = 0
    for line_number, line in enumerate(stream, 1):
        try:
            record = parse_line(line)
            if record is None:
                continue
            frame = bytes.fromhex(record["frameHex"].replace(":", "").replace(" ", ""))
            now_ms = int(record.get("receivedMs", default_time))
            default_time = max(default_time, now_ms + 1000)
            rssi = record.get("rssiDbm", args.rssi)
            channel = record.get("channel", args.channel)
            observations = rid_decoder.decode_wifi_frame(
                frame, rssi=rssi, channel=channel, now_ms=now_ms
            )
            if not observations:
                print(
                    json.dumps(
                        {"line": line_number, "ok": False, "reason": "no_rid_ie"},
                        ensure_ascii=False,
                    )
                )
                continue
            for observation in observations:
                target = store.apply(observation, now_ms)
                output = {
                    "line": line_number,
                    "ok": True,
                    "observation": observation,
                    "targetState": store.state(target, now_ms),
                }
                print(json.dumps(output, ensure_ascii=False, separators=(",", ":")))
        except Exception as error:
            print(
                json.dumps(
                    {
                        "line": line_number,
                        "ok": False,
                        "reason": type(error).__name__,
                        "error": str(error),
                    },
                    ensure_ascii=False,
                )
            )
    if stream is not sys.stdin:
        stream.close()


if __name__ == "__main__":
    main()
