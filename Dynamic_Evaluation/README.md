# Dynamic Evaluation
Dynamic evaluation focuses on compiling the code and runtime-generated logs, addressing static evaluation’s inability to verify code compilability and runtime logs. To directly assess runtime logs, we generate them using unit tests, which are widely used in software development to verify code functionality in isolated scenarios. 

## Quick Start
### Step 1
You need to prepare the [Hadoop 3.4.0 source code](https://drive.google.com/drive/u/1/folders/1eoK7SaYTuwqcAe9T3ddjeU5oGLRDX2Ps) and use the dockerfile in `docker/` repo to build the enviroment. Replace the dockerfile provided by Hadoop with the one in `docker/Dockerfile_aarch64`.

### Step 2
Run command `mvn clean install -DskipTests` to prepare the source code for dynamic evaluation.

### Step 3
Run command `./start-test.sh` to run the unit test and generate the logs. Before running this script, you need to modify the `dynamic_evaluation.js` script to replace the `[PATH IN DOCKER]` path of source code with your real path. If you want to test the prediction results of your automatic logging tool, you need to put the prediction results in `./data/demo/test` repo and run the script. 

### Step 4
Run the script `./dynamic_evaluation/res/script/Similarity/calculateSimilarity.py` to calculate the similarity between the predicted logs and the actual logs. Run the script `./dynamic_evaluation/res/script/getMetrics.js` to get the metrics of the predicted logs.


The `data/demo` repo contains:

```markdown
data/demo/
├── test/
│   └── demo.json           # Prediction results file
│       ├── function_content  # Content of function to modify
│       ├── function_position  # File path of function to modify
│       ├── function_lines     # Line range of function (e.g. "10-20") 
│       ├── function_without_covered_logs     # function without covered logs
│       ├── uuidMap    # necessary information for mapping uuid to function_position
│       ├── prediction         # Predicted log statement
│       └── uuid              # Unique identifier for prediction
│
├── result/
│   └── demo.json           # Prediction results file
│
├── replaceLogs/           # Directory for replacement logs
│   ├── <uuid>.json       # Records original and replaced content
│   └── <uuid>.bak        # Indicates reversed replacements
│
├── output/             # Directory for unit test output logs
│   └── <hadoop_project_name>_<Unit Test Name>_<uuid>.txt       # Unit test output logs
│
└── logs/             # Directory for test execution logs
    └── *.log            # Runtime logs for comparing predictions vs actual output

  
```

## Results
The data when we build the dataset are all packaged and the generated logs are all packaged. We put all data on the One Drive: https://drive.google.com/drive/u/1/folders/1eoK7SaYTuwqcAe9T3ddjeU5oGLRDX2Ps