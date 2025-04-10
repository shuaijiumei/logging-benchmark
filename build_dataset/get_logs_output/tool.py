# 配置日志
import logging
from typing import Optional
import datetime
import os
import json
from pathlib import Path
import sys
import shutil  # 确保导入
from typing import List, Dict


def read_jsonl(file_path: str) -> List[Dict]:
    """读取 jsonl 文件，返回包含所有 JSON 对象的列表"""
    data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            data.append(json.loads(line))
    return data


def read_json(json_path: str) -> List[Dict]:
    """读取 json 文件"""
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def setup_logging(log_path: Optional[str] = None, log_level: int = logging.INFO) -> logging.Logger:
    """配置日志记录并返回logger实例

    Args:
        log_file: 日志文件路径，如果为None则输出到控制台
        log_level: 日志级别，默认为INFO

    Returns:
        logging.Logger: 配置好的logger实例
    """
    logger = logging.getLogger(__name__)
    logger.setLevel(log_level)

    # 清除已有handler，避免重复添加
    if logger.hasHandlers():
        logger.handlers.clear()

    # 创建handler
    if log_path:
        log_file = os.path.join(
            log_path, f'execute_unittest_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
        handler = logging.FileHandler(log_file)
    else:
        handler = logging.StreamHandler()

    # 设置日志格式
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)

    # 添加handler
    logger.addHandler(handler)

    return logger


def replace_func(position: str, function_lines: str, prediction: str, uuid: str, replace_data_path: str, docker_path: str, real_path: str, logger: logging.Logger) -> None:
    """
    替换函数实现 (使用临时文件和原子替换保证安全)
    """
    replace_record_data = {}
    replace_obj = {}
    replace_location_str = position.replace(real_path, docker_path)
    replace_location = Path(replace_location_str)
    tmp_location = Path(f"{replace_location_str}.tmp")  # 定义临时文件路径

    try:
        # --- 1. 读取原始文件内容 ---
        try:
            with open(replace_location, 'r', encoding='utf-8') as f:
                content = f.read()
        except FileNotFoundError:
            logger.error(
                f"Error: Original file not found at {replace_location}")
            # 根据需要决定是否抛出异常或退出
            return  # 或者 sys.exit(1)

        # --- 2. 计算替换内容 ---
        start_line = int(function_lines.split("-")[0].strip())
        end_line = int(function_lines.split("-")[1].strip())
        lines = content.split("\n")
        # 获取需要替换的内容
        function_content = "\n".join(lines[start_line - 1:end_line])

        replace_obj = {
            "target": function_content,
            "replacement": prediction,
            "lines": function_lines
        }

        # --- 3. 生成新文件内容 ---
        # 注意：str.replace 可能会替换掉非预期的部分，如果函数内容可能在其他地方重复出现。
        # 一个更精确的方法是按行替换，但这会更复杂。
        # 假设当前的 str.replace 满足需求。
        new_content = content.replace(
            replace_obj["target"], replace_obj["replacement"])

        # 验证替换是否发生 (可选但推荐)
        if new_content == content and replace_obj["target"] != replace_obj["replacement"]:
            logger.warning(
                f"Replacement target not found in file {replace_location} for UUID {uuid}. The file content might have changed unexpectedly.")
            # 根据需要决定是否继续，这里我们假设可能就是没找到（例如，之前已经恢复过）
            # 或者可以抛出异常: raise ValueError("Replacement target not found")

        # --- 4. 记录替换信息到 JSON (先于文件修改) ---
        replace_record_data = {
            "file_path": replace_location_str,  # 存储字符串路径可能更通用
            "replace_obj": replace_obj
        }
        replace_log_path = Path(replace_data_path) / \
            f"{uuid}.json"  # 使用 Path 构造路径

        try:
            replace_log_path.parent.mkdir(
                parents=True, exist_ok=True)  # 确保目录存在
            with open(replace_log_path, 'w', encoding='utf-8') as f:
                json.dump(replace_record_data, f, indent=2)  # 美化 JSON 输出
        except Exception as e:
            logger.error(
                f"Error writing replacement log to {replace_log_path}: {e}")
            # 考虑是否应该在此处停止，因为没有日志就无法恢复
            raise e

        # --- 5. 将新内容写入临时文件 ---
        try:
            with open(tmp_location, 'w', encoding='utf-8') as f:
                f.write(new_content)
        except Exception as e:
            logger.error(
                f"Error writing to temporary file {tmp_location}: {e}")
            # 尝试删除临时文件（如果已创建）
            if tmp_location.exists():
                try:
                    tmp_location.unlink()
                except OSError as unlink_err:
                    logger.warning(
                        f"Could not remove temporary file {tmp_location}: {unlink_err}")
            raise  # 重新抛出异常

        # --- 6. 原子性替换原文件 ---
        try:
            # os.replace 在大多数现代系统上是原子性的
            os.replace(tmp_location, replace_location)
            logger.info(
                f"Successfully replaced content in {replace_location} (UUID: {uuid})")
        except OSError as e:
            logger.error(
                f"Error replacing file {replace_location} with {tmp_location}: {e}")
            if tmp_location.exists():
                try:
                    tmp_location.unlink()
                except OSError as unlink_err:
                    logger.warning(
                        f"Could not remove temporary file {tmp_location}: {unlink_err}")
            raise  # 重新抛出异常

    except Exception as e:
        # 捕获上面重新抛出的异常或其他未预料的错误
        logger.error(f"Failed to replace function for UUID {uuid}. Error: {e}")
        # 这里可以添加额外的清理或通知逻辑
        # 注意：如果是在写入日志文件后、替换文件前失败，日志文件可能需要手动处理
        # 如果是在替换文件时失败，原文件应该保持不变
        raise


