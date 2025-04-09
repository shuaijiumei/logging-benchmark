import os
import json
from pathlib import Path
from typing import List, Dict, Any, Tuple
from functools import reduce
import argparse


def find_available_test_classes(directory: str) -> List[str]:
    """
    递归搜索所有既有pom.xml又有src/test的目录

    Args:
        directory: 要搜索的基础目录

    Returns:
        包含测试项目的目录列表
    """
    def is_test_project(dir_path: str) -> bool:
        """判断目录是否是测试项目"""
        try:
            files = os.listdir(dir_path)
            return ("pom.xml" in files and
                    "src" in files and
                    os.path.isdir(os.path.join(dir_path, "src")) and
                    "test" in os.listdir(os.path.join(dir_path, "src")))
        except (PermissionError, FileNotFoundError):
            return False

    def get_subdirectories(dir_path: str) -> List[str]:
        """获取目录下的所有子目录"""
        try:
            return [
                os.path.join(dir_path, file)
                for file in os.listdir(dir_path)
                if os.path.isdir(os.path.join(dir_path, file))
            ]
        except (PermissionError, FileNotFoundError):
            return []

    def search(current_dir: str, accumulated: List[str]) -> List[str]:
        """递归搜索测试项目目录"""
        if is_test_project(current_dir):
            accumulated.append(current_dir)

        subdirs = get_subdirectories(current_dir)
        return reduce(
            lambda acc, subdir: search(subdir, acc),
            subdirs,
            accumulated
        )

    return search(directory, [])

def count_test_files(directory: str) -> Tuple[int, List[str]]:
    """
    递归统计目录中包含@Test注解的Java文件数量并返回文件列表

    Args:
        directory: 要搜索的目录

    Returns:
        包含@Test注解的Java文件数量和文件路径列表
    """
    def has_test_annotation(file_path: str) -> bool:
        """检查文件是否包含@Test注解"""
        if not file_path.endswith(".java"):
            return False

        try:
            with open(file_path, encoding='utf-8') as f:
                return "@Test" in f.read()
        except Exception as e:
            # 处理文件编码错误或其他异常
            print(f"Error reading {file_path}: {e}")
            return False

    def search_files(dir_path: str) -> Tuple[int, List[str]]:
        """递归搜索并返回测试文件数量和文件列表"""
        try:
            files = os.listdir(dir_path)
            test_files = []


            # 当前目录中的测试文件
            for file in files:
                file_path = os.path.join(dir_path, file)
                if os.path.isfile(file_path) and has_test_annotation(file_path):
                    test_files.append(file_path.split("/")[-1].replace(".java", ""))

            # 递归搜索子目录中的测试文件
            for subdir in files:
                subdir_path = os.path.join(dir_path, subdir)
                if os.path.isdir(subdir_path):
                    subdir_count, subdir_files = search_files(subdir_path)
                    test_files.extend(map(lambda x: x.split('/')[-1].replace('.java', ''), subdir_files))

            return len(test_files), test_files
        except (PermissionError, FileNotFoundError):
            return 0, []

    return search_files(directory)

def analyze_projects(project_dirs: List[str], base_dir: str) -> List[Dict[str, Any]]:
    """
    分析项目目录中的测试文件

    Args:
        project_dirs: 测试项目目录列表
        base_dir: 基础目录路径

    Returns:
        项目信息列表
    """
    def analyze_project(project_dir: str) -> Dict[str, Any]:
        """分析单个项目"""
        test_dir = os.path.join(project_dir, "src", "test")
        test_count, test_list = count_test_files(test_dir)

        if test_count > 0:
            # 直接使用最终格式
            return {
                "project_dir": project_dir.replace(base_dir, "").lstrip('/'),
                "test_num": test_count,
                "test_list": test_list,
            }
        return None

    # 过滤掉没有测试的项目
    return list(filter(
        lambda x: x is not None,
        map(analyze_project, project_dirs)
    ))

def save_results(projects: List[Dict[str, Any]], output_path: str = None) -> str:
    """
    保存分析结果到JSON文件

    Args:
        projects: 项目信息列表
        output_path: 结果文件的保存路径

    Returns:
        保存结果的文件路径
    """
    if output_path is None:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        output_path = os.path.join(current_dir, "potential_dir.json")

    # 确保输出目录存在
    if not os.path.exists(os.path.dirname(output_path)):
        os.makedirs(os.path.dirname(output_path))
    with open(output_path, "w") as f:
        json.dump(projects, f, indent=2)

    return output_path


def main():
    """主函数，协调整个工作流程，支持命令行参数"""
    
    # 创建命令行参数解析器
    parser = argparse.ArgumentParser(description='查找和分析Java测试项目')
    parser.add_argument('--base-dir', type=str, default="/Users/tby/Downloads/hadoop_test_platform/",
                help='要搜索的基础目录路径')
    parser.add_argument('--output-path', type=str, default='./data/potential_dir.json',
                help='结果文件的保存路径')
    
    # 解析命令行参数
    args = parser.parse_args()
    base_dir = args.base_dir
    output_path = args.output_path

    print(f"开始在 {base_dir} 搜索测试项目...")
    project_dirs = find_available_test_classes(base_dir)
    print(f"找到 {len(project_dirs)} 个可能的测试项目")
    print(project_dirs[0])

    print("分析测试文件...")
    projects = analyze_projects(project_dirs, base_dir)
    print(f"找到 {len(projects)} 个包含测试的项目")

    # 一共多少个项目
    total_projects = len(projects)
    print(f"总共有 {total_projects} 个项目")

    # 展示一共有多少个测试文件
    total_test_files = sum(project["test_num"] for project in projects)
    print(f"总共有 {total_test_files} 个测试文件")

    # 不再需要分组步骤
    print("保存结果...")
    output_path = save_results(projects, output_path)
    print(f"结果已保存到: {output_path}")
    print("完成！")


if __name__ == "__main__":
    main()
