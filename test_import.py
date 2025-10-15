#!/usr/bin/env python3
# -*- coding: utf-8 -*-

print("开始测试导入...")

try:
    print("1. 测试基础导入...")
    import os
    print("✓ os 导入成功")
    
    print("2. 测试 pathlib 导入...")
    from pathlib import Path
    print("✓ pathlib 导入成功")
    
    print("3. 测试 tomllib 导入...")
    import tomllib
    print("✓ tomllib 导入成功")
    
    print("4. 测试 app.utils.common 导入...")
    from app.utils.common import get_project_meta
    print("✓ app.utils.common 导入成功")
    
    print("5. 测试函数调用...")
    result = get_project_meta()
    print(f"✓ 函数调用成功: {result}")
    
    print("6. 测试 app.config.settings 导入...")
    from app.config.settings import settings
    print("✓ app.config.settings 导入成功")
    
    print("所有测试通过！")
    
except Exception as e:
    print(f"❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()
