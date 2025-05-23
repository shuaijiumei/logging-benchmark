import json
import os
import sys
import xml.etree.ElementTree as ET
from typing import Dict, List, Any, Tuple, Optional
from functools import reduce
import argparse
import uuid
from tqdm import tqdm
from tool import remove_java_comments, replace_log_statements, setup_logging, judge_bad_pattern_functions
import logging

def load_hadoop_data(file_path: str = "./data/hadoop-cleaned.json") -> List[Dict[str, Any]]:
    """加载 Hadoop 数据文件"""
    with open(file_path, "r") as f:
        return json.load(f)

def parse_xml_file(file_path: str, logger: logging.Logger) -> ET.Element:
    """解析 XML 文件并返回根元素"""
    try:
        tree = ET.parse(file_path)
        return tree.getroot()
    except Exception as e:
        logger.error(f"Error processing XML file: {e}")
        sys.exit(1)

def is_log_line(line: str) -> bool:
    """判断一行代码是否是日志语句"""
    return line.strip().lower().startswith("log.")

def extract_log_line(file_path: str, line_number: int, logger: logging.Logger) -> Optional[str]:
    """从给定文件中提取指定行号的日志语句"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.read().splitlines()
            if 0 <= line_number - 1 < len(lines):
                content = lines[line_number - 1]
                return content.strip() if is_log_line(content) else None
    except Exception as e:
        logger.debug(f"Error reading file {file_path}: {e}")
    return None

def find_covered_logs(root: ET.Element, base_dir: str, logger: logging.Logger) -> List[Dict[str, Any]]:
    """查找被覆盖的日志语句"""
    covered_logs = []
    
    for pkg in root.findall(".//package"):
        pkg_name = pkg.get("name")
        
        for sourcefile in pkg.findall(".//sourcefile"):
            file_name = sourcefile.get("name")
            full_file_name = f"{pkg_name}/{file_name}"
            
            for line in sourcefile.findall(".//line"):
                if int(line.get("ci")) > 0:  # 检查行是否被覆盖
                    line_number = int(line.get("nr"))
                    file_path = os.path.join(base_dir, full_file_name)
                    log_line = extract_log_line(file_path, line_number, logger)
                    if log_line:
                        covered_logs.append({
                            "lineNumber": line_number,
                            "logLine": log_line,
                            "position": file_path
                        })
    
    return covered_logs

def is_line_in_function(log_entry: Dict[str, Any], function_data: Dict[str, Any]) -> bool:
    """判断日志行是否在函数范围内"""
    func_start, func_end = map(int, function_data["function_lines"].split("-"))
    position_match = log_entry["position"].find(
        function_data["function_position"]
    ) != -1
    
    return (func_start <= log_entry["lineNumber"] <= func_end) and position_match

def match_logs_to_functions(covered_logs: List[Dict[str, Any]], 
                           hadoop_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """将日志行与函数关联，避免生成重复的函数数据"""
    result = {}
    
    # 为每个函数创建唯一key
    for func in hadoop_data:
        key = func["function_name"] + func["function_position"] + func["function_lines"]
        if key not in result:
            # 创建函数的副本并初始化covered_log列表
            func_copy = func.copy()
            func_copy["covered_log"] = []
            result[key] = func_copy
    
    # 将日志匹配到函数中
    for log_entry in covered_logs:
        for func_key, func_data in result.items():
            if is_line_in_function(log_entry, func_data):
                func_data["covered_log"].append(log_entry["logLine"])
    
    # 过滤掉没有匹配到日志的函数
    return [func for func in result.values() if func["covered_log"]]

def extract_complete_log_statements(item: Dict[str, Any], logger: logging.Logger) -> Dict[str, Any]:
    """
    从函数源代码中提取完整的日志语句
    
    Args:
        item: 包含函数信息和部分日志的字典
        
    Returns:
        更新后的函数信息字典，包含完整的日志语句
    """
    # 保存原始部分日志内容
    covered_part_logs = item.get("covered_log", [])
    # 重置日志列表
    item["covered_log"] = []
    
    try:
        # 读取函数源码
        with open(item["function_position"], "r", encoding="utf-8") as f:
            content = f.read()
        
        # 提取函数实际内容
        start_line = int(item["function_lines"].split("-")[0].strip())
        end_line = int(item["function_lines"].split("-")[1].strip())
        lines = content.split("\n")
        content_lines = lines[start_line - 1:end_line]
        
        # 查找完整日志语句
        for log_part in covered_part_logs:
            flag = False
            log_lines = []
            
            # 清理之前查找的日志行
            if log_lines:
                for log_line in log_lines:
                    if log_line in content_lines:
                        content_lines.remove(log_line)
                log_lines = []
            
            # 在源码中查找完整日志语句
            for i, line in enumerate(content_lines):
                if flag:
                    log_lines.append(line)
                if flag and line.strip().endswith(";"):
                    flag = False
                    break
                if line.strip() == log_part.strip():
                    log_lines.append(line)
                    if not line.strip().endswith(";"):
                        flag = True
                    else:
                        # 如果以 ; 结尾，代表这条日志语句已经完了
                        break
            
            # 查找匹配的日志语句
            if log_lines and "log_detailsList" in item:
                for log_detail in item.get("log_detailsList", []):
                    if all(log_element.strip() in (log_detail.get("statement", "") + ";") 
                           for log_element in log_lines):
                        item["covered_log"].append(log_detail)
                        break
    except Exception as e:
        logger.error(f"Error processing {item['function_position']}: {e}")
    
    return item

def process_covered_data(functions_with_covered_logs: List[Dict[str, Any]], logger: logging.Logger, unit_test, execute_dir) -> List[Dict[str, Any]]:
    
    # 处理函数中的完整日志语句
    processed_result = [extract_complete_log_statements(item, logger) for item in functions_with_covered_logs]
    
    # 过滤出包含覆盖日志的函数
    filtered_data = [item for item in processed_result if item.get("covered_log")]
    
    # 生成没有日志的函数内容，添加 UUID
    result_data = []
    for item in filtered_data:
        source_code_info = {
            'function_name': item['function_name'],
            'function_position': item['function_position'],
            'function_lines': item['function_lines'],
            'function_content': item['function_content'],
            'function_content_without_logs': item['function_without_logs'],
            'log_detailsList': item['log_detailsList'],
        }
        item["function_content_without_covered_logs"] = item["function_content"]


        # 使用这个函数替换原来的代码
        item["function_content_without_covered_logs"] = replace_log_statements(
            item["function_content"], item.get("covered_log", []), replace_target="empty", all_logs=item.get("log_detailsList", [])
        )

        # 新建一个 function_with_labeled_data
        item["function_with_labeled_data"] = replace_log_statements(
            item["function_content"], item.get("covered_log", []), replace_target='label', all_logs=item.get("log_detailsList", [])
        )

        # 去掉 Java 代码中的所有注释
        if "function_content_without_covered_logs" in item:
            item["function_content_without_covered_logs"] = remove_java_comments(item["function_content_without_covered_logs"])

        result_data.append({
            'function_info': source_code_info,
            'covered_log': item['covered_log'],
            'unit_test': unit_test,
            'execute_dir': execute_dir + '/',
            'function_content_without_covered_logs': item['function_content_without_covered_logs'],
            'function_with_labeled_data': item['function_with_labeled_data'],
            'uuid': str(uuid.uuid4())
        })

    return result_data

def deduplicate_by_log_coverage(all_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
  """
  处理结果数据，保留每个函数中日志覆盖最多的单元测试
  
  Args:
    all_results: 所有函数的覆盖日志信息
    
  Returns:
    去重后的结果，每个函数只保留覆盖日志最多的单元测试
  """
  # 按函数分组
  function_groups = {}
  for item in all_results:
    func_info = item['function_info']
    key = func_info['function_name'] + func_info['function_position'] + func_info['function_lines']
    
    if key not in function_groups:
      function_groups[key] = []
    function_groups[key].append(item)
  
  # 为每个函数选择覆盖日志最多的测试
  deduplicated_results = []
  for key, items in function_groups.items():
    # 按覆盖的日志数量排序
    items.sort(key=lambda x: len(x.get('covered_log', [])), reverse=True)
    # 取覆盖日志最多的那一条
    best_item = items[0]
    
    deduplicated_results.append(best_item)
  
  return deduplicated_results


def save_results(covered_functions: List[Dict[str, Any]], save_path: str) -> None:
    """保存结果到文件"""

    unique_covered_functions = deduplicate_by_log_coverage(covered_functions)
    if unique_covered_functions:
        with open(save_path, "w") as f:
            json.dump(unique_covered_functions, f, indent=2)

def clean_bad_pattern_functions(functions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """清理 bad pattern 的函数"""
    cleaned_functions = []
    for function in functions:
        if not judge_bad_pattern_functions(function['function_info']['log_detailsList']):
            cleaned_functions.append(function)
    return cleaned_functions


def extract_covered_logs(data_dir: str, source_code_dir: str, code_json: str, 
                         save_dir: str, logger: logging.Logger) -> None:
    """提取被覆盖的日志语句的主要功能
    
    Args:
        data_dir: 包含项目数据的目录
        source_code_dir: 源代码目录的路径
        code_json: 包含日志语句信息的JSON文件路径
        save_dir: 保存提取的覆盖日志语句的路径
    """
    # 检查路径是否存在
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        logger.info(f"Created data directory: {data_dir}")

    # 加载日志数据
    logger.info(f"Loading Hadoop data from {code_json}")
    hadoop_data = load_hadoop_data(code_json)
    logger.info(f"Loaded Hadoop data successfully")
    
    # 递归搜索所有 jacoco.xml 文件
    xml_files = []
    for root_dir, dirs, files in os.walk(data_dir):
      # 只处理包含 "jacoco" 的文件夹
      if "jacoco" not in root_dir:
          continue

      # 检查是否存在兄弟文件夹 surefire-reports
      parent_dir = os.path.dirname(root_dir)
      surefire_dir = os.path.join(parent_dir, "surefire-reports")
      if not os.path.exists(surefire_dir):
          continue
          
      # 检查 surefire-reports 下是否有 -output.txt 文件
      has_output_file = any(file.endswith("-output.txt") for file in os.listdir(surefire_dir))
      if not has_output_file:
          continue
      for file in files:
        if file == "jacoco.xml":
          xml_path = os.path.join(root_dir, file)
          output_path = os.path.join(os.path.dirname(root_dir), "covered_log_statement.json")
          unit_test = root_dir.split('/')[-2]
          execute_dir = source_code_dir + '/'.join(root_dir.replace(data_dir, "").split('/')[:-2])
          project_base_dir = execute_dir + '/src/main/java/'
          xml_files.append((xml_path, output_path, project_base_dir, unit_test, execute_dir))

    # Initialize a list to collect all results
    all_results = []
    
    logger.info(f"Found {len(xml_files)} XML files to process")
    for index, (xml_path, _, project_base_dir, unit_test, execute_dir) in enumerate(xml_files):
      try:
        # 解析 XML 文件
        logger.info(f"Processing file {index + 1}/{len(xml_files)}: {xml_path}")
        root = parse_xml_file(xml_path, logger)
        
        # 执行主要处理逻辑
        covered_logs = find_covered_logs(root, project_base_dir, logger)
        # logger.info(f"Found {len(covered_logs)} covered logs")
        
        covered_functions = match_logs_to_functions(covered_logs, hadoop_data)
        # logger.info(f"Matched logs to {len(covered_functions)} functions")
        
        result = process_covered_data(covered_functions, logger, unit_test, execute_dir)

        # 清理 bad pattern 的函数
        result = clean_bad_pattern_functions(result)
        
        # Add results to the collected list
        if result:
          all_results.extend(result)
        #   logger.info(f"Added {len(result)} results")
      except Exception as e:
        logger.error(f"Error processing {xml_path}: {e}")
    
    # Save all results to a single output file
    if all_results:
      logger.info(f"Saving {len(all_results)} results to {save_dir}")
      save_results(all_results, save_dir)
      logger.info(f"All results saved to {save_dir}")
    else:
      logger.info("No results found to save")

def main():
    """命令行入口函数"""
    # 从命令行获得 data_dir 参数 
    parser = argparse.ArgumentParser(description='Extract covered log statements from xml file')
    parser.add_argument('--data-dir', type=str, help='Directory containing the project data', default='/home/al-bench/AL-Bench/Dynamic_Evaluation/find_covered_log_statement/data')
    parser.add_argument('--source-code-dir', type=str, help='Path to the Source Code Directory', default="/home/al-bench/hadoop-3.4.0-src")
    parser.add_argument('--code-json', type=str, help='Path to the Json file containing log statement information', default="./code_data/hadoop-log-statement-data.json")
    parser.add_argument('--save-dir', type=str, help='The project path in docker container', default="./code_data/covered_log_statement.json")
    parser.add_argument('--log-dir', type=str, help='The log directory', default="./log")
    parser.add_argument('--execute-id', type=str, help='The id of the execution', default="hadoop_major_test")
    args = parser.parse_args()
    logger = setup_logging(args.log_dir)

    target_dir = args.data_dir + '/' + args.execute_id + '/target'
    
    # 调用主要功能函数
    extract_covered_logs(
        data_dir=target_dir,
        source_code_dir=args.source_code_dir,
        code_json=args.code_json,
        save_dir=args.save_dir,
        logger=logger
    )

if __name__ == "__main__":
    main()
