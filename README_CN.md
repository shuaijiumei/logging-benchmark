# AL-Bench: 自动日志基准测试框架

[English](README.md) | [中文](README_CN.md)

AL-Bench 是一个全面的自动日志基准测试框架，旨在评估和比较不同的自动日志生成工具。本框架包含静态评估和动态评估两个主要组件。

## 概述

![AL-Bench 概述](assets/overview.png)

*图 1: AL-Bench 框架和评估流程概述*

## 项目结构

```
.
├── Static_Evaluation/    # 静态评估相关脚本和结果
│   ├── eval/            # 各个日志工具的评估脚本
│   └── data/            # 评估结果数据
└── Dynamic_Evaluation/  # 动态评估相关脚本和结果
    ├── dynamic_evaluation/  # 动态评估核心脚本
    └── init_dynamic_evaluation/  # 数据集构建脚本
```

## 评估方法

### 静态评估 (Static Evaluation)

静态评估主要关注以下几个方面：
1. 日志级别准确性 (Log Level Accuracy)
2. 日志位置准确性 (Log Position Accuracy)
3. 日志消息准确性 (Log Message Accuracy)
4. 综合评估指标：
   - ROUGE 分数
   - BLEU 分数
   - 余弦相似度

![静态评估流程](assets/static_evaluation.png)

*图 2: 静态评估流程和指标计算*

### 动态评估 (Dynamic Evaluation)

动态评估基于 Hadoop 3.4.0 的单元测试，评估日志工具在实际运行环境中的表现：
1. 编译成功率
2. 运行时行为
3. 日志输出质量
4. 性能影响

![动态评估流程](assets/dynamic_evaluation.png)

*图 3: 基于 Hadoop 测试套件的动态评估工作流*

## 快速开始

### 环境要求
- Java Development Kit (JDK)
- Maven
- Node.js
- Docker (用于动态评估)

### 静态评估

1. 进入 Static_Evaluation 目录：
```bash
cd Static_Evaluation
```

2. 运行评估脚本：
```bash
python eval/[tool_name]/run_eval.py
```

### 动态评估

1. 准备环境：
```bash
cd Dynamic_Evaluation
# 按照 init_dynamic_evaluation 中的说明构建 Docker 环境
```

2. 运行演示评估：
```bash
# 修改 dynamic_evaluation.js 中的路径配置
# 运行评估脚本
./start-test.sh
```

## 数据集

完整的评估数据集可在以下位置获取：
https://drive.google.com/drive/u/1/folders/1eoK7SaYTuwqcAe9T3ddjeU5oGLRDX2Ps

## 支持的日志工具

- FastLog
- UniLog
- LANCE
- Leonid
- Leonid_M

## 引用

如果您在研究中使用了 AL-Bench，请引用我们的论文：[论文引用信息待补充]

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

```
MIT License

Copyright (c) 2024 AL-Bench

特此免费授予任何获得本软件副本和相关文档文件（"软件"）的人不受限制地处理本软件的权利，
包括但不限于使用、复制、修改、合并、发布、分发、再许可和/或出售软件副本的权利，
以及允许向其提供本软件的人这样做，但须符合以下条件：

上述版权声明和本许可声明应包含在本软件的所有副本或重要部分中。

本软件按"原样"提供，不提供任何形式的明示或暗示的保证，包括但不限于对适销性、
特定用途的适用性和非侵权性的保证。在任何情况下，作者或版权持有人均不对任何索赔、
损害或其他责任负责，无论是在合同诉讼、侵权行为或其他方面，由软件或软件的使用或
其他交易引起、由软件引起或与之相关。
``` 