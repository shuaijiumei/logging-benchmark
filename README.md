# AL-Bench: Automatic Logging Benchmark

[English](README.md) | [中文](README_CN.md)

AL-Bench is a comprehensive automatic logging benchmark framework designed to evaluate and compare different automatic log generation tools. This framework consists of two main components: static evaluation and dynamic evaluation.

## Overview

![AL-Bench Overview](./img/evaluation_based_on_execution.png)

*Figure 1: Overview of AL-Bench framework and evaluation process*

## Project Structure

```
.
├── Static_Evaluation/    # Scripts and results for static evaluation
│   ├── eval/            # Evaluation scripts for each logging tool
│   └── data/            # Evaluation result data
└── Dynamic_Evaluation/  # Scripts and results for dynamic evaluation
    ├── dynamic_evaluation/  # Core scripts for dynamic evaluation
    └── init_dynamic_evaluation/  # Dataset construction scripts
```

## Evaluation Methods

### Static Evaluation

Static evaluation focuses on the following aspects:
1. Log Level Accuracy
2. Log Position Accuracy
3. Log Message Accuracy
4. Comprehensive Evaluation Metrics:
   - ROUGE Score
   - BLEU Score
   - Cosine Similarity

![Static Evaluation Process](assets/static_evaluation.png)

*Figure 2: Static evaluation process and metrics calculation*

### Dynamic Evaluation

Dynamic evaluation is based on Hadoop 3.4.0 unit tests, assessing the performance of logging tools in actual runtime environments:
1. Compilation Success Rate
2. Runtime Behavior
3. Log Output Quality
4. Performance Impact

![Dynamic Evaluation Process](assets/dynamic_evaluation.png)

*Figure 3: Dynamic evaluation workflow with Hadoop test suite*

## Quick Start

### Requirements
- Java Development Kit (JDK)
- Maven
- Node.js
- Docker (for dynamic evaluation)

### Static Evaluation

1. Enter the Static_Evaluation directory:
```bash
cd Static_Evaluation
```

2. Run evaluation script:
```bash
python eval/[tool_name]/run_eval.py
```

### Dynamic Evaluation

1. Prepare environment:
```bash
cd Dynamic_Evaluation
# Follow instructions in init_dynamic_evaluation to build Docker environment
```

2. Run demo evaluation:
```bash
# Modify path configuration in dynamic_evaluation.js
# Run evaluation script
./start-test.sh
```

## Dataset

The complete evaluation dataset can be accessed at:
https://drive.google.com/drive/u/1/folders/1eoK7SaYTuwqcAe9T3ddjeU5oGLRDX2Ps

## Supported Logging Tools

- FastLog
- UniLog
- LANCE
- Leonid
- Leonid_M

## Citation

If you use AL-Bench in your research, please cite our paper: [Citation information to be added]

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2024 AL-Bench

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.