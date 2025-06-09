#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@File: execute_unittest.py
@Author: shuaijiumei
@Email: BoyinTan1221@gmail.com
@Date: 2025-4-10
@Description: 
  Mainly implements three functions: function replacement + test execution + log processing
  1. Function replacement: Operates on files to replace original content with labeled content. This operation needs to be recorded to prevent original code from being corrupted in case of sudden termination
  2. Test execution: mvn clean test -Dtest={test_name}
  3. Find logs printed by marked log statements in the log files
"""

import os
import json
import logging
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Union, Optional
from tool import setup_logging, replace_func, reverse_func, read_jsonl, read_json
import argparse
import shutil
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import sys


def load_catch_point(results_data: List[Dict], uuid: str) -> bool:
    for item in results_data:
        if item['uuid'] == uuid:
            return True
    return False

def save_result(execute_success: bool, execute_time: float, label_file_size: float, complete_file_size: float, results_dir: str, uuid: str, file_location: str, write_lock: threading.Lock = None) -> None:
    result_item = {
        "uuid": uuid,
        "execute_success": execute_success,
        'execute_time': execute_time,
        'label_file_size': label_file_size,
        'complete_file_size': complete_file_size,
        'file_location': file_location
    }
    if write_lock is not None:
        write_lock.acquire()
    with open(os.path.join(results_dir, "results.jsonl"), 'a', encoding='utf-8') as f:
        f.write(json.dumps(result_item) + '\n')
    if write_lock is not None:
        write_lock.release()


def run_maven_test(test_name: str, mvn_dir: str, logger: logging.Logger, record_error: bool, record_error_path: str, uuid: str) -> bool:
    try:
        command = ["mvn", "clean", "test", f"-Dtest={test_name}"]
        result = subprocess.run(
            command,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=mvn_dir
        )
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to run test: {test_name}")
        logger.error(f"Command: {e.cmd}")
        logger.error(f'Execute dir: {mvn_dir}')
        logger.error(f"Return code: {e.returncode}")
        logger.error(f"Standard output:\n{e.stdout}")
        logger.error(f"Standard error:\n{e.stderr}")
        if record_error:
            with open(os.path.join(record_error_path, f"{uuid}.log"), 'w', encoding='utf-8') as f:
                f.write(f"Command: {e.cmd}\n")
                f.write(f'Execute dir: {mvn_dir}\n')
                f.write(f"Return code: {e.returncode}\n")
                f.write(f"Standard output:\n{e.stdout}\n")  
                f.write(f"Standard error:\n{e.stderr}\n")
        return False
    except Exception as e:
        logger.error(f"Unexpected error occurred while running test {test_name}: {str(e)}")
        return False

def execute_unittest(json_data: List[Dict], replace_data_path: str, results_dir: str, logger: logging.Logger, use_catch_point: bool, record_error: bool, record_error_path: str, write_lock: threading.Lock = None) -> None:
    """
    1. Replace code: Replace the original code with the labeled content based on the function_info in covered_log_statement.json. The position needs to be corrected, and the replacement operation needs to be recorded.
    2. Test execution: mvn clean test -Dtest={test_name}
    3. Find logs printed by marked log statements in the log files
    """
    if os.path.exists(os.path.join(results_dir, "results.jsonl")):
        results_data = read_jsonl(os.path.join(results_dir, "results.jsonl"))
    else:
        results_data = []
    for index, item in enumerate(json_data):
        if use_catch_point and load_catch_point(results_data, item['uuid']):
            continue

        uuid = item['uuid']
        function_position = item['function_info']['function_position']
        function_lines = item['function_info']['function_lines']
        prediction_data = item['function_with_labeled_data']
        test_name = item.get('unit_test', 'UNKNOWN_TEST')
        execute_dir = item.get('execute_dir', 'UNKNOWN_TEST')

        if not execute_dir or not test_name or not prediction_data:
            logger.error(f"Missing required data for UUID: {uuid}")
            continue

        try:
            logger.info(f"--- Processing UUID: {uuid} ---")
            logger.info(f"--- Current Progress: {index}/{len(json_data)} ---")

            # 1. Replace code
            replace_func(function_position, function_lines, prediction_data,
                         uuid, replace_data_path, logger)

            # 2. Test execution
            logger.info(f"Running test: {test_name}")
            start_time = time.time()
            execute_success = run_maven_test(test_name, execute_dir, logger, record_error, record_error_path, uuid)
            execute_time = time.time() - start_time

            if not execute_success:
                save_result(execute_success, execute_time, 0, 0, results_dir, uuid, '', write_lock)
                logger.error(f"Failed to run test: {test_name}")
                continue

            logger.info(f"Test run success for {uuid}.")

            # 处理产生的日志
            log_file_dir = execute_dir + "/target/surefire-reports"
            if not os.path.exists(log_file_dir):
                logger.error(f"Log file directory not found: {log_file_dir}")
                save_result(False, execute_time, 0, 0, results_dir, uuid, '', write_lock)
                continue
            log_files = [f for f in os.listdir(log_file_dir) if f.endswith('output.txt')]
            test_log_content = ""
            for log_file in log_files:
                with open(os.path.join(log_file_dir, log_file), 'r', encoding='utf-8') as f:
                    test_log_content += f.read()
            complete_log_file_path = os.path.join(results_dir, 'complete_logs', f"{uuid}.txt")
            if not os.path.exists(complete_log_file_path):
                os.makedirs(os.path.dirname(complete_log_file_path), exist_ok=True)
            with open(complete_log_file_path, 'w', encoding='utf-8') as f:
                f.write(test_log_content)

            super_tag_lines = [line for line in test_log_content.split('\n') if '[SUPER TAG]' in line]
            result_file_path = os.path.join(results_dir, 'output_logs', f"{uuid}.txt")
            if not os.path.exists(result_file_path):
                os.makedirs(os.path.dirname(result_file_path), exist_ok=True)
            
            try:
                with open(result_file_path, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(super_tag_lines))
                logger.info(f"Successfully saved [SUPER TAG] logs to {result_file_path}")

                # get absolute path of write file
                file_location = os.path.abspath(result_file_path)
                save_result(execute_success, execute_time, os.path.getsize(result_file_path), os.path.getsize(complete_log_file_path), results_dir, uuid, file_location, write_lock)
            except Exception as e:
                logger.error(f"Failed to save [SUPER TAG] logs for UUID {uuid}: {e}")

        except Exception as e:
            logger.error(f"Failed processing UUID {uuid}: {e}")
        finally:
            logger.info(
                f"Attempting to reverse changes for failed UUID: {uuid}")
            try:
                reverse_func(uuid, replace_data_path, logger)
            except Exception as reverse_e:
                logger.error(
                    f"Failed to reverse changes for UUID {uuid}: {reverse_e}")
                sys.exit(1)
            logger.info(f"--- End Process UUID: {uuid} ---")

def classify_data_for_multi_thread(json_data: List[Dict]) -> Dict[str, List[Dict]]:
    """
    1. Filter json data: If function_with_labeled_data is empty, filter it
    2. Classify json data: Classify json data by execute_dir
    3. Classify json data by unit_test: Classify json data by unit_test in each execute_dir

    return a dictionary, key is execute_dir, value is a list of unit_test
    """
    classify_data = {}
    for item in json_data:
        if item['function_with_labeled_data'] is None:
            continue
        execute_dir = item['execute_dir']
        if execute_dir not in classify_data:
            classify_data[execute_dir] = []
        classify_data[execute_dir].append(item)
    return classify_data

def execute_unittest_thread(json_path: str, replace_data_path: str, results_dir: str, logger: logging.Logger, use_catch_point: bool, record_error: bool, record_error_path: str, num_thread: int) -> None:
    """
    return a dictionary, key is execute_dir, value is a list of unit_test, different execute_dir can be processed in parallel
    """
    if not os.path.exists(json_path):
        logger.error(f"Json file not found: {json_path}")
        return
    json_data = read_json(json_path)
    classify_data = classify_data_for_multi_thread(json_data)
    if num_thread == 1:
        for _, data_item_list in classify_data.items():
            execute_unittest(data_item_list, replace_data_path, results_dir, logger, use_catch_point, record_error, record_error_path)
            project_name = '/'.join(data_item_list[0]['execute_dir'].split('/')[3:])
            logger.info(f"Project {project_name} completed successfully")
            logger.info(f"==========Current progress: {index + 1}/{len(classify_data)}==========")
    else:
        write_lock = threading.Lock()
        with ThreadPoolExecutor(max_workers=num_thread) as executor:
            futures = {
                executor.submit(execute_unittest, data_item_list, replace_data_path, results_dir, logger, use_catch_point, record_error, record_error_path, write_lock): data_item_list
                for data_item_list in classify_data.values()
            }
            for index, future in enumerate(as_completed(futures)):
                data_item_list = futures[future]
                try:
                    future.result()
                    project_name = '/'.join(data_item_list[0]['execute_dir'].split('/')[3:])
                    logger.info(f"Project {project_name} completed successfully")
                except Exception as e:
                    logger.error(f"Error processing project {data_item_list}: {e}")
                logger.info(f"==========Current progress: {index + 1}/{len(classify_data)}==========")

def main():

    # Create argument parser
    parser = argparse.ArgumentParser(
        description='Execute unit tests and collect logs')

    # Add arguments
    parser.add_argument('--execute_id', type=str, default="hadoop_major_test_2",
                        help='execute id')
    parser.add_argument('--results_dir', type=str, default="/home/al-bench/AL-Bench/Dynamic_Evaluation/build_dataset/get_logs_output/results",help='Directory path for storing results (in docker)')

    parser.add_argument('--json_path', type=str, default="/home/al-bench/AL-Bench/Dynamic_Evaluation/build_dataset/find_covered_log_statement/data/hadoop_major_test/result/covered_log_statement.json",help='Path to the JSON file (in docker)')
    parser.add_argument('--use_catch_point', action='store_true',
                        help='Skip already processed UUIDs based on results.jsonl')
    parser.add_argument('--record_error', action='store_true',
                        help='Record error')
    parser.add_argument('--num_thread', type=int, default=4,
                        help='Number of threads')

    # Parse arguments
    args = parser.parse_args()

    # Get argument values
    execute_id = args.execute_id
    results_dir = os.path.join(args.results_dir, execute_id)
    log_dir = os.path.join(results_dir, "log")
    replace_data_path = os.path.join(results_dir, "replace_data")
    record_error_path = os.path.join(results_dir, "build_error_log")

    json_path = args.json_path
    use_catch_point = args.use_catch_point
    record_error = args.record_error
    num_thread = args.num_thread

    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    if not os.path.exists(results_dir):
        os.makedirs(results_dir)

    if not os.path.exists(replace_data_path):
        os.makedirs(replace_data_path)

    if record_error and not os.path.exists(record_error_path):
        os.makedirs(record_error_path)

    logger = setup_logging(log_dir, log_level=logging.INFO)

    # Process json data to support multi-threading
    execute_unittest_thread(json_path, replace_data_path, results_dir, logger, use_catch_point, record_error, record_error_path, num_thread)


if __name__ == "__main__":
    main()
