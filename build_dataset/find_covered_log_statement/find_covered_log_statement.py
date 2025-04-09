'''
In docker container, run the following command to execute the script:
python3 find_covered_log_statement.py
'''

import json
import os
import subprocess
import logging
import time
from typing import List, Dict, Any
import argparse
from tool import setup_logging

def load_projects(json_path: str) -> List[Dict[str, Any]]:
    """load data from json file"""
    try:
        with open(json_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        raise Exception(f"load data failed: {e}")

def run_tests(project_dir: str, hadoop_root: str, test_list: List[str], logger: logging.Logger, data_save_dir) -> bool:
    """Run tests in the specified project directory"""
    try:
        # Change to project directory
        os.chdir(project_dir)
        logger.info(f"Changed to directory: {project_dir}")
        
        # Run mvn test command for each test case
        for index,test_name in enumerate(test_list):
            cmd = f"mvn test -Dtest={test_name}"
            if index == 0:
              cmd = f"mvn clean test -Dtest={test_name}"
            logger.info(f"Running Test: {test_name} in {cmd}")
            
            # Record start time
            start_time = time.time()

            # Execute command and capture output
            subprocess.run(
                cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            if not os.path.exists("target/site/jacoco") or not os.path.exists("target/surefire-reports"):
                logger.warning(f"{test_name} has no jacoco or surefire-reports")
                continue
            

            # Create a folder to save test results
            save_dir = f'{data_save_dir}/{project_dir.replace(hadoop_root, "")}/{test_name}'
            os.makedirs(save_dir, exist_ok=True)

            # Create jacoco and surefire-reports folders
            os.makedirs(f"{save_dir}/jacoco", exist_ok=True)
            os.makedirs(f"{save_dir}/surefire-reports", exist_ok=True)

            # Copy the contents of jacoco and surefire-reports folders to data_save_dir
            subprocess.run(f"cp -r target/site/jacoco/* {save_dir}/jacoco/", shell=True, stderr=subprocess.DEVNULL)
            subprocess.run(f"cp -r target/surefire-reports/* {save_dir}/surefire-reports/", shell=True, stderr=subprocess.DEVNULL)
          


            # Delete jacoco and surefire-reports folders in target directory
            subprocess.run("rm -rf target/site target/surefire-reports", shell=True)
  
            # Record execution time
            execution_time = time.time() - start_time
            
            # Log command output
            logger.info(f"Test case {test_name} execution completed, time spent: {execution_time:.2f} seconds")
            logger.info(f"Current project progress: {index + 1}/{len(test_list)}")
        
        return True
    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        return False

def process_projects(projects: List[Dict[str, Any]], hadoop_root: str, logger: logging.Logger, data_save_dir: str) -> None:
    """Process all projects and run their tests"""
    # Creating a progress bar for projects
    for project in projects:
      project_dir = os.path.join(hadoop_root, project["project_dir"])
      test_list = project["test_list"]
      test_num = project["test_num"]
      
      logger.info(f"Begin Processing: {project['project_dir']}")
      logger.info(f"Number of test cases: {test_num}")
      
      if os.path.exists(project_dir):
        success = run_tests(project_dir,hadoop_root, test_list, logger, data_save_dir)
        if success:
          logger.info(f"All tests for project {project['project_dir']} have been successfully executed")
        else:
          logger.warning(f"Errors occurred during test execution for project {project['project_dir']}")
      else:
        logger.error(f"Project directory does not exist: {project_dir}")
      
      logger.info(f"Current progress: {projects.index(project) + 1}/{len(projects)}")

def main():
    """Main function"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Run project test cases')
    parser.add_argument('--potential-dir', type=str, default='/home/tby/hadoop/script_new/build_dataset/initial_project/data/test_dir.json',
                      help='Path to project list JSON file')
    parser.add_argument('--hadoop-root', type=str, default='/home/tby/hadoop',
                      help='Hadoop project root directory in Docker')
    parser.add_argument('--log-dir', type=str, default='./log',
                      help='Log file storage directory')
    parser.add_argument('--data-save-dir', type=str, default='/home/tby/hadoop/script_new/build_dataset/find_covered_log_statement/data',
                      help='Data save directory, please use absolute path in Docker')
    
    args = parser.parse_args()

    if not os.path.exists(args.data_save_dir):
        os.makedirs(args.data_save_dir)
        print(f"Created data save directory: {args.data_save_dir}")
    
    # Set up logging
    logger = setup_logging(args.log_dir)
    logger.info("Starting test execution process")
    
    try:
        # Load project list
        logger.info(f"Loading project list from {args.potential_dir}")
        projects = load_projects(args.potential_dir)
        logger.info(f"Loaded {len(projects)} projects")
        
        # Process projects
        process_projects(projects, args.hadoop_root, logger, args.data_save_dir)
        
        logger.info("Test execution process completed")
    except Exception as e:
        logger.error(f"Execution error: {e}", exc_info=True)

if __name__ == "__main__":
    main()
