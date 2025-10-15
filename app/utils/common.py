import os
from pathlib import Path
import tomllib

def get_project_meta(package_name: str = "knowledge-service"):
    """从 pyproject.toml 读取项目元数据"""
    try:
        toml_path = Path(__file__).parent.parent.parent / "pyproject.toml"
        if not toml_path.exists():
            return {
                "name": "pando-user-service",
                "version": "1.0.0",
                "description": "Pando User Service",
            }
        
        with open(toml_path, "rb") as f:
            data = tomllib.load(f)
        poetry = data.get("tool", {}).get("poetry", {})
        return {
            "name": poetry.get("name", "pando-user-service"),
            "version": poetry.get("version", "1.0.0"),
            "description": poetry.get("description", "Pando User Service"),
        }
    except Exception as e:
        # 如果读取失败，返回默认值
        return {
            "name": "pando-user-service",
            "version": "1.0.0",
            "description": "Pando User Service",
        }

def get_project_base_directory():
    """获取项目根目录"""
    try:
        # 通过查找包含pyproject.toml的目录来确定项目根目录
        current_dir = os.path.dirname(__file__)

        project_root = current_dir
        while project_root != os.path.dirname(project_root):  # 直到到达文件系统根目录
            if os.path.exists(os.path.join(project_root, "pyproject.toml")):
                break
            project_root = os.path.dirname(project_root)

        return project_root
    except Exception:
        # 如果查找失败，返回当前目录的父目录
        return os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

def is_chinese(text: str) -> bool:
    """判断文本是否包含中文字符"""
    for char in text:
        if '\u4e00' <= char <= '\u9fff':
            return True
    return False

def is_english(text: str) -> bool:
    """判断文本是否只包含英文字符"""
    for char in text:
        if not ('a' <= char.lower() <= 'z' or char == ' ' or char == '\n' or char == '\t'):
            return False
    return True
