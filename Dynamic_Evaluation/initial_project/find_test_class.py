import os
import json
from pathlib import Path
from typing import List, Dict, Any, Tuple
from functools import reduce
import argparse


def find_available_test_classes(directory: str) -> List[str]:
    """
    Recursively search for directories that contain both pom.xml and src/test.

    Args:
        directory: The base directory to search.

    Returns:
        A list of directories containing test projects.
    """
    def is_test_project(dir_path: str) -> bool:
        """Check if a directory is a test project."""
        try:
            files = os.listdir(dir_path)
            return ("pom.xml" in files and
                    "src" in files and
                    os.path.isdir(os.path.join(dir_path, "src")) and
                    "test" in os.listdir(os.path.join(dir_path, "src")))
        except (PermissionError, FileNotFoundError):
            return False

    def get_subdirectories(dir_path: str) -> List[str]:
        """Get all subdirectories in a directory."""
        try:
            return [
                os.path.join(dir_path, file)
                for file in os.listdir(dir_path)
                if os.path.isdir(os.path.join(dir_path, file))
            ]
        except (PermissionError, FileNotFoundError):
            return []

    def search(current_dir: str, accumulated: List[str]) -> List[str]:
        """Recursively search for test project directories."""
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
    Recursively count the number of Java files containing @Test annotations and return the file list.

    Args:
        directory: The directory to search.

    Returns:
        The number of Java files containing @Test annotations and the list of file paths.
    """
    def has_test_annotation(file_path: str) -> bool:
        """Check if a file contains the @Test annotation."""
        if not file_path.endswith(".java"):
            return False

        try:
            with open(file_path, encoding='utf-8') as f:
                return "@Test" in f.read()
        except Exception as e:
            # Handle file encoding errors or other exceptions
            print(f"Error reading {file_path}: {e}")
            return False

    def search_files(dir_path: str) -> Tuple[int, List[str]]:
        """Recursively search and return the number of test files and the file list."""
        try:
            files = os.listdir(dir_path)
            test_files = []


            # Test files in the current directory
            for file in files:
                file_path = os.path.join(dir_path, file)
                if os.path.isfile(file_path) and has_test_annotation(file_path):
                    test_files.append(file_path.split("/")[-1].replace(".java", ""))

            # Recursively search for test files in subdirectories
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
    Analyze test files in project directories.

    Args:
        project_dirs: List of test project directories.
        base_dir: The base directory path.

    Returns:
        A list of project information.
    """
    def analyze_project(project_dir: str) -> Dict[str, Any]:
        """Analyze a single project."""
        test_dir = os.path.join(project_dir, "src", "test")
        test_count, test_list = count_test_files(test_dir)

        if test_count > 0:
            # Use the final format directly
            return {
                "project_dir": project_dir.replace(base_dir, "").lstrip('/'),
                "test_num": test_count,
                "test_list": test_list,
            }
        return None

    # Filter out projects without tests
    return list(filter(
        lambda x: x is not None,
        map(analyze_project, project_dirs)
    ))

def save_results(projects: List[Dict[str, Any]], output_path: str = None) -> str:
    """
    Save analysis results to a JSON file.

    Args:
        projects: List of project information.
        output_path: The path to save the result file.

    Returns:
        The path where the result file is saved.
    """

    # Ensure the output directory exists
    if not os.path.exists(os.path.dirname(output_path)):
        os.makedirs(os.path.dirname(output_path))
    with open(output_path, "w") as f:
        json.dump(projects, f, indent=2)

    return output_path


def main():
    """Main function to coordinate the entire workflow, supporting command-line arguments."""
    
    # Create a command-line argument parser
    parser = argparse.ArgumentParser(description='Find and analyze Java test projects')
    parser.add_argument('--base-dir', type=str, default="/home/al-bench/hadoop-3.4.0-src/",
                help='The base directory path to search')
    parser.add_argument('--output-path', type=str, default='./data/potential_dir.json',
                help='The path to save the result file')
    
    # Parse command-line arguments
    args = parser.parse_args()
    base_dir = args.base_dir
    output_path = args.output_path

    print(f"Starting to search for test projects in {base_dir}...")
    project_dirs = find_available_test_classes(base_dir)
    print(f"Found {len(project_dirs)} potential test projects")
    print(project_dirs[0])

    print("Analyzing test files...")
    projects = analyze_projects(project_dirs, base_dir)
    print(f"Found {len(projects)} projects containing tests")

    # Total number of projects
    total_projects = len(projects)
    print(f"Total number of projects: {total_projects}")

    # Total number of test files
    total_test_files = sum(project["test_num"] for project in projects)
    print(f"Total number of test files: {total_test_files}")

    # No longer need the grouping step
    print("Saving results...")
    output_path = save_results(projects, output_path)
    print(f"Results saved to: {output_path}")
    print("Done!")


if __name__ == "__main__":
    main()