def reverse_func(uuid: str, replace_data_path: str, logger: logging.Logger) -> None:
    """
    恢复函数实现 (使用临时文件和原子替换保证安全)
    根据 {uuid}.json 文件将对应文件恢复到替换前的状态。
    """
    json_log_path = Path(replace_data_path) / f"{uuid}.json"
    bak_log_path = Path(replace_data_path) / f"{uuid}.bak"
    restore_tmp_path = None  # 初始化临时文件路径变量

    try:
        # --- 1. 检查并读取 JSON 日志文件 ---
        if not json_log_path.exists():
            # 检查是否已经恢复过 (存在 .bak 文件)
            if bak_log_path.exists():
                logger.info(
                    f"File for UUID {uuid} seems already reversed (found .bak file). Skipping reverse.")
                return
            else:
                logger.error(
                    f"Reverse log file not found: {json_log_path}. Cannot reverse changes for UUID {uuid}.")
                return  # 或者可以根据需要抛出异常

        try:
            with open(json_log_path, 'r', encoding='utf-8') as f:
                replace_record_data = json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON from {json_log_path}: {e}")
            # 考虑是否将文件重命名为 .error 或其他标记，防止重复尝试
            # os.rename(json_log_path, json_log_path.with_suffix('.error'))
            return  # 无法解析则无法恢复
        except Exception as e:
            logger.error(
                f"Error reading reverse log file {json_log_path}: {e}")
            return

        # --- 2. 解析替换记录 ---
        try:
            file_path_str = replace_record_data["file_path"]
            replace_obj = replace_record_data["replace_obj"]
            target_content = replace_obj["target"]       # 原始内容
            replaced_content = replace_obj["replacement"]  # 被替换成的内容
            file_path = Path(file_path_str)
            restore_tmp_path = Path(f"{file_path_str}.rev.tmp")  # 定义恢复用的临时文件
        except KeyError as e:
            logger.error(
                f"Invalid format in reverse log file {json_log_path}. Missing key: {e}")
            # 同样，考虑标记此文件
            return

        # --- 3. 读取当前文件内容 ---
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                current_content = f.read()
        except FileNotFoundError:
            logger.error(
                f"Error: File to be reversed not found at {file_path}. It might have been moved or deleted.")
            # 即使文件不在，也应该处理日志文件（例如重命名为.bak或.error）
            # 但无法进行文件内容的恢复
            # 可以选择在这里重命名日志为 .error 并返回
            try:
                os.replace(json_log_path, json_log_path.with_suffix(
                    '.error_file_missing'))
                logger.warning(
                    f"Renamed log {json_log_path} to .error_file_missing because target file was missing.")
            except OSError as rename_err:
                logger.error(
                    f"Could not rename log file {json_log_path} after file not found error: {rename_err}")
            return
        except Exception as e:
            logger.error(f"Error reading current file {file_path}: {e}")
            return  # 无法读取当前文件，无法恢复

        # --- 4. 生成恢复后的内容 ---
        # 将 "被替换成的内容" 替换回 "原始内容"
        restored_content = current_content.replace(
            replaced_content, target_content)

        # --- 5. 将恢复内容写入临时文件 ---
        try:
            with open(restore_tmp_path, 'w', encoding='utf-8') as f:
                f.write(restored_content)
        except Exception as e:
            logger.error(
                f"Error writing to reverse temporary file {restore_tmp_path}: {e}")
            if restore_tmp_path.exists():
                try:
                    restore_tmp_path.unlink()
                except OSError as unlink_err:
                    logger.warning(
                        f"Could not remove reverse temporary file {restore_tmp_path}: {unlink_err}")
            # 写入临时文件失败，不继续，日志文件保持原样
            return

        # --- 6. 原子性替换原文件 ---
        try:
            os.replace(restore_tmp_path, file_path)
            logger.info(
                f"Successfully reversed changes in {file_path} (UUID: {uuid})")
        except OSError as e:
            logger.error(
                f"Error reversing file {file_path} with {restore_tmp_path}: {e}")
            if restore_tmp_path.exists():
                try:
                    restore_tmp_path.unlink()
                except OSError as unlink_err:
                    logger.warning(
                        f"Could not remove reverse temporary file {restore_tmp_path}: {unlink_err}")
            # 替换失败，不继续，日志文件保持原样
            return

        # --- 7. 原子性重命名日志文件为 .bak ---
        try:
            os.replace(json_log_path, bak_log_path)
            logger.info(
                f"Renamed reverse log {json_log_path} to {bak_log_path}")
        except OSError as e:
            logger.error(
                f"Error renaming reverse log file {json_log_path} to {bak_log_path}: {e}")
            # 文件内容已恢复，但日志重命名失败。这是一个可接受的结束状态，但日志会提示问题。

    except Exception as e:
        # 捕获未预料的错误
        logger.error(
            f"An unexpected error occurred during reverse_func for UUID {uuid}: {e}")
        # 尝试清理临时文件（如果已创建且路径已知）
        if restore_tmp_path and restore_tmp_path.exists():
            try:
                restore_tmp_path.unlink()
                logger.info(
                    f"Cleaned up temporary file {restore_tmp_path} after unexpected error.")
            except OSError as unlink_err:
                logger.warning(
                    f"Could not remove temporary file {restore_tmp_path} after unexpected error: {unlink_err}")
