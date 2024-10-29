# Logging Benchmark
This repo includes the scripts for dynamic evaluation.

## Repo Description
+ In `dynamic_evaluation` repo, we put the results of dynamic evaluation and the scripts for analyzing the results.
  + In repo `data`, we provide a demo JSON file for dynamic eavaluation. It is very time consuming for evaluating the complete predictions results of any automatic logging tools, we provide a demo data for run the whole process of dynamic evaluation. The details could be seen following.
  + In repo `res`, we provide the analysis of dynamic evaluation's results. Scripts for evaluate the similarity between logs are put here, and you need to download the data of analysis results and logs produced from One Drive.
  + In repo `rq2`, we put the randomly selected examples for analyzing the compilation failure.
  + In repo `tool`, we provide some additional scirpts of dynamic evaluation.
+ In `init_dynamic_evaluation`, we provide necessary scripts for reproducing our process for building datasets. To reproduce our process of building datasets, you need compile the Hadoop 3.4.0 source code and use the scirpt to add dependencies of Jacoco. We release the dockerfile used for building the enviroment put in `dockek/` repo. Then you could use the `autoTest.js` script to run each unit test to get the covered functions with log statements.

## Conduct Dynamic Evaluation
### Step 1
First, you need to download the source code of Hadoop 3.4.0 and compile the Hadoop according to the guidelines.

### Step 2
Second, following the demo in `./dynamic_evaluation/data/demo`, you need to put the data with predicted log statements in `test` repo. The data should follow the `demo.json` striucture. In this data, you need to modify the `function_position` to your real location on your computer so that the scirpt in `./dynamic_evaluation` could successfully replace the source code. And you need also modify the path in `./dynamic_evaluation.js`, we leave `[PATH IN DOCKER]` to highlight the path.

### Step 3
Third, modify the scirpts in `./start-test.sh` according to data you want to test, and in docker enviroment, run the `./start-test.sh`.

## Results
The data when we build the dataset are all packaged and the generated logs are all packaged. We put all data on the One Drive: https://drive.google.com/drive/u/1/folders/1eoK7SaYTuwqcAe9T3ddjeU5oGLRDX2Ps