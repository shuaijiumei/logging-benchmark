import json
import os
import xml.etree.ElementTree as ET
from typing import Dict, List, Any

def load_potential_dir(file_path: str) -> List[Dict[str, Any]]:
    """加载潜在的测试目录列表"""
    with open(file_path, 'r') as f:
        return json.load(f)

def inject_jacoco_plugin(pom_path: str, record_file: str = None) -> None:
    """向pom.xml注入Jacoco插件，并记录操作到文件中"""
    try:
        # 解析XML
        ET.register_namespace('', "http://maven.apache.org/POM/4.0.0")
        ET.register_namespace('xsi', "http://www.w3.org/2001/XMLSchema-instance")
        tree = ET.parse(pom_path)
        root = tree.getroot()
        
        # Maven命名空间
        ns = {'maven': 'http://maven.apache.org/POM/4.0.0'}
        
        # 查找或创建build元素
        build = root.find('./maven:build', ns)
        if build is None:
            build = ET.SubElement(root, "{http://maven.apache.org/POM/4.0.0}build")
        
        # 查找或创建plugins元素
        plugins = build.find('./maven:plugins', ns)
        if plugins is None:
            plugins = ET.SubElement(build, "{http://maven.apache.org/POM/4.0.0}plugins")
        
        # 创建jacoco插件元素
        plugin = ET.SubElement(plugins, "{http://maven.apache.org/POM/4.0.0}plugin")
        
        # 添加groupId
        groupId = ET.SubElement(plugin, "{http://maven.apache.org/POM/4.0.0}groupId")
        groupId.text = "org.jacoco"
        
        # 添加artifactId
        artifactId = ET.SubElement(plugin, "{http://maven.apache.org/POM/4.0.0}artifactId")
        artifactId.text = "jacoco-maven-plugin"
        
        # 添加version
        version = ET.SubElement(plugin, "{http://maven.apache.org/POM/4.0.0}version")
        version.text = "0.8.7"
        
        # 添加configuration
        configuration = ET.SubElement(plugin, "{http://maven.apache.org/POM/4.0.0}configuration")
        
        destFile = ET.SubElement(configuration, "{http://maven.apache.org/POM/4.0.0}destFile")
        destFile.text = "target/jacoco.exec"
        
        dataFile = ET.SubElement(configuration, "{http://maven.apache.org/POM/4.0.0}dataFile")
        dataFile.text = "target/jacoco.exec"
        
        # 添加executions
        executions = ET.SubElement(plugin, "{http://maven.apache.org/POM/4.0.0}executions")
        
        # 添加第一个execution
        execution1 = ET.SubElement(executions, "{http://maven.apache.org/POM/4.0.0}execution")
        id1 = ET.SubElement(execution1, "{http://maven.apache.org/POM/4.0.0}id")
        id1.text = "jacoco-initialize"
        goals1 = ET.SubElement(execution1, "{http://maven.apache.org/POM/4.0.0}goals")
        goal1 = ET.SubElement(goals1, "{http://maven.apache.org/POM/4.0.0}goal")
        goal1.text = "prepare-agent"
        
        # 添加第二个execution
        execution2 = ET.SubElement(executions, "{http://maven.apache.org/POM/4.0.0}execution")
        id2 = ET.SubElement(execution2, "{http://maven.apache.org/POM/4.0.0}id")
        id2.text = "check"
        goals2 = ET.SubElement(execution2, "{http://maven.apache.org/POM/4.0.0}goals")
        goal2 = ET.SubElement(goals2, "{http://maven.apache.org/POM/4.0.0}goal")
        goal2.text = "check"
        
        # 添加第三个execution
        execution3 = ET.SubElement(executions, "{http://maven.apache.org/POM/4.0.0}execution")
        id3 = ET.SubElement(execution3, "{http://maven.apache.org/POM/4.0.0}id")
        id3.text = "jacoco-site"
        phase3 = ET.SubElement(execution3, "{http://maven.apache.org/POM/4.0.0}phase")
        phase3.text = "test"
        goals3 = ET.SubElement(execution3, "{http://maven.apache.org/POM/4.0.0}goals")
        goal3 = ET.SubElement(goals3, "{http://maven.apache.org/POM/4.0.0}goal")
        goal3.text = "report"
        
        # 保存修改后的XML
        tree.write(pom_path, encoding='utf-8', xml_declaration=True)
        print(f"Jacoco插件已成功注入到 {pom_path}")
            
    except Exception as e:
        print(f"注入Jacoco插件失败: {e}")

def delete_jacoco_plugin(pom_path: str, record_file: str = None) -> None:
    """从pom.xml删除Jacoco插件，并从记录文件中移除"""
    try:
        # 解析XML
        ET.register_namespace('', "http://maven.apache.org/POM/4.0.0")
        ET.register_namespace('xsi', "http://www.w3.org/2001/XMLSchema-instance")
        tree = ET.parse(pom_path)
        root = tree.getroot()
        
        # Maven命名空间
        ns = {'maven': 'http://maven.apache.org/POM/4.0.0'}
        
        # 查找jacoco插件
        jacoco_found = False
        for plugins in root.findall('.//maven:plugins', ns):
            for plugin in plugins.findall('./maven:plugin', ns):
                artifact_id = plugin.find('./maven:artifactId', ns)
                if artifact_id is not None and artifact_id.text == 'jacoco-maven-plugin':
                    # 移除插件
                    plugins.remove(plugin)
                    jacoco_found = True
                    break
            if jacoco_found:
                break
        
        if jacoco_found:
            # 保存修改后的XML
            tree.write(pom_path, encoding='utf-8', xml_declaration=True)
            print(f"Jacoco插件已从 {pom_path} 中删除")
        else:
            print(f"在 {pom_path} 中未找到Jacoco插件")
    except Exception as e:
        print(f"删除Jacoco插件失败: {e}")


def main():
    # 设置命令行参数
    parser = argparse.ArgumentParser(description='Inject or remove JaCoCo plugin in Maven projects')
    parser.add_argument('--potential_dir', help='Path to potential directories JSON file', default='./data/test_dir.json')
    parser.add_argument('--record_file', help='Path to operation record JSON file', default='./data/record.json')
    parser.add_argument('--base_dir', help='Hadoop base directory', default='/Users/tby/Downloads/hadoop_test_platform/')
    parser.add_argument('--action', help='Add or remove Jacoco plugin', required=True, choices=['add', 'remove'], default='add')
    

    args = parser.parse_args()
    
    # 从命令行参数读取文件路径
    potential_dir_path = args.potential_dir
    record_file = args.record_file
    base_dir = args.base_dir
    
    # 加载潜在的测试目录列表
    project_list = load_potential_dir(potential_dir_path)
    
    # 处理每个项目
    for project in project_list:
        project_dir = base_dir + project["project_dir"]
        # 构建pom.xml路径
        pom_path = f"{project_dir}/pom.xml"
        
        if args.action == 'add':
            # 注入Jacoco插件
            inject_jacoco_plugin(pom_path, record_file)
        elif args.action == 'remove':
            # 删除Jacoco插件
            delete_jacoco_plugin(pom_path, record_file)

from datetime import datetime

import argparse


if __name__ == "__main__":
    main()
