**EVT1 固件工程**

`core/` 是实际可在主机编译运行的逻辑：姿态切换、WGS84 相对位置、视图方向轴、逐字段位置时效、充电状态解释和带 CRC 的模组间数据帧。主机测试结果写入 `../validation/`。

`s3/` 和 `c5/` 为 ESP-IDF 启动/接收骨架。当前环境没有 ESP-IDF 工具链，不能把主机测试通过当成 ESP-IDF 编译通过。预期先以支持 S3/C5 的统一 ESP-IDF 版本进行构建并固定依赖版本，之后才进行实板验证。

S3 默认只发送真实的初始化状态。GNSS、IMU、罗盘、电量、LCD、BLE 以及 RID 业务解码尚未接入，均明确标为未初始化或未实现，不输出模拟飞机、模拟 GPS 或模拟充电百分比。`EVT1_BOARD_REVIEWED` 关闭时不配置未校核的板级输出。

C5 骨架提供被动 Beacon/Probe Response 报文筛选与队列化串口输出，默认关闭接收。启用前必须完成对应硬件上电审查、天线连接及目标 SDK/信道 API 验证。5.8 GHz 的 band-mode 配置与实际驱动需在首次 ESP-IDF 构建/实机时核对；NAN 与 BLE 不在此接收实现中。代码没有发送或模拟空中 RID 广播的功能。

串口统一为 921600、8N1。C5 UART0 使用 GPIO11 TX / GPIO12 RX，日志放 USB Serial/JTAG，ROM 启动日志由主控帧解析器重新同步。100 ms 空闲后丢弃未完成帧。S3 导出原始帧十六进制数据，并明确 `decoded:false`；此阶段不把原始信息元素当成业务目标。

后续驱动顺序：电源状态只读回读 → LCD 厂家接口确认及显示测试 → GNSS 与传感器驱动 → 国际/国标业务解码 → BLE 接收 → 实机组合运行。GPIO 初表为工程分配，原理图未审查前不得把该表当作制造已冻结结果。

## ESP32-P4 / ESP32-C6 台架验证

`p4/` 是连接 P4 内置 C6、监听 Wi-Fi 管理帧、解码 ASTM/OpenDroneID 与
GB 46750-2025，并驱动 ILI9341 雷达/高度页面的台架固件。`c6/` 包含
promiscuous 捕获和 raw 802.11 发送的 custom RPC 支持；`c6-ota/` 通过
P4 到 C6 的 SDIO OTA 安装对应 C6 镜像。`p4-prototype/` 保留 MicroPython
屏幕、触摸和协议回放验证脚本。

2026-11-05 真实空口闭环已通过。PC 上的 MT7612U 用 Windows 自带驱动，
以 Wi-Fi Direct Beacon 发送合成 RID（[`../tools/virtual-rid-tx/windows_wfd_tx.py`](../tools/virtual-rid-tx/windows_wfd_tx.py)），
P4/C6 在信道 11 接收。结果：

- 圆周航线 8 个位置连续两轮全部收到；
- GB 46750 与 ASTM 均正确解码，`LAB-TEST-001`，XYZ 与发射值一致；
- ILI9341 新 UI 上目标随航线移动，已人工目视确认。

这条路径不是原计划的 Linux monitor 注入，`mt76x2u` 在 QEMU 中仍探测失败。
它也只证明台架合成信号能收到，不代表已兼容真实无人机。完整证据、
测量数据和限制见
[`../validation/REAL_AIR_LOOPBACK_HANDOFF.md`](../validation/REAL_AIR_LOOPBACK_HANDOFF.md)。
固件构建、主机检查和 UI 说明见 [`p4/README.md`](p4/README.md)。
