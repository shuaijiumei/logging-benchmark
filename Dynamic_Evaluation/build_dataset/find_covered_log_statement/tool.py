# 配置日志记录
import logging
import os
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any
import re

def setup_logging(log_dir: str) -> logging.Logger:
    """设置日志记录配置"""
    # 确保日志目录存在
    os.makedirs(log_dir, exist_ok=True)
    
    # 创建日志文件名，包含时间戳（北京时间）
    timestamp = datetime.now().astimezone(timezone(timedelta(hours=8))).strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"test_run_{timestamp}.log")
    
    # 配置日志记录
    logger = logging.getLogger("test_runner")
    logger.setLevel(logging.INFO)
    
    # 文件处理器
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.INFO)
    
    # 设置日志格式（使用北京时间）
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    formatter.converter = lambda *args: datetime.now().astimezone(timezone(timedelta(hours=8))).timetuple()
    file_handler.setFormatter(formatter)
    
    # 只添加文件处理器，不添加控制台处理器
    logger.addHandler(file_handler)
    
    return logger

def remove_java_comments(code: str) -> str:
    """
    Remove all Java comments from code
    
    Args:
        code: Java source code as a string
    
    Returns:
        The code with all comments removed
    """
    # Remove all single-line comments //
    code = re.sub(r'//.*?$', '', code, flags=re.MULTILINE)
    # Remove all multi-line comments /* */
    code = re.sub(r'/\*[\s\S]*?\*/', '', code)
    # Remove leading newline if exists
    if code.startswith("\n"):
        code = code[1:]
    return code

def replace_log_statements(source_code: str, covered_logs: list, replace_target: str = "empty", all_logs: list = []) -> str:
    """
    从源代码中移除或标记指定的日志语句
    
    Args:
        source_code: 源代码字符串
        covered_logs: 要处理的日志信息列表
        replace_target: 处理方式，只能是 "empty"(移除) 或 "label"(标记)，默认为"empty"
        
    Returns:
        处理后的源代码字符串
    """
    # 验证 replace_target 参数
    if replace_target not in ["empty", "label"]:
        raise ValueError("replace_target must be either 'empty' or 'label'")
    
    result = source_code
    
    # 处理日志语句
    for log in covered_logs:
        if "statement" in log:
            if replace_target == "empty":
                result = result.replace(log["statement"] + ";\n", "")
            elif replace_target == "label":
                labeled_statement = label_data(log["statement"])
                result = result.replace(log["statement"], labeled_statement)
    
    # 清理多余的空行
    result = result.replace("\n\n", "\n")
    
    return result

def label_data(log_state: str) -> str:
    """标记数据"""
    return log_state.split('(')[0] + '(\"[SUPER TAG]\" + ' + '('.join(log_state.split('(')[1:])

def judge_bad_pattern_functions(log_list: List[Dict[str, Any]]) -> bool:
    """判断 bad pattern 的函数"""
    # 1. 存在重复的日志语句，该 item 被视为 bad pattern
    # 2. 存在日志语句中存在重复的变量，该 item 被视为 bad pattern
    # 3. 存在日志语句中有连续重复特殊字符，该 item 被视为 bad pattern

    # 1. 存在重复的日志语句，该 item 被视为 bad pattern
    log_list_content = [log["statement"] for log in log_list]
    if len(log_list_content) != len(set(log_list_content)):
        return True
    
    # 2. 存在日志语句中存在重复的变量，该 item 被视为 bad pattern
    for log in log_list:
        if len(log['vars']) != len(set(log['vars'])):
            return True
        
    # 3. 存在日志语句中有连续重复特殊字符，该 item 被视为 bad pattern
    for log in log_list_content:
        if re.search(r'([^a-zA-Z0-9\s])\1\1+', log):
            return True
    # 如果存在日志语句为空，则该 item 被视为 bad pattern
    for log in log_list_content:
        if log.strip() == "":
            return True
    
    return False
