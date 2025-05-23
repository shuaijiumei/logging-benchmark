# Dynamic Evaluation

This directory contains scripts and tools for dynamic evaluation of AI models in a software development context.

## Directory Structure

### build_dataset/

This directory contains scripts for building datasets used in dynamic evaluation:

- **initial_project/**: Initial project templates and configurations. (If you use docker image to build the dataset, you can ignore this step.)
- **get_logs_output/**: Scripts for collecting log outputs from the system.
- **find_covered_log_statement/**: Tools to identify and analyze covered log statements in the codebase.

### eval/

This directory contains scripts and tools for executing the evaluation process:

- Download the dataset from [here](https://drive.google.com/drive/u/1/folders/1eoK7SaYTuwqcAe9T3ddjeU5oGLRDX2Ps) and put it in the `eval/res` directory.

- Run the `eval_res.py` script to evaluate the results.

- Run the `get_metrics.py` script to get the evaluation metrics. The result will be saved in the `eval/evaluation_results.md` file.


## Requirements

Please ensure all dependencies are installed before running the scripts.

