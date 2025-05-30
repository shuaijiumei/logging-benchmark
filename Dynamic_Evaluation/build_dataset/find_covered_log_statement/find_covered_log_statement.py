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
# 从extract_covered_log_statement模块导入extract_covered_logs函数
from extract_covered_log_statement import extract_covered_logs
# Multi-thread version
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

def load_projects(json_path: str) -> List[Dict[str, Any]]:
    """load data from json file"""
    try:
        with open(json_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        raise Exception(f"load data failed: {e}")

def write_test_result(result_save_dir: str, project_dir: str, test_name: str, execution_time: float, build_success: bool, result_file_lock: threading.Lock = None) -> None:
    """将测试结果写入文件"""
    def write_to_file(result_save_dir: str, project_dir: str, test_name: str, execution_time: float, build_success: bool):
        with open(result_save_dir, 'a') as f:
            f.write(json.dumps({
                "project_dir": project_dir,
                "test_name": test_name,
                "execution_time": execution_time,
                "build_success": build_success
            }) + '\n')

    if result_file_lock is not None:
        result_file_lock.acquire()
    write_to_file(result_save_dir, project_dir, test_name, execution_time, build_success)
    if result_file_lock is not None:
        result_file_lock.release()


def run_tests(project_dir: str, hadoop_root: str, test_list: List[str], logger: logging.Logger, data_save_dir: str, execution_result_save_dir: str, use_cache: str, result_file_lock: threading.Lock = None) -> bool:
    """Run tests in the specified project directory"""
    try:
        # Run mvn test command for each test case
        for index,test_name in enumerate(test_list):
            if use_cache == 'yes':
                # 如果 data_save_dir 中存在相同的 project_dir 和 test_name，则跳过
                if os.path.exists(execution_result_save_dir):
                    with open(execution_result_save_dir, 'r') as f:
                        data_save_list = [json.loads(line) for line in f]
                    if any(item["project_dir"] == project_dir and item["test_name"] == test_name for item in data_save_list):
                        continue
            if index == 0:
                # 先构建项目
                cmd = f"mvn clean install -DskipTests"
                result = subprocess.run(cmd, shell=True, cwd=project_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                if result.returncode != 0:
                    logger.error(f"Build project failed: {project_dir}")
                    # 写入 jsonl 记录
                    write_test_result(execution_result_save_dir, project_dir, 'all', 0, False, result_file_lock)
                    return False

            cmd = f"mvn test -Dtest={test_name}"
            logger.info(f"Running Test: {test_name} in {cmd}")
            target_dir = os.path.join(project_dir, "target/site/jacoco")
            surefire_dir = os.path.join(project_dir, "target/surefire-reports")

            # 先删一遍，万一有漏网之鱼
            subprocess.run(f"rm -rf {target_dir} {surefire_dir}", shell=True)
            
            # Record start time
            start_time = time.time()

            # Execute command and capture output
            subprocess.run(
                cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=project_dir
            )

            if not os.path.exists(target_dir) or not os.path.exists(surefire_dir):
                logger.warning(f"{test_name} has no jacoco or surefire-reports")
                # 如果只存在一个，则删除，因为会影响下一次的测试
                if os.path.exists(target_dir):
                    subprocess.run(f"rm -rf {target_dir}", shell=True)
                if os.path.exists(surefire_dir):
                    subprocess.run(f"rm -rf {surefire_dir}", shell=True)
                
                write_test_result(execution_result_save_dir, project_dir, test_name, 0, True, result_file_lock)
                continue
            
            # Create a folder to save test results
            save_dir = f'{data_save_dir}/{project_dir.replace(hadoop_root, "")}/{test_name}'
            os.makedirs(save_dir, exist_ok=True)

            # Create jacoco and surefire-reports folders
            os.makedirs(f"{save_dir}/jacoco", exist_ok=True)
            os.makedirs(f"{save_dir}/surefire-reports", exist_ok=True)

            # Copy the contents of jacoco and surefire-reports folders to data_save_dir, to save space, only copy
            # jacoco.xml for usage
            subprocess.run(f"cp -r {target_dir}/jacoco.xml {save_dir}/jacoco/", shell=True, stderr=subprocess.DEVNULL)
            subprocess.run(f"cp -r {surefire_dir}/* {save_dir}/surefire-reports/", shell=True, stderr=subprocess.DEVNULL)

            # Delete jacoco and surefire-reports folders in target directory
            subprocess.run(f"rm -rf {target_dir} {surefire_dir}", shell=True)

            # Record execution time
            execution_time = time.time() - start_time
            
            # Log command output
            logger.info(f"Test case {test_name} execution completed, time spent: {execution_time:.2f} seconds")
            logger.info(f"Project {project_dir} progress: {index + 1}/{len(test_list)}")

            # 写入 jsonl 记录
            write_test_result(execution_result_save_dir, project_dir, test_name, execution_time, True, result_file_lock)
        return True

    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        return False

def start_from_cache():
    '''
    从缓存中读取已经执行过的项目，并跳过这些项目
    '''

def process_single_project(project: Dict[str, Any], hadoop_root: str, logger: logging.Logger, data_save_dir: str, result_save_dir: str, use_cache: str, result_file_lock: threading.Lock = None) -> None:
    """Process a single project and run its tests"""
    project_dir = os.path.join(hadoop_root, project["project_dir"])
    test_list = project["test_list"]
    test_num = project["test_num"]
    
    logger.info(f"Begin Processing: {project['project_dir']}")
    logger.info(f"Number of test cases: {test_num}")
    
    if os.path.exists(project_dir):
        success = run_tests(project_dir, hadoop_root, test_list, logger, data_save_dir, result_save_dir, use_cache, result_file_lock)
        if success:
            logger.info(f"All tests for project {project['project_dir']} have been successfully executed")
        else:
            logger.warning(f"Errors occurred during build project {project['project_dir']}")
    else:
        logger.error(f"Project directory does not exist: {project_dir}")

def process_projects(projects: List[Dict[str, Any]], hadoop_root: str, logger: logging.Logger, data_save_dir: str, num_thread: int, result_save_dir: str, use_cache: str) -> None:
    """Process all projects and run their tests"""

    if not os.path.exists(result_save_dir):
        with open(result_save_dir, 'w') as f:
            f.write('')

    if num_thread == 1:
        # Single thread version
        for index, project in enumerate(projects):
            logger.info(f"Current progress: {index + 1}/{len(projects)}")
            process_single_project(project, hadoop_root, logger, data_save_dir, result_save_dir, use_cache, None)
            logger.info(f"Project {project['project_dir']} completed successfully")
            logger.info(f"==========Current progress: {index + 1}/{len(projects)}==========")
    else:
        
        # 创建文件锁
        result_file_lock = threading.Lock()
        
        with ThreadPoolExecutor(max_workers=num_thread) as executor:
            futures = {
                executor.submit(process_single_project, project, hadoop_root, logger, data_save_dir, result_save_dir, use_cache, result_file_lock): project
                for project in projects
            }
            
            for index, future in enumerate(as_completed(futures)):
                project = futures[future]
                try:
                    future.result()
                    logger.info(f"Project {project['project_dir']} completed successfully")
                except Exception as e:
                    logger.error(f"Error processing project {project['project_dir']}: {e}")
                logger.info(f"==========Current progress: {index + 1}/{len(projects)}==========")

def exclude_build_failed_from_catch_projects(data_save_dir: str, projects: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    '''
        这里只清理 projects build failed 的
    '''
    if not os.path.exists(data_save_dir):
        return projects

    # 读取 jsonl
    with open(data_save_dir, 'r') as f:
        data_save_list = [json.loads(line) for line in f]

    build_failed_projects = []
    for item in data_save_list:
        if item["build_success"] == False:
            build_failed_projects.append(item["project_dir"])
    
    unfinished_projects = []
    for project in projects:
        if project["project_dir"] not in build_failed_projects:
            unfinished_projects.append(project)
    return unfinished_projects

def main():
    """Main function"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Run project test cases and extract covered log statements')
    parser.add_argument('--potential-dir', type=str, default='/home/al-bench/AL-Bench/Dynamic_Evaluation/initial_project/data/test.json',
                      help='Path to project list JSON file')
    parser.add_argument('--code-root', type=str, default='/home/al-bench/hadoop-3.4.0-src',
                      help='Hadoop project root directory in Docker')
    parser.add_argument('--num-thread', type=int, default=4,
                      help='Multi-thread execution')
    # 添加extract_covered_log_statement.py需要的参数
    parser.add_argument('--code-json', type=str, default='/home/al-bench/AL-Bench/Dynamic_Evaluation/find_covered_log_statement/code_data/hadoop-log-statement-data.json',
                      help='Path to the Json file containing log statement information')

    parser.add_argument('--execute_id', type=str, default='hadoop_major_test',
                      help='The id of the execution')
    parser.add_argument('--data-save-dir', type=str, default='/home/al-bench/AL-Bench/Dynamic_Evaluation/find_covered_log_statement/data/',
                    help='Data save directory, please use absolute path in Docker')
    parser.add_argument('--use-cache', choices=['yes', 'no'], required=True,
                      help='Start from cache')

    args = parser.parse_args()

    code_root = args.code_root
    code_json = args.code_json
    num_thread = args.num_thread
    potential_dir = args.potential_dir
    use_cache = args.use_cache

    execute_id = args.execute_id
    data_save_dir = os.path.join(args.data_save_dir, execute_id)
    log_dir = os.path.join(data_save_dir, 'log')
    target_save_dir = os.path.join(data_save_dir, 'target')
    result_save_dir = os.path.join(data_save_dir,'result')
    execution_result_save_dir = os.path.join(data_save_dir,'result', 'execution_result.jsonl')
    covered_log_statement_result_save_dir = os.path.join(result_save_dir, 'covered_log_statement.json')

    if not os.path.exists(data_save_dir):
        os.makedirs(data_save_dir)
    if not os.path.exists(target_save_dir):
        os.makedirs(target_save_dir)
    if not os.path.exists(result_save_dir):
        os.makedirs(result_save_dir)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Set up logging
    logger = setup_logging(log_dir)
    logger.info("Starting test execution process")
    
    try:
        # 第一步：执行测试并收集覆盖率信息
        logger.info(f"Loading project list from {potential_dir}")
        projects = load_projects(potential_dir)
        logger.info(f"Loaded {len(projects)} projects")

        if use_cache == 'yes':
            unfinished_projects = exclude_build_failed_from_catch_projects(execution_result_save_dir, projects)
            projects = unfinished_projects

        # Process projects
        process_projects(projects, code_root, logger, target_save_dir, num_thread, execution_result_save_dir, use_cache)
        logger.info("Test execution process completed")

        # 第二步：提取被覆盖的日志语句
        logger.info("==========Starting extraction of covered log statements==========")
        # 直接调用extract_covered_logs函数，传入参数
        extract_covered_logs(
            data_dir=target_save_dir,
            source_code_dir=code_root,
            code_json=code_json,
            save_dir=covered_log_statement_result_save_dir,
            logger=logger
        )
        logger.info("Extraction of covered log statements completed")
            
    except Exception as e:
        logger.error(f"Execution error: {e}", exc_info=True)

if __name__ == "__main__":
    main()
