# STEP 装配体

当前文件：[yuntong-rig-p1-v4-native-assembly.stp](yuntong-rig-p1-v4-native-assembly.stp)。

这份文件由 CadQuery/OpenCascade 原生建模后直接导出，单位 mm，14 个结构实体各自保留名称、颜色及装配位置。包含壳体、黑框、按键、托架与四个压片；电子元件简化包络不在本结构装配体内。

圆柱孔、圆弧、倒圆及贝塞尔边界是 CAD 曲线/曲面，没有读取 STL 或将三角面缝合成实体。STEP 保留几何与装配结构；重建参数和操作顺序保存在 Python 源码中，不将 STEP 称为带原软件特征历史的工程文件。

导出记录：[native-cad-export.json](../validation/native-cad-export.json)。源 BRep：[yuntong-rig-p1-v4-native-assembly.brep](../cad/yuntong-rig-p1-v4-native-assembly.brep)。

旧 `yuntong-rig-p1-v4.stp` 和 `parts/` 是先前网格转换产物，仅保留对照，不作为本次原生 CAD 交付。
