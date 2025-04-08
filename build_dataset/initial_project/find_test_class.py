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


def count_test_files(directory: str) -> int:
    """
    递归统计目录中包含@Test注解的Java文件数量

    Args:
        directory: 要搜索的目录

    Returns:
        包含@Test注解的Java文件数量
    """
    def has_test_annotation(file_path: str) -> bool:
        """检查文件是否包含@Test注解"""
        if not file_path.endswith(".java"):
            return False

        try:
            with open(file_path, "utf-8") as f:
                return "@Test" in f.read()
        except Exception:
            return False

    def search_files(dir_path: str) -> int:
        """递归搜索并计数测试文件"""
        try:
            files = os.listdir(dir_path)

            # 当前目录中的测试文件数量
            file_count = sum(
                1 for file in files
                if os.path.isfile(os.path.join(dir_path, file)) and
                has_test_annotation(os.path.join(dir_path, file))
            )

            # 递归搜索子目录中的测试文件
            subdir_count = sum(
                search_files(os.path.join(dir_path, subdir))
                for subdir in files
                if os.path.isdir(os.path.join(dir_path, subdir))
            )

            return file_count + subdir_count
        except (PermissionError, FileNotFoundError):
            return 0

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
        test_count = count_test_files(test_dir)

        return {
            "project": project_dir.replace(base_dir, "").lstrip('/'),
            "testNum": test_count
        } if test_count > 0 else None

    # 过滤掉没有测试的项目
    return list(filter(
        lambda x: x is not None,
        map(analyze_project, project_dirs)
    ))


def group_projects(projects: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """
    将项目按照路径前缀分组

    Args:
        projects: 项目信息列表

    Returns:
        按路径前缀分组的项目信息字典
    """
    def reducer(acc: Dict[str, List[Dict[str, Any]]], item: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
        """归约函数，将项目添加到对应的分组中"""
        path_parts = item["project"].split("/")
        key = "/".join(path_parts[:-1])

        if key not in acc:
            acc[key] = []

        acc[key].append({
            **item,
            "project": path_parts[-1]
        })

        return acc

    return reduce(reducer, projects, {})


def save_results(grouped_projects: Dict[str, List[Dict[str, Any]]], output_path: str = None) -> str:
    """
    保存分析结果到JSON文件

    Args:
        grouped_projects: 按路径前缀分组的项目信息
        output_path: 结果文件的保存路径

    Returns:
        保存结果的文件路径
    """
    if output_path is None:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        output_path = os.path.join(current_dir, "potentialDir.json")

    # 确保输出目录存在
    if not os.path.exists(os.path.dirname(output_path)):
        os.makedirs(os.path.dirname(output_path))
    with open(output_path, "w") as f:
        json.dump(grouped_projects, f, indent=2)

    return output_path


def main():
    """主函数，协调整个工作流程，支持命令行参数"""
    
    # 创建命令行参数解析器
    parser = argparse.ArgumentParser(description='查找和分析Java测试项目')
    parser.add_argument('--base-dir', type=str, default="/Users/tby/Downloads/hadoop_test_platform/",
                help='要搜索的基础目录路径')
    parser.add_argument('--output-path', type=str, default='./data/potentialDir.json',
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

    print("对项目进行分组...")
    grouped_projects = group_projects(projects)

    print("保存结果...")
    output_path = save_results(grouped_projects, output_path)
    print(f"结果已保存到: {output_path}")
    print("完成！")


if __name__ == "__main__":
    main()
