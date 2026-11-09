# HY-A354TU102GG · 云瞳手持项目选定屏幕

2026-11-09 更新。**保留现有 ESP32-P4-WIFI6-M，先用 HY-A354TU102GG 样品做双通道点屏。** 两份资料足以开始转接板设计和四通道点屏。原规格书第 5 页列出双通道，原规格书第 12–13 页与 V01 第 4 页给出的工作配置是四通道。本批样品的双通道配置和实屏结果待验证。

依据：用户提供的 [原始规格书](references/HY-A354TU102GG.pdf)，共 40 页。PDF 未经修改，以 Git LFS 保存。封面标记为 Preliminary、V1，修订表为 A0 / 2026-04-02；第 37 页内嵌结构图另有 2026-02-28 / Rev.02 标记。这不是已签核的最终承认书。

补充材料为华御 SD5207 点屏说明 V01，共 7 页，版本日期 2026-02-10。原件由团队本地保管，以下记录开发所需参数和页码。第 4 页列出四通道视频时序及点屏电压。第 5 页是上掉电波形。第 6、7 页给出初始化、10 bit 调光和 AOD 切换命令。

## 已核实的规格

| 项目 | 规格书记录 | 位置 |
|---|---|---|
| 厂家 | 深圳市华御智能电子有限公司 / Shenzhen Winfull Intelligent Electronics Co.,Ltd. | 封面 |
| 型号 | HY-A354TU102GG | 封面 |
| 尺寸 / 类型 | 3.54 英寸，AMOLED，LTPS，带 Oncell 触摸 | 第 5、15 页 |
| 分辨率 | **604 × 1024**，不是 640 × 1024 | 第 5、37 页 |
| AA 显示区 | **45.6624 × 77.4144 mm** | 第 5、37 页 |
| 像素间距 / 密度 | 75.6 μm；据此计算约 **336 ppi** | 第 5 页 / 计算 |
| 面板本体 | **47.56 ± 0.15 × 80.11 ± 0.15 mm** | 第 37 页 |
| 本体厚度 | **0.812 ± 0.15 mm**，不含保护膜 | 第 37 页 |
| 展平总包络 | 总表写 **47.56 × 118.07 × 0.812 mm**；结构图为 80.11 mm 面板 + 37.95 ± 0.5 mm 尾部 | 第 5、37 页 |
| 局部器件厚度 | 显示 FPC 器件区最大 1.45 mm；触摸器件区最大 1.05 mm | 第 37 页 |
| 圆角 | 结构图画出圆角轮廓；未标注可直接用于 CAD 的圆角半径或角部像素遮罩 | 第 37 页 |
| 显示驱动 | SD5207，COF | 第 5、37 页 |
| 触摸驱动 | CST3530；I2C 地址记为 0x5A、总线不高于 400 kHz，5 点触控依整机调试 | 第 14 页 |
| 显示接口 | **MIPI DSI**。用户反馈支持 2 lane。原始规格书两处的通道数有差异，V01 第 4 页列出 4 lane 配置。 | 规格书第 5–7、12 页，V01 第 4 页 |
| 模式 / 刷新 | Video mode；Normal 60 Hz、AOD 30 Hz | 第 13 页 |
| 亮度 | 典型 850 cd/m²，标称范围 765–935 cd/m²；以样品为准 | 第 17 页 |

## 对外观与 UI 的影响

1. **118.07 mm 不是刚性屏体高度。** 第 37 页注明 FPC 展平出货，本体高 80.11 mm。不能因此把掌上机直接拉长到 118 mm；也不能把带 COF/器件的排线任意折叠。折弯区域、半径、连接器位置、器件净空需厂家图纸与实物确认。
2. 现有 A1 的黑玻璃是 56.4 × 80.6 mm，A3 旧草案按另一块 55.5 × 84.96 mm 模组估算。新面板更窄，但 A1 玻璃高度与新面板本体只差 0.49 mm，不能当成已有装配余量。旧 82 × 86 / 82 × 90 mm 机身均只保留作比例参考；取得 FPC 折叠包络后再收敛壳体。
3. 保留用户的 CNC 铝框 / SLA 两种材质、正面可见铝边、底部 Type-C、内置 GNSS、平放雷达 / 竖持高度示意。面板圆角与机身三次贝塞尔圆角分别设计，不能相互代用。按键布局仍按最新确认记录推进，不因换屏自行新增触摸必选操作。
4. UI 改为 **604 × 1024 原生画布**。像素数约为旧 320 × 480 的 4.03 倍，但物理字号不会随分辨率自动变大；需要重新排版，不将旧界面非等比拉伸。雷达圆形保持圆形，中文字阶和线宽按毫米与实屏观察确定。
5. AMOLED 的黑底有利于显示区与黑色窗口融合，但仍有边缘结构。精确圆角 R、角部安全区和外观盖板须用厂家 DXF / STEP 与全白点亮样品核对。
6. 第 5 页写含 cover lens，但第 37 页的 0.812 mm 拆分为 POL、Encap、LTPS、泡棉铜箔，未清楚列出独立保护盖板。**不能直接把 0.812 mm 当成已含耐用外盖板的整套外观件厚度**，也不能未经确认重复叠加盖板。

