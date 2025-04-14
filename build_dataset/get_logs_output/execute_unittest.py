#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@File: execute_unittest.py
@Author: shuaijiumei
@Email: BoyinTan1221@gmail.com
@Date: 2025-4-10
@Description: 
  主要实现三个功能： 替换函数 + 运行测试 + 处理日志
  1. 替换函数：对文件进行操作，将原本有的内容替换成 label 后的。 这个操作要记录下来，以免突然停止导致原本的代码被破坏
  2. 运行测试， mvn clean test -Dtest={test_name}
  3. 在日志中找到被标记的 log statement 打印的日志

"""

import os
import json
import logging
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Union, Optional
from tool import setup_logging, replace_func, reverse_func, read_jsonl, read_json
import argparse
import shutil  # 需要导入 shutil 以便在 os.replace 不可用时回退 (虽然 os.replace 通常更好)
import time

def load_catch_point(results_data: List[Dict], uuid: str) -> bool:
    for item in results_data:
        if item['uuid'] == uuid:
            return True
    return False

def save_result(execute_success: bool, execute_time: float, file_size: float, results_dir: str, uuid: str) -> None:
    result_item = {
        "uuid": uuid,
        "execute_success": execute_success,
        'execute_time': execute_time,
        'file_size': file_size
    }
    with open(os.path.join(results_dir, "results.jsonl"), 'a', encoding='utf-8') as f:
        f.write(json.dumps(result_item) + '\n')

def run_maven_test(test_name: str, mvn_dir: str, logger: logging.Logger, record_error: bool, record_error_path: str, uuid: str) -> bool:
    try:
        """运行 Maven 测试"""
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
        # 记录详细的错误输出
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



def execute_unittest(json_data: List[Dict], replace_data_path: str, results_dir: str, logger: logging.Logger, use_catch_point: bool, record_error: bool, record_error_path: str) -> None:
    """
    1. 替换代码，根据 covered_log_statement.json 中的 function_info 来替换源码，要对位置进行修正，并且对替换操作进行记录。

    2. 运行单元测试，并收集日志

    3. 根据 [SUPER TAG] 标记提取日志的 content

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
        # 注意：这里您使用的是 'function_with_labeled_data'，我在 replace_func 中参数名是 prediction
        # 请确保传递正确的参数。假设 prediction 就是 function_with_labeled_data
        prediction_data = item['function_with_labeled_data']
        # 假设 test_name 在 item 中或者可以推断出来
        test_name = item.get('unit_test', 'UNKNOWN_TEST')  # 需要确定测试名称的来源
        # 假设 mvn_dir 需要传入或可以确定
        execute_dir = item.get('execute_dir', 'UNKNOWN_TEST')  # 需要确定测试名称的来源

        if not execute_dir or not test_name or not prediction_data:
            logger.error(f"Missing required data for UUID: {uuid}")
            continue

        try:
            logger.info(f"--- Processing UUID: {uuid} ---")
            logger.info(f"--- Current Progress: {index}/{len(json_data)} ---")

            # 1. 替换代码
            replace_func(function_position, function_lines, prediction_data,
                         uuid, replace_data_path, logger)

            # 2. 运行单元测试 (示例，需要您完善日志收集逻辑)
            logger.info(f"Running test: {test_name}")
            start_time = time.time()
            execute_success = run_maven_test(test_name, execute_dir, logger, record_error, record_error_path, uuid)
            execute_time = time.time() - start_time

            if not execute_success:
                # 如果没有编译成功，则不进行后续处理，直接记录结果
                save_result(execute_success, execute_time, 0, results_dir, uuid)
                logger.error(f"Failed to run test: {test_name}")
                continue

            logger.info(f"Test run success for {uuid}.")

            # 处理产生的日志
            log_file_dir = execute_dir + "/target/surefire-reports"
            if not os.path.exists(log_file_dir):
                logger.error(f"Log file directory not found: {log_file_dir}")
                save_result(False, execute_time, 0, results_dir, uuid)
                continue
            # 获取所有以output.txt结尾的日志文件
            log_files = [f for f in os.listdir(log_file_dir) if f.endswith('output.txt')]
            # 读取所有日志文件内容
            test_log_content = ""
            for log_file in log_files:
                with open(os.path.join(log_file_dir, log_file), 'r', encoding='utf-8') as f:
                    test_log_content += f.read()
            # 将日志内容保存到 complete_logs 文件夹
            complete_log_file_path = os.path.join(results_dir, 'complete_logs', f"{uuid}.txt")
            if not os.path.exists(complete_log_file_path):
                os.makedirs(os.path.dirname(complete_log_file_path), exist_ok=True)
            with open(complete_log_file_path, 'w', encoding='utf-8') as f:
                f.write(test_log_content)

            # 直接筛选出包含 [SUPER TAG] 的行，即使为空也继续处理
            super_tag_lines = [line for line in test_log_content.split('\n') if '[SUPER TAG]' in line]
            # 将包含 [SUPER TAG] 的日志内容保存到结果文件夹
            result_file_path = os.path.join(results_dir, 'output_logs', f"{uuid}.txt")
            if not os.path.exists(result_file_path):
                os.makedirs(os.path.dirname(result_file_path), exist_ok=True)
            
            try:
                with open(result_file_path, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(super_tag_lines))
                logger.info(f"Successfully saved [SUPER TAG] logs to {result_file_path}")

                save_result(execute_success, execute_time, os.path.getsize(result_file_path), results_dir, uuid)
            except Exception as e:
                logger.error(f"Failed to save [SUPER TAG] logs for UUID {uuid}: {e}")

        except Exception as e:
            logger.error(f"Failed processing UUID {uuid}: {e}")
        finally:
            # 无论成功与否，都尝试恢复代码，确保环境干净以处理下一个 item 或结束
            logger.info(
                f"Attempting to reverse changes for failed UUID: {uuid}")
            try:
                reverse_func(uuid, replace_data_path, logger)
            except Exception as reverse_e:
                logger.error(
                    f"Failed to reverse changes for UUID {uuid}: {reverse_e}")
            logger.info(f"--- End Process UUID: {uuid} ---")

    # 循环结束后，可以统一处理 results
    logger.info("--- Processing Complete ---")


def main():

    # Create argument parser
    parser = argparse.ArgumentParser(
        description='Execute unit tests and collect logs')

    # Add arguments
    parser.add_argument('--execute_id', type=str, default="tag_execute_2",
                        help='execute id')
    parser.add_argument('--results_dir', type=str, default="/home/al-bench/AL-Bench/build_dataset/get_logs_output/results",help='Directory path for storing results (in docker)')

    
    parser.add_argument('--json_path', type=str, default="/home/al-bench/AL-Bench/build_dataset/find_covered_log_statement/code_data/covered_log_statement.json",
                        help='Path to the JSON file (in docker)')
    parser.add_argument('--use_catch_point', action='store_true',
                        help='Skip already processed UUIDs based on results.jsonl')
    parser.add_argument('--record_error', action='store_true',
                        help='Record error')
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

    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    if not os.path.exists(results_dir):
        os.makedirs(results_dir)

    if not os.path.exists(replace_data_path):
        os.makedirs(replace_data_path)

    if record_error and not os.path.exists(record_error_path):
        os.makedirs(record_error_path)

    logger = setup_logging(log_dir, log_level=logging.INFO)

    # 读取 json 文件
    json_data = read_json(json_path)

    execute_unittest(json_data, replace_data_path, results_dir, logger, use_catch_point, record_error, record_error_path)


if __name__ == "__main__":
    main()
