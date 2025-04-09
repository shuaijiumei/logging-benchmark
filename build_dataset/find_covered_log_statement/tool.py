# 配置日志记录
import logging
import os
from datetime import datetime
from typing import List, Dict, Any
import re

def setup_logging(log_dir: str) -> logging.Logger:
    """设置日志记录配置"""
    # 确保日志目录存在
    os.makedirs(log_dir, exist_ok=True)
    
    # 创建日志文件名，包含时间戳
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"test_run_{timestamp}.log")
    
    # 配置日志记录
    logger = logging.getLogger("test_runner")
    logger.setLevel(logging.INFO)
    
    # 文件处理器
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.INFO)
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # 设置日志格式
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # 添加处理器到日志记录器
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
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

def replace_log_statements(source_code: str, covered_logs: list, replace_target: str = "empty") -> str:
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