## 双通道可行性和主控方案

**ESP32-P4 的接口、带宽和帧缓冲容量具备验证条件。** 乐鑫标称双通道 D-PHY 每条最高 1.5 Gbit/s，支持视频模式和 RGB888。微雪已为 568 × 1210 的 SD5207 屏发布双通道 ESP-IDF 驱动，驱动支持传入面板专用初始化表和 DPI 时序。该参考的分辨率、默认寄存器与链路速率应按本屏参数适配。[ESP32-P4 数据手册](https://documentation.espressif.com/esp32-p4_datasheet_en.html) · [微雪 SD5207 驱动](https://components.espressif.com/components/waveshare/esp_lcd_sd5207/versions/2.0.0/readme)

| 阶段 | 主控及做法 |
|---|---|
| 实验室点屏 | 沿用现有微雪 ESP32-P4-WIFI6-M，PCB 外形 71.05 × 21 mm，板上带 32 MB PSRAM、双通道 DISPLAY 接口。原理图 J2 为 22 针，点屏用短 FFC 和 39 针屏端转接板，按手头板卡版本核对插座朝向及引脚。 [微雪板卡资料](https://docs.waveshare.com/ESP32-P4-WIFI6) · [原理图](https://files.waveshare.com/wiki/ESP32-P4-WIFI6/ESP32-P4-WIFI6-datasheet.pdf) |
| 轻薄样机 | 双通道点亮后，优先评估 **微雪 ESP32-P4-Core-32MB**。24 × 20 mm 邮票孔核心模组，32 MB PSRAM、32 MB Flash，双通道 DSI 已引出。把模组、屏座、电源及底部 Type-C 布置在同一载板上。载板与接收模组的尺寸、堆叠和功耗通过样机实测。 [核心模组资料](https://docs.waveshare.com/ESP32-P4-Core) |
| 四通道备选 | 广州眺望 **Core-T113-S3，134 针邮票孔版**，40 × 30 mm，原生四通道 DSI 全部引出。先用 T113-S-EVM 和厂商 Linux BSP 验证同一块屏，再把核心板贴焊到便携载板。核心板由 5 V 供电，单节电池方案需增加 5 V 升压，并实测整机功耗。 [核心板手册](https://17575419.s21i.faiusr.com/61/ABUIABA9GAAghOvnuAYovtOh7gc.pdf) · [评估套件](https://www.talowe.com/modules/t113s.html) |

V01 第 4 页的 60 Hz 总时序为 `(604 + 252 + 252 + 8) × (1024 + 10 + 10 + 4) = 1116 × 1048`，像素时钟约 **70.174 MHz**。若双通道沿用同一时序且用 RGB888，按总像素时钟折算约 **842 Mbit/s/通道**。首轮可把 **1,000 Mbit/s/通道**作为留有协议开销余量的测试起点，实际可用速率和时序以样品验证为准。604 × 1024 的 RGB888 单帧约 1.77 MiB，持续 60 Hz 扫屏约需 111 MB/s 的帧缓冲读取带宽。帧缓冲容量充足，连续刷新与无线接收并发时需观察是否欠载。 [乐鑫 DSI 驱动文档](https://docs.espressif.com/projects/esp-idf/en/stable/esp32p4/api-reference/peripherals/lcd/dsi_lcd.html) · [乐鑫 LCD 调试 FAQ](https://docs.espressif.com/projects/esp-faq/en/latest/software-framework/peripherals/lcd.html)

以微雪验证过的 ESP-IDF v5.5.5 为台架基线，按实板芯片版本选 BSP 配置。设置 DPI 目标 70.174 MHz 时，默认 240 MHz 时钟经整数分频后内部 DPI 为 80 MHz，驱动会补偿内部行时序，并按目标时钟配置 DSI 发送时序。调试时同时记录内部时钟、实际 DSI 速率和帧率。该版本默认用带同步脉冲的 burst 模式，V01 只给出 Video mode。 [微雪 BSP 配置](https://github.com/waveshareteam/ESP32-P4-Platform/blob/main/docs/GETTING_STARTED.md) · [ESP-IDF 默认时钟](https://github.com/espressif/esp-idf/blob/v5.5.5/components/soc/esp32p4/include/soc/clk_tree_defs.h#L382-L392) · [时序补偿](https://github.com/espressif/esp-idf/blob/v5.5.5/components/hal/mipi_dsi_hal.c#L218-L250) · [视频模式](https://github.com/espressif/esp-idf/blob/v5.5.5/components/esp_lcd/dsi/esp_lcd_panel_dpi.c#L282-L317)

## 点屏和转接板

双通道转接板从现有 P4 的 22 针 DISPLAY 口接屏端 39 针座，首轮按 CLK、D0 和 D1 走线，座子方向按样品核对。DSI 差分线走短 FFC 和受控阻抗 PCB。屏端第 10 脚预留为空，第 38 脚引出测试焊盘并核对样品电路后再决定是否驱动。另一个同分辨率、同驱动 IC 的模组把第 10 脚定义为可留空的编程电源，第 38 脚定义为 VBAT 使能，可用于辅助排查。 [TOH360XVT-01C 规格书第 6 页](https://tailorpixels.com/wp-content/uploads/2026/08/TOH360XVT-01C_3.6-inch-AMOLED-with-On-Cell-Touch-604%C3%971024-MIPI.pdf#page=6)

下表是 **屏端** 规格书第 8 页的工作电源，典型值与 V01 第 4 页一致。RESX 按 1.8 V 逻辑驱动，P4 主机的 D-PHY 按原理图和 BSP 单独配置 2.5 V。

| 电源域 | 最小 / 典型 / 最大 |
|---|---|
| VDDI | 1.65 / **1.8** / 1.95 V |
| VCI | 2.65 / **2.8** / 3.6 V |
| VBAT（面板 PMIC） | 2.9 / **3.7** / 4.5 V |

1. 用微雪 BSP 和已知正常的 DSI 屏跑通板卡作对照。接 HY-A354TU102GG 时按 V01 的 VDDIO → VCI → VBAT → 释放 RESX 顺序上电，在屏端实测电压与复位。
2. 参考微雪 SD5207 的 DBI/DPI 驱动结构，按原规格书第 13 页用 LP 模式发送本屏的 V01 命令表。首轮可在释放 RESX 后留 120 ms，覆盖原规格书第 11 页的复位等待。发 `0x11` 后再等 120 ms 发 `0x29`。用 `esp_lcd_dpi_panel_set_pattern` 输出硬件色条，检查色序、行同步和四角。 [ESP-IDF 色条接口](https://docs.espressif.com/projects/esp-idf/en/stable/esp32p4/api-reference/peripherals/lcd/dsi_lcd.html#_CPPv429esp_lcd_dpi_panel_set_pattern22esp_lcd_panel_handle_t23mipi_dsi_pattern_type_t)
3. 色条通过后切到 PSRAM 帧缓冲，在原生分辨率下做 10 次完整上下电和 30 分钟连续刷新，记录帧率、闪屏及欠载日志。最后接入 UI 与 RID 接收测并发、功耗及温升。触摸和 AOD 在正常视频通过后分别验证。 [CST3530 参考驱动](https://components.espressif.com/components/viewesmart/esp_lcd_touch_cst3530/versions/1.0.2/readme)

**主控切换条件。** 双通道稳定通过后，再按 P4 核心模组画便携载板。双通道黑屏时先排查供电、使能、复位、差分映射和实际视频时序。如果同一块屏用 V01 在四通道参考台架稳定工作，现有 P4 的 DSI 输出已核实，双通道仍无法满足稳定性要求，则切换到 T113-S3。

便携载板在同一片 PCB 上布置供电、显示和接收连接。先实测面板 FPC 折叠、盖板、屏座和电池的总叠层，再确定整机厚度。P4 承担显示、UI 和数据汇聚，RID 无线接收按项目的 C5 / BLE 方案单独验证。

## 样品和资料需核对的项目

| 编号 | 资料中的问题 | 需要的确认 |
|---|---|---|
| D01 | 规格书第 5 页列双通道，V01 第 4 页为四通道配置 | 用样品验证双通道的数据对、每通道速率、视频子模式和时序，记录 V01 初始化的适用性。可用同批次参考配置直接复现。 |
| D02 | 第 6 页 pin 10 / 38 为 NC；第 37 页分别为 MTP_PWR / EN | 最终 39 pin 定义、NC/EN/MTP_PWR 处置与未使用数据 lane 的连接要求 |
| D03 | 第 5 页与第 37 页对本体/展平包络的口径不同；无精确圆角 R 与弯折规范 | 受控 DXF / STEP、AA 角部轮廓、推荐折叠形态、禁弯区、最小弯曲半径与公差 |
| D04 | 第 5 页称含 cover lens，结构图没有清晰的独立外盖板层 | 实际交货是否含外保护玻璃、材质、厚度、触摸叠层及可贴合区域 |
| D05 | 第 6 页推荐插座名称区分 ZIF / Finger；第 37 页仅写 OK-F302-39115 | 主板座完整订货号、触点面、FPC / 连接器封装图与样品 |
| D06 | VCI 典型 2.8 V，结构图标 3.3 V；触摸 IO 也有不同配置标注，缺功耗 | 实际交货电源配置、触摸 IO 电平、典型/峰值电流、亮度档位、关机漏电与上下电延时 |

## 状态与资料来源

- 已完成资料核对、V01 归档和主控纸面评估。待制作点屏转接板，验证双通道实屏、整机功耗和结构试装。
- A1 / A2 模型和 A3 旧二维图继续作为历史参考，不冒充此屏的新结构模型。
- 规格书和 V01 文件的 SHA-256 见 [display-spec.json](display-spec.json)。
