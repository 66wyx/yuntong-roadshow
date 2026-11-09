# 云瞳 RID 掌上接收器 · Claude 接手 README

> **2026-11-06 CAD 交付更新：** [V4 整体原生 STEP](hardware/rid-handheld-rig-p1/v4/step/yuntong-rig-p1-v4-native-assembly.stp) 已按 V4 参数用 CadQuery/OpenCascade 重建，14 个结构实体，含真实圆柱面、圆弧、倒圆和精确贝塞尔几何；未读取 STL。该 STEP 为当前 CAD 交付，旧 82.8 MB 的网格转换 STEP 不再是推荐入口。原生源脚本在 V4 `scripts/native_*.py`，导出入口 `09_export_native_assembly.py`，记录为 `validation/native-cad-export.json`。Blender 展示模型与旧 STL 尚未从新的 CAD 主模型重新派生，修改结构应先改 CAD 源，再更新显示/打印派生文件。

2026-11-05 更新。**当前先验证照片中的细长 ESP32-P4-WIFI6 带排针版 + MSP2834 2.8 英寸 SPI 屏。用户指定所有线材焊接、屏幕总高 14 mm、板总高 14.5 mm、底部居中 Type-C 面板延长线、总厚度不超过 28 mm。** 已完成 [RIG-P1 V4 结构试装文件](hardware/rid-handheld-rig-p1/v4/README.md)：外壳 27 mm，包含按键 27.7 mm。先阅读 V4；本文件下方的 HY-A354TU102GG / T113 路线及 2026-10-30 Blender 快照均属于后续或历史资料，不再作为当前验证步骤。

## 1. 先读这段：当前要接手什么

项目目录：`C:/Users/YX/Documents/云台检测`。

