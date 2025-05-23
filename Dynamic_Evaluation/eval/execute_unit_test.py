#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@File: execute_unittest.py
@Author: shuaijiumei
@Email: BoyinTan1221@gmail.com
@Date: 2025-04-12
@Description: 
  Execute unit tests and collect logs, reuse the execute_unittest.py in build_dataset
"""

import os
import argparse
import logging

from Dynamic_Evaluation.build_dataset.get_logs_output.tool import setup_logging
from Dynamic_Evaluation.build_dataset.get_logs_output.execute_unittest import execute_unittest_thread


def main():

    # Create argument parser
    parser = argparse.ArgumentParser(
        description='Execute unit tests and collect logs')

    # Add arguments
    parser.add_argument('--execute_id', type=str, default="hadoop_major_test_2",
                        help='execute id')
    parser.add_argument('--results_dir', type=str, default="/home/al-bench/AL-Bench/Dynamic_Evaluation/get_logs_output/results",help='Directory path for storing results (in docker)')

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

    execute_unittest_thread(json_path, replace_data_path, results_dir, logger, use_catch_point, record_error, record_error_path, num_thread)


if __name__ == "__main__":
    main()
