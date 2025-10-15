#!/usr/bin/env python3
# -*- coding: utf-8 -*-

print("开始简单测试...")

try:
    print("1. 测试基础导入...")
    import os
    print("✓ os 导入成功")
    
    print("2. 测试 pydantic 导入...")
    from pydantic_settings import BaseSettings
    print("✓ pydantic_settings 导入成功")
    
    print("3. 测试 app.config.settings 导入...")
    from app.config.settings import APP_NAME, APP_VERSION
    print("✓ app.config.settings 导入成功")
    print(f"APP_NAME: {APP_NAME}")
    print(f"APP_VERSION: {APP_VERSION}")
    
    print("所有测试通过！")
    
except Exception as e:
    print(f"❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()