项目仓库：[66wyx/yuntong-roadshow](https://github.com/66wyx/yuntong-roadshow)，当前结构分支：`codex/rig-p1-printable-shell`，继承 `codex/yuntong-handheld`。模型和硬件 PDF 使用 Git LFS。V4 Blender 文件已保存，场景 `RIG_P1_V4_Print`；保留历史场景，不要重建覆盖。

当前优先读取 [V4 说明、文件及验证边界](hardware/rid-handheld-rig-p1/v4/README.md)。旧 A3 二维包络与后续 HY-A354TU102GG 不参与这套 2.8 英寸测试壳的尺寸计算。V4 13 种 STL 已独立检查；实体与简化硬件 178 对包络检查通过，未实物打印或装配。Type-C 尾套与弯头部分尺寸仍为截图推定，应先打 P13 接口试装片。

当前重点是 **云瞳 RID 掌上接收器的工业设计、屏幕选型、天线/GNSS 布置及样机实现**。同目录还有 UAVGuard 双摄视觉监测系统，属于关联项目，不是本轮需要重写的对象。

最重要的状态：

- **外观优先级最高。** 用户要求先看设计、比例、材质与交互，再落实器件装配。
- **不采用 CoreS3。** 从定制掌上机方案直接验证。
- **当前测试屏：MSP2834 2.8 英寸 SPI，配现有细长 P4 板。** 用户已选择的 HY-A354TU102GG 保留为后续 3.54 英寸路线，不能据此再次跳过现有器件验证。
- **A1 是当前重要的比例参考，A2 是已有的包覆铝壳/贝塞尔圆角参考。** 不能简单把 A2 当成当前已定稿的整机，也不能因为用户喜欢 A1 比例就恢复其全部旧结构。
- 最新测试壳按用户重新引用的 **A1 左屏右列正面按键** 完成，全打印；底部 Type-C 改用居中延长座。早先竖式/侧键两材质概念图保留为历史外观研究。
- **外接天线、GNSS 具体料号及内外天线切换仍是讨论建议。** 上一轮助手的建议不等于用户已冻结的要求。
- 现有 `.blend`、`.glb` 和生成图片主要是外观资产；没有完成量产结构、完整 PCB、电源和射频验收。
- **RID 接收台架闭环已于 2026-11-05 通过**（ESP32-P4 + C6 + ILI9341，非掌上机最终硬件）：
  - 电脑 MT7612U 通过 Windows Wi-Fi Direct 发送合成 RID，P4 能解码 GB 46750 与 ASTM，位置随航线变化，屏幕显示已目视确认；
  - 尚未接收过真实无人机。

  见 [真实空口闭环记录](hardware/rid-handheld-evt1/validation/REAL_AIR_LOOPBACK_HANDOFF.md) 与 [P4 固件](hardware/rid-handheld-evt1/firmware/p4/README.md)。

建议阅读顺序：V4 README → V4 Blender/主图与接口试装片 → 本文件的历史背景 → 后续新屏资料。不要把老版 32/37 mm 壳体当作当前打印文件。

## 2. 用户要求与优先级

| 项目 | 用户明确要求 / 当前处理原则 |
|---|---|
| 产品定位 | 先做实验室便携演示；另有系统部署版路线。掌上机要小巧，不要直接做成手机大小的开发板盒子 |
| 外观 | Rams / Braun 式极简、功能主义；克制的几何、灰白/银色哑光、精密小接缝 |
| 材质 A | CNC 铝合金框体 + 光固化打印前后盖；保留金属触感与正面可见铝边 |
| 材质 B | 同一构型的全光固化打印外壳，便于对比与验证 |
| 金属结构 | 曾明确取消上下盖压住中框的包夹外观，改为铝壳包围正面、打印面板内嵌。后续材质组合没有明确要求恢复夹层外观 |
| 四角 | iPhone 直板机观感的三次贝塞尔连续圆角；已有原创曲线，不能称为苹果原厂 CAD |
| 色彩 | 机身中性；一个有功能的彩色焦点。最近组合采用橙色圆形确认/锁定键 |
| 字标 | 少量、小号、严格对齐的 Helvetica 风格黑字；最终字体文件、授权与中文回退仍需确认 |
| 接口 | **底部 Type-C 充电**；原工程进一步提出 USB 数据、边充边用、关机充电，但这些电路还未验证 |
| 当前屏幕 | MSP2834 2.8 英寸 SPI，用户给出总高 14 mm；先配细长 ESP32-P4-WIFI6。后续 HY-A354TU102GG 另行适配。 |
| 视图 | 平放：雷达式俯视，表示目标方位与距离；竖持：高度/2.5D 空间示意，表示大概相对高度 |
| 定位 | 机内 GNSS；IMU 判断持握姿态，地磁辅助静止朝向 |
| 展示 | 安静的浅灰/暖米色影棚、柔光、深景深、正交或轻微侧角；旧 A1 暗背景渲染用于比例参考，不强制沿用照明 |

早期参考中的七格标记、刻纹、分隔槽等已经建模保留；后来的 Rams 简化方向优先级更高。不要为了“保留每个早期细节”重新堆装饰，也不要未经说明删除关键功能按钮。

## 3. 版本、模型与图片地址

文档链接使用仓库相对路径，便于在 GitHub 和新电脑打开；代码示例中保留的 Windows 本机路径需按新目录调整。

| 版本 | 入口 | 状态与用途 |
|---|---|---|
| RIG-P1 V4 | [当前结构 README](hardware/rid-handheld-rig-p1/v4/README.md) | 焊线、居中面板 Type-C、27.7 mm 名义总厚度；Blender/GLB/STL，待打印试装 |
| EVT1-A0 | [工程 README](hardware/rid-handheld-evt1/README.md) | 2.4 英寸时期的器件包络、CAD、GPIO、电源架构及固件骨架；壳体与布局已过时 |
| ID-A1 | [A1 README](hardware/rid-handheld-id-a1/README.md) | 82 × 86 × 20 mm 外观目标；长黑玻璃、右列正面按键、CNC 中框与打印盖；用户最新重新偏好的比例参考 |
| ID-A2 | [A2 README](hardware/rid-handheld-id-a2/README.md) | 64 × 54 × 20 mm、2 英寸方屏、正面包覆铝壳与连续贝塞尔四角；不是最终 3.5 英寸方案 |
| 当前屏幕 | [HY-A354TU102GG](hardware/display-hy-a354tu102gg/README.md) | 已由用户选定；原始 PDF 和结构/电气核对记录，尚未点亮样品或更新模型 |
| ID-A3 | [A3 README](hardware/rid-handheld-id-a3/README.md) | 旧 320 × 480 屏的二维包络与 UI 草案；没有对应新 Blender 模型，需按选定屏重算 |
| Rams 三选项 | [概念说明](output/rid-rams-concepts-2026-10-30/README.md) | A/1 橙键横向、B/2 绿滑钮竖式、C/3 钴蓝条键；生成图片，无对应新增精确 CAD |
| 竖式两材质 | [组合方案说明](output/rid-rams-portrait-v2-2026-10-30/README.md) | 2 的布局 + 1 的侧键 + 3 的底部接口；铝框/全树脂两图，仍为方屏时期的生成概念 |

### 必看的视觉文件

- **用户最近引用的原图**：[A1 主视角](hardware/rid-handheld-id-a1/renders/02-hero-cnc.png)。
- [A1 正面 RID](hardware/rid-handheld-id-a1/renders/01-front-rid.png)、[A1 细节板](hardware/rid-handheld-id-a1/renders/09-detail-board.png)。
- [A2 包覆铝壳](hardware/rid-handheld-id-a2/renders/01-hero-metal-wrap.png)、[A2 圆角近景](hardware/rid-handheld-id-a2/renders/04-continuous-corner.png)。
- [竖式：铝框 + SLA 前后盖](output/rid-rams-portrait-v2-2026-10-30/a-aluminum-frame-sla-covers.png)。
- [竖式：全 SLA 外壳](output/rid-rams-portrait-v2-2026-10-30/b-all-sla-resin.png)。
- [组合方案原始提示词](output/rid-rams-portrait-v2-2026-10-30/prompts.json)。

### 可编辑模型

- A1 Blender：`C:/Users/YX/Documents/云台检测/hardware/rid-handheld-id-a1/blender/yuntong-rid-id-a1.blend`
- A1 GLB：`C:/Users/YX/Documents/云台检测/hardware/rid-handheld-id-a1/blender/yuntong-rid-id-a1.glb`
- A2 Blender：`C:/Users/YX/Documents/云台检测/hardware/rid-handheld-id-a2/blender/yuntong-rid-id-a2.blend`
- A2 GLB：`C:/Users/YX/Documents/云台检测/hardware/rid-handheld-id-a2/blender/yuntong-rid-id-a2.glb`
- A2 精确平面曲线：[贝塞尔 SVG](hardware/rid-handheld-id-a2/references/id-a2-bezier-contours.svg)。
- A0 STEP：`C:/Users/YX/Documents/云台检测/hardware/rid-handheld-evt1/mechanical/generated/rid-handheld-evt1-a0.step`，**不是 A1/A2 或下一版的加工文件**。

早期交互演示已复制到仓库：[平放雷达 / 竖持高度交互 HTML](hardware/rid-handheld-evt1/interface/rid-pocket-interaction-v2.html)。它使用模拟数据，不代表实机或固件已接通；包含不同按键布局，主机可选的轮播/调节控件可能依赖原预览环境。

## 4. 后续屏幕路线：HY-A354TU102GG 已选定，当前测试先用 MSP2834

用户本轮提供原始规格书并明确“就用这个屏幕了”。当前型号固定为 **HY-A354TU102GG**，不再继续以旧候选表作为采购决策。

| 项目 | 已核实的规格书输入 |
|---|---|
| 显示 | 3.54 英寸 AMOLED，**604 × 1024**，约 336 ppi |
| AA | 45.6624 × 77.4144 mm |
| 面板本体 | 47.56 ± 0.15 × 80.11 ± 0.15 × 0.812 ± 0.15 mm，不含保护膜 |
| 展平包络 | 总表高度 118.07 mm 包含尾部；不是刚性面板高度，折叠形态未确认 |
| 圆角 | 结构图有圆角轮廓；准确半径与角部像素遮罩需厂家图纸 |
| 显示 / 触摸 | SD5207 / CST3530；MIPI DSI / I2C |
| 电气冲突 | 第 5 页 2 lane 与第 12 页 4 lane 不一致；第 6、37 页 pin 10 / 38 定义冲突 |

原始 PDF、页码、盖板叠层疑点及可转发给厂家的问题见 [当前屏幕记录](hardware/display-hy-a354tu102gg/README.md)。PDF 是 Preliminary，选定型号不代表已解决全部工程输入。

此前讨论过广州眺望 Core-T113-S3 和配套 T113-S-EVM，用户随后明确先在现有 P4 板验证。这段四通道方案不再是当前实验室测试基线。若后续恢复 3.54 英寸屏路线，再结合实屏时序与原始规格书评估。

以下为确认新屏之前的历史选型资料，保留供追溯，不作为当前方案。

### 先前已选择的 2 英寸屏

型号为 **AM200Q460460FLS1**，460 × 460，QSPI，有效显示区 35.88 × 35.88 mm。A2 已按此屏建模；供应商资料见 [本地 PDF](hardware/rid-handheld-id-a2/references/AM200Q460460FLS1.pdf) 和 [A2 设计说明](hardware/rid-handheld-id-a2/DESIGN_NOTES.md)。不要与 AM200MT460460FLS2 等 MIPI 型号混用。

### 历史候选：约 3.5 英寸竖屏（已被当前料号替代）

用户原话：**“可以找到3.5的无边框屏幕吗，最好还有圆角，我还是觉得原图比例更好一些。”**

此前对话查到的候选如下。它们是选型线索，**没有下单、收到样品或完成驱动验证；本轮交接没有重新核验库存/价格**。

| 型号 | 规格 | 有效显示区 AA / mm | 模组外形 / mm | 当前限制 |
|---|---|---|---|---|
| HP35001-D | 3.5 英寸 IPS，320 × 480，ST7796，SPI/并口 | 48.96 × 73.44 | 55.26 × 84.52 × 2.40，不带触摸版本 | 未确认原生圆角；不同供应商/触摸版本需核对 |
| ORC-T035023N-V01 | 3.5 英寸 IPS，320 × 480，ST7796S | 48.96 × 73.44 | 53.4 × 83 × 2.34 | 厂家询样；接口列为 MCU 16-bit / SPI+RGB 16-bit，不能擅自当纯 SPI 显示屏 |
| AMS353FD09-0 | 3.5 英寸 AMOLED，480 × 800 | 46.08 × 76.8 | 50.98 × 86.1 | RGB + SPI；厚度、供货、初始化和电源待拿完整规格书确认 |

来源：[HP35001 厂商页](https://www.eya-display.com/hp35001/)、[HP35001 显示区资料](https://www.zjhlcd.com/pd.jsp?id=87)、[ORIC 型号页](https://www.tftoled.com/products/3-5-inch-tft-motorcycle-display.html)、[AMOLED 供应商页](https://www.youritech.com/products/3-5-inch-oled-display-480x800-rgb-and-spi-interface-oled-module-high-contrast-amoled.html)。HP35001 厂商链接的[淘宝样品店](https://shop71431219.taobao.com/)仅作为询样入口，尚未确认具体在售商品及库存。

当时的选型判断（以下“未核实”等状态仅指此前调查）：

1. 尚未核实到同时满足 **3.5 英寸、原生圆角显示区、四边极窄、单片现货** 的确定型号。
2. 区分 AA（发光区）、VA（可视窗口）、CG（盖板玻璃）、LCM（模组）和整块开发板。商品图片中的圆角可能只是盖板或 PCB。
3. [A1 参数文件](hardware/rid-handheld-id-a1/id-brief.json)中的黑玻璃为 56.4 × 80.6 mm，对角线约 3.87 英寸；它是外观玻璃尺寸，**不是已实现的 3.87 英寸无边框显示区**。
4. 320 × 480 的 2:3 比例更接近 A1 黑玻璃；480 × 800 更瘦长。AMOLED 对大面积黑底的视觉融合有优势，但不能用材质渲染替代点亮样品观察。
5. 可以研究普通矩形屏 + 定制圆角黑色盖板/丝印遮光窗口；这不等于面板本身没有黑边，且会遮挡角部部分像素，需要 UI 安全边距。
6. 候选模组高 83–86.1 mm，外壳、排线、安装边和顶部天线还需空间。原 A1 机身 82 × 86 mm 不能直接当成装配已经成立。

上述旧候选不再继续冻结。当前下一步是澄清 HY-A354TU102GG 的 lane/引脚与盖板/FPC 输入，点亮样品，再据其重做结构包络；当前仍不发布冻结加工图。

## 5. 天线与 GNSS：最近讨论的结论

用户询问是否需要外接天线、能否沿用 FPV 棒棒糖接口，以及 GPS 是否需要像穿越机一样露在外面。下面是助手提出的建议，**用户尚未最终选定接口数量或模块型号**。

### RID 接收天线

- 便携版优先研究内置 FPC 天线；铝壳中的天线需要面向非金属打印窗口，避开屏幕金属背板、握持遮挡及不合适的电池/金属邻近位置。
- 原草案候选 **Molex 1461530100**，约 34.9 × 9 mm，100 mm 馈线，兼容 U.FL / I-PEX MHF 类连接，覆盖 2.4 GHz 和 5 GHz Wi-Fi；小型机也可核对同系列更短馈线型号。实际连接器代际和线长按模组核对。[Molex 资料](https://www.molex.com/en-us/products/series-chart/146153)
- 外接对照候选 **Taoglas GW.05.0153W**：白色可折叠，62.3 mm 长、直径 10 mm，RP-SMA(M)，覆盖 2.4/5.8 GHz 等 Wi-Fi 频段。[产品资料](https://www.taoglas.com/product/2-4-5-8ghz-white-terminal-mount-monopole-antenna-hinged-rp-smam/)
- 5.8 GHz 图传棒棒糖不能代替 2.4 GHz 天线；RHCP/LHCP 也不是通用“更强接收”的标志。按频段、极化、效率、方向图和握持表现选。
- SMA 与 RP-SMA 中心针孔不同，必须按两端实物/图纸匹配。
- 三路接收不能简单用一分三线并接；内外天线选择需要正确的射频开关/分路设计，或验证阶段人工换接。
- 曾提议背面上缘可更换打印嵌件：日常使用封闭外观，外场换成带接口版本。若两路 Wi-Fi 都外接可分别留接口、BLE 保持内置。此为可选结构提案，**不是已确定要在机身开两个孔**。

### GNSS 定位与姿态

- 可以使用穿越机同类 GNSS 小模块；**不必裸露，也不要求透明外壳**。上方要有适当非金属窗口，不能用金属化涂层把窗口封住。
- 现成验证候选 **FLYWOO GOKU GM10 Nano V3 GPS w/compass**：12 × 17 × 5 mm，3.3–5 V 输入，含罗盘。接线、逻辑电平、UART 和罗盘 I2C 仍须核对当前版本。[厂家产品页](https://flywoo.net/products/goku-gm10-nano-v3-gps-w-compass)
- 原定制主板候选 **u-blox MAX-M10S** + 独立 GNSS 天线。原天线占位为 Taoglas DSGP154B 15 × 15 × 4 mm 陶瓷贴片，其接地载板、馈点与安装没有验证；不要只按贴片尺寸认定所需总空间。
- 打印区树脂、涂层、间隙、铝框与天线接地板都会影响性能。参考 [u-blox GNSS 天线应用说明](https://content.u-blox.com/sites/default/files/products/documents/GNSS-Antennas_AppNote_%28UBX-15030289%29.pdf)。
- 单颗陶瓷贴片在平放/竖持时朝向不同；须比较两姿态和手握状态下的定位质量，不能假定竖持和平放完全一样。
- GPS 给本机位置，RID 给飞机广播位置，IMU 给姿态，地磁辅助静止航向。单天线 GPS 的运动航迹角不能替代静止设备朝向。
- 若用带罗盘的现成 GPS 模块，需决定使用其罗盘还是保留独立 BMM350，并考虑磁干扰；不能把两者未经设计都当作最终必装器件。

## 6. 电子与软件基线：可以继承，但不能宣称已完成

关键原件表：[key-bom.csv](hardware/rid-handheld-evt1/electrical/key-bom.csv)。完整状态：[EVT1 REVIEW](hardware/rid-handheld-evt1/REVIEW.md)。

| 模块 | 原草案 | 现状 |
|---|---|---|
| 原主控 | ESP32-S3-WROOM-1U-N16R8 | 旧 UI、BLE、汇聚、USB 草案；不能直接连接当前 MIPI DSI 屏，职责待调整 |
| 当前测试主控 | 细长 ESP32-P4-WIFI6 带排针版 | 用户照片和回复已确认。配 MSP2834 SPI 屏验证，板总高按用户 14.5 mm，结构见 V4。 |
| 后续四通道提案 | 全志 T113-S3，广州眺望 Core-T113-S3 | 历史选型，当前不采购此板来替换用户现有 P4 验证。 |
| Wi-Fi 接收 | 2 × ESP32-C5-WROOM-1U-N8R8 | 分别承担 2.4 GHz / 5 GHz 频段；每颗仍一次监听一个信道，采购与实机性能未确认 |
| GNSS / 姿态 / 地磁 | MAX-M10S / BMI270 / BMM350 | 选型与连接初表，不等于驱动已完成 |
| 充电 / USB-C | BQ25619 / TUSB320LAI | 5 V 受电、电源路径与 CC 方案；完整原理图和热/电流预算未完成 |
| 稳压 / 电量 | TPS63070 / MAX17048 | 候选；不能把芯片开关电流当作整机可用连续输出 |
| 电池 | 原约 2000 mAh、1S、保护及 NTC | 属于目标，不是已有确定供应商的完整电池包；尺寸/续航需按新屏和结构重新核算 |
| 当前显示电路 | HY-A354TU102GG | 用户已选定；原 A0 的 DT024ETFT-IPS 背光、插座与 GPIO 假设不适用，尚无新驱动或完成的原理图 |

参考：[电源与接口架构](hardware/rid-handheld-evt1/electrical/ARCHITECTURE.md)、[固件 README](hardware/rid-handheld-evt1/firmware/README.md)、[首板验收表](hardware/rid-handheld-evt1/validation/BRINGUP.md)。

历史检查记录写有 19 项主机 C++17 逻辑测试通过、GPIO 初表检查、A0 名义实体检查；A1/A2 也有模型封闭性和文件检查。**本轮交接没有重跑这些测试。** 它们均不代表已完成 ESP-IDF 编译、上板、真实 RID 接收、CNC 加工或充电/RF 验收。

固件当前有 C5 Beacon/Probe Response 信息元素筛选及串口骨架；NAN、BLE 接收、屏幕与各传感器驱动仍需落实。不得把“看到原始报文”写成“已兼容所有 RID 无人机”。

ESP32-P4/C6 台架固件（`hardware/rid-handheld-evt1/firmware/p4`）已做到以下几点：

- 解码 Wi-Fi Beacon 中的 ASTM F3411 与 GB 46750 位置、身份、航迹和速度；
- 按接收机原点换算东/北/天坐标，相对高度取大地高之差；
- 在 ILI9341 上显示北向上俯视页和侧视高度页；
- 已通过 2026-11-05 空口闭环（合成信号）。

这套固件可作为掌上机解码与 UI 逻辑的参考实现，但它不是 EVT1 主控方案；其解码器也只用本仓库自生成的报文验证过。

更早的路线和开源项目调查见 [RID 接收模块计划](docs/RID_RECEIVER_PLAN_2026-10-29.md)。其中仓库维护时间、协议范围与许可证是当时记录，真正采用前重新检查；OpenDroneID 国际协议库不能自动等同于国标解码器。

系统部署版可继续沿用接收核心，研究以太网/PoE 与后台接入。本轮仍优先掌上机，不把部署版机柜、天线和网络工作强行塞进便携机 ID 任务。

## 7. UI 与按键需要继承的语义

参考 [掌上交互设计 V2](docs/RID_HANDHELD_DESIGN_V2_2026-10-29.md) 与 [EVT1 按键/UI](hardware/rid-handheld-evt1/interface/INTERACTION.md)。这些文件的旧屏幕/壳体尺寸不再优先。

- 平放雷达式俯视；竖持线框地面、目标投影、高度柱的 2.5D 示意。它不是主动雷达测距或设备新增了测高传感器。
- 自动切换初值：低于 25° / 高于 60°，稳定 600 ms；中间保持原视图。属于待实机调整的参数。
- 上下键切目标；橙色键确认/锁定；M 做模式/返回；顶部或受保护电源键开关机、息屏。若采用最新侧边布局，要重新核实按键数量与 M 的容纳方式。
- 历史文档对 M 短按/长按的具体定义不完全一致：EVT1 写短按循环模式，A2 写短按打开模式菜单。**不把任一旧定义当成最终确认，下一版统一交互表。**
- 视图切换保留选定目标与范围；显示数据年龄、定位和航向有效性。
- GNSS 无定位、目标过期、罗盘异常时必须有退化显示；高度基准未知/不一致时显示“高度未知”，不能把相对起飞高度直接当成本机相对高度。
- 室内可能没有 GNSS 定位。模拟、回放、真实接收要明确区分，所有现有画面里的 168 m、+62 m 等都是示例。

## 8. Blender MCP：本机实测状态

**2026-11-05 当前状态：** Blender 5.2.1 LTS，MCP safe mode 下完成 V4 建模；已保存 `hardware/rid-handheld-rig-p1/v4/blender/yuntong-rig-p1-v4.blend`，当前场景 `RIG_P1_V4_Print`。历史 A1/V2/V3 场景保留。具体脚本、米/毫米转换和验证范围见 V4 README。以下表格仅为 **2026-10-30 历史现场记录**，接手时重新查询实时状态。

| 项目 | 实测 |
|---|---|
| Blender | 5.2.1 LTS |
| 当前文件 | `C:/Users/YX/Documents/云台检测/hardware/rid-handheld-id-a1/blender/yuntong-rid-id-a1.blend` |
| 当前场景 | `RID_ID_A1_Studio`；本次进程中另有 `Scene`，没有已经加载的 A2 场景 |
| 当前相机 | `RID_A1_Camera_hero` |
| 当前帧 | 0；标准装配展示通常用 1，拆分用 60 |
| 当前修改状态 | `bpy.data.is_dirty == True`，有未保存状态；此次没有保存或切换文件 |
| 单位 | METRIC / MILLIMETERS，`scale_length = 1.0`；真实坐标单位仍按米，脚本常用毫米 × 0.001 |
| MCP 插件 | 插件报告版本 `[1, 6]`，协议 5；当前 MCP 服务端期望协议 15，`up_to_date = false` |
| 可用性 | 本轮 `get_addon_status`、`get_scene_info`、安全范围内 `execute_blender_code` 和 `look` 均成功 |
| 安全模式 | `BLENDER_MCP_SAFE_MODE` 启用；具体限制见下文 |
| 外部素材/生成器 | 未依赖 Poly Haven、Sketchfab 等素材；纯 bpy 建模足以继续 |

接手时先查当前状态，再决定是否切换文件。**当前窗口有未保存状态，直接打开 A2 或重跑构建脚本可能丢失工作；应先保留当前修改，再开始新版本。** 本轮按用户要求只整理 README，没有创建交接快照或新压缩包。

### 8.1 当前配置与 Claude 的连接

本机存在可执行文件：`C:/Users/YX/.local/bin/uvx.exe`，本轮 `--version` 返回 `uvx 0.11.12`。不要使用 `C:/Users/YX/.codex/uvx.exe`，本轮检查该路径并不存在。

本机 Codex 的 `C:/Users/YX/.codex/config.toml` 中，`blender` 条目仍记录旧包命令：

```text
command: C:\Users\YX\.local\bin\uvx.exe
args: --python 3.11 blender-mcp
BLENDER_HOST: localhost
BLENDER_PORT: 9876
```

这只是已读到的本地条目，不能据此认定 Claude 已配置成功，也不能据此确定当前工具宿主一定由这一条启动。本轮未在检查到的 Claude 全局/当前项目配置字段发现 Blender 条目；Claude Desktop 的默认配置文件未找到。没有修改任何客户端配置。

上游现用名称为 **mcp-for-blender**。建议按一套服务端/插件版本配套配置，避免同时启用两个客户端控制同一场景。官方：[安装与升级](https://www.mcp-for-blender.com/docs/installation)、[客户端配置](https://www.mcp-for-blender.com/docs/mcp-clients)。

Claude Code 的手动添加示例（仅文档示例，本轮未执行；已有同名服务器时先检查，勿重复添加）：

```powershell
Set-Location -LiteralPath 'C:/Users/YX/Documents/云台检测'
claude mcp list
claude mcp add --scope local --transport stdio blender -- 'C:/Users/YX/.local/bin/uvx.exe' --python 3.11 mcp-for-blender
```

`--scope local` 仅针对当前项目的本机配置。进入 Claude Code 后用 `/mcp` 检查；若 `claude` 不在 PATH，先从已安装的 Claude Code 入口启动，不把命令不存在误判为 Blender 插件故障。[Claude Code MCP 文档](https://code.claude.com/docs/en/mcp)

Claude Desktop 则在其“Settings → Developer → Edit Config”中合并下面的服务器条目，保留已有配置：

```json
{
  "mcpServers": {
    "blender": {
      "command": "C:/Users/YX/.local/bin/uvx.exe",
      "args": ["--python", "3.11", "mcp-for-blender"],
      "env": {
        "BLENDER_HOST": "localhost",
        "BLENDER_PORT": "9876"
      }
    }
  }
}
```

默认配置路径通常是 `C:/Users/YX/AppData/Roaming/Claude/claude_desktop_config.json`，以客户端实际打开的位置为准。桌面版和 Code 的配置入口不同；普通云端网页聊天不会自动获得此本地 MCP 的控制能力。

版本不一致的处理示例（此次未升级）：先保存工作，再按上游步骤安装匹配插件。

```powershell
& 'C:/Users/YX/.local/bin/uvx.exe' mcp-for-blender install-addon
```

之后在 Blender 偏好设置中重新启用对应插件，或重启 Blender；3D 视图按 N 找到 MCP 面板，确认服务器运行，必要时点 Start MCP Server。重启 MCP 客户端后重新调用状态工具。不要为了交接文档就自动改动用户安装。

### 8.2 接手的第一次工具调用

工具前缀随 Claude 配置变化，以实际发现的工具为准。本次 Codex 暴露的是 `mcp__blender__...`。

1. `get_addon_status`：检查连通性、插件版本。
2. `get_scene_info`：建议 `fields=["settings","size","children","hidden"]`，先限制对象数量。
3. `execute_blender_code`：运行下面的只读检查。
4. `look`：`mode="camera"`、`shading="material"`、`max_size=720`，先看当前模型再修改。

下面这类代码已在当前安全模式成功执行：

```python
import bpy, json
s = bpy.context.scene
print(json.dumps({
    'file': bpy.data.filepath,
    'is_dirty': bpy.data.is_dirty,
    'scenes': [x.name for x in bpy.data.scenes],
    'active_scene': s.name,
    'frame': s.frame_current,
    'scale_length': s.unit_settings.scale_length,
    'camera': s.camera.name if s.camera else None,
    'render_running': bpy.app.is_job_running('RENDER')
}, ensure_ascii=False))
```

MCP 工具的 `user_prompt` 若需要提供，填写用户本次要求的原话；不要用助手内部步骤冒充用户指令。

### 8.3 当前安全模式与脚本执行方法

当前 MCP 明确限制：禁止 `os`、`subprocess`、网络调用、`open`、`eval`、`exec`、handlers/timers/drivers、类/属性注册，以及加载外部 `.blend` datablocks。渲染、保存、导入/导出操作在工具允许范围内；仍以实际工具检查结果为准。

本轮只读检查曾因 `import os` 和 `bpy.app.binary_path` 被拦截，删除不必要的访问后成功。因此：

- **不要通过 MCP 执行 `exec(open(path).read())`**，也不要绕过安全模式。
- 在 Claude 的文件工具/终端中读取 `.py` 内容，检查后把允许的纯 Python 源码直接作为 `execute_blender_code.code` 发送。
- 文件存在性、JSON 校验和报告写入放到普通主机文件工具中完成；不是必须在 Blender 内做。
- 旧导出脚本包含读取图片、文字转网格、保存及报告生成，不应在当前文件直接整段重跑。
- `BLENDER_MCP_SAFE_MODE` 的关闭不属于接手的必要步骤，不在此文档中要求更改它。

### 8.4 模型名称、单位与构建脚本

| 项目 | A1 | A2 |
|---|---|---|
| 场景 | `RID_ID_A1_Studio` | `RID_ID_A2_Studio` |
| 装配根 | `RID_A1_Assembly` | `RID_A2_Assembly` |
| 产品集合 | `ID-A1 | Product` | `ID-A2 | Product` |
| 摄影集合 | `ID-A1 | Studio` | `ID-A2 | Studio` |
| 参考/构造 | `ID-A1 | Supplied references` | `ID-A2 | Construction` |
| 主相机 | `RID_A1_Camera_hero` | `RID_A2_Camera_hero` |
| 屏幕 | `RID_A1_Screen_height/radar/reference` | `RID_A2_Screen_height/radar` |

上表中的斜线表示多个分别命名的对象，不是单个对象名。例如 `RID_A2_Screen_height` 和 `RID_A2_Screen_radar` 要互斥显示/渲染。

A2 关键对象包括 `RID_A2_CNC_wrap_shell`、`RID_A2_Printed_front_insert`、`RID_A2_Printed_rear_insert`、`RID_A2_Cubic_corner_control_path`。主模型的文字多数已转网格；精确贝塞尔构造曲线单独保留，勿误删。

- A1 脚本目录：`C:/Users/YX/Documents/云台检测/hardware/rid-handheld-id-a1/scripts/`。
- A2 脚本目录：`C:/Users/YX/Documents/云台检测/hardware/rid-handheld-id-a2/scripts/`。
- `make_artwork.py` 等是主机素材脚本；`01_build_blender.py` 等是 Blender 内运行的 bpy 脚本。
- A1 的历史阶段为构建、摄影棚、两轮细节、渲染、保存导出；A2 对应 `01_build`、`02_studio`、`04_finish`、`03_render`、`05_save_export`。有些阶段依赖先前状态，勿仅按文件编号批量执行。
- 两版构建脚本都有“场景已经存在则停止”的保护；应编辑现有对象或建立新版本，不能删保护后覆盖原场景。
- 渲染脚本内置 `BASE` 和固定文件名，会覆盖对应目录的既有渲染。新方案先改输出路径、对象前缀与场景名。
- Blender 坐标为米，辅助函数多接收毫米后乘 0.001；核对 `dimensions * 1000`，避免放大 1000 倍。摄影棚地面约 4 m，不属于产品尺寸。
- 材质节点按类型查找，如 `node.type == 'BSDF_PRINCIPLED'`；不要依赖本地化节点名称。颜色设在着色节点输入，不能只改 `diffuse_color`。
- 渲染/导出枚举依实际 Blender 版本查询。先小尺寸预览并 `look` 检查，再出高分辨率图；一次只跑一项渲染，超时后先检查 `bpy.app.is_job_running('RENDER')`。

贝塞尔控制点、G2/C2 定义与历史检查见 [A2 设计说明](hardware/rid-handheld-id-a2/DESIGN_NOTES.md)。网格是曲线采样结果，不能直接当作精确 CNC 曲面；需要制造时在 CAD 中重建并补齐公差/装配设计。

## 9. 建议 Claude 从这里继续

1. 读取本文件和关键图片，核对当前 Blender 文件/未保存状态，不重建整个项目。
2. 先打印 V4 的 P12/P13，确认孔径、面板 Type-C 孔距、沉头与尾套/弯头实际包络，再进行屏幕/托架/主板试装。当前不切换 T113，不把长杜邦母头空间加回来。
3. 将 A1 的长屏比例、A2 的正面金属围边与连续圆角、最新竖式/侧键组合放到一套可调布局中。保留铝框/SLA 与全 SLA 两材质对照。
4. 同时做初步剖面：屏幕/FPC、定制主板、电池、底部 Type-C、GNSS 与 Wi-Fi/BLE 非金属窗口。天线配置先比较方案，不未经说明固定外接接口数量。
5. 现有 `ID-A3` 二维包络属于旧 320 × 480 屏；为新屏重新计算并为三维版本独立命名。当前 A3 没有 Blender 模型。保留 A1/A2 原资产，新产物按自己的版本更新说明和验证范围。
6. 先交付能比较比例和按键的正面/三分之四/侧面图、材质对照与尺寸包络；外观收敛后再推进完整机械和电气设计。

本机目录还有 [AI_HANDOFF.md](AI_HANDOFF.md)，主要讲 2026-09-04 的双摄视觉监控系统。其历史软件背景可参考，但不覆盖本文件所记录的最新 RID 工业设计决策。

## 10. 可直接发给 Claude 的接手提示

> 在 `codex/rig-p1-printable-shell` 分支接手，先读 `hardware/rid-handheld-rig-p1/v4/README.md`。当前使用照片中的细长 ESP32-P4-WIFI6 带排针版和 MSP2834 2.8 SPI 屏，全部焊线；屏幕总高 14 mm，板总高 14.5 mm。V4 外壳厚 27、包含按键 27.7 mm，底部居中 Type-C 延长座，总厚度必须控制在 28 mm 内。用 Git LFS 获取文件，打开 V4 Blender 场景。先做 P12/P13 和实板试装，核对 USB 尾套及弯头暂定包络，再增量修改。使用 Blender MCP 前检查实时场景，保留 A1 等历史资产。HY-A354TU102GG / T113 属于后续或历史路线，不跳过现有器件验证。
