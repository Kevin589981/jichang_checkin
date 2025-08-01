#!/usr/bin/env python3
"""
测试脚本：验证 GitHub Actions workflow 配置
"""

import os
import sys
import yaml
from pathlib import Path


def test_workflow_config():
    """测试 workflow 配置文件"""
    workflow_path = Path(".github/workflows/ikuuu.yml")
    
    if not workflow_path.exists():
        print("❌ Workflow 文件不存在")
        return False
    
    try:
        with open(workflow_path, 'r', encoding='utf-8') as f:
            workflow = yaml.safe_load(f)
        
        print("✅ Workflow YAML 格式正确")
        
        # 检查必要的触发器
        # YAML 解析器将 'on' 解析为 True (boolean)
        triggers = workflow.get(True, {})  # 'on' 被解析为 True
        required_triggers = ['schedule', 'workflow_dispatch', 'repository_dispatch']
        
        print(f"Debug: 找到的触发器: {list(triggers.keys())}")
        
        for trigger in required_triggers:
            if trigger in triggers:
                print(f"✅ 包含 {trigger} 触发器")
            else:
                print(f"❌ 缺少 {trigger} 触发器")
                return False
        
        # 检查 jobs
        jobs = workflow.get('jobs', {})
        if 'checkin' in jobs and 'notify' in jobs:
            print("✅ 包含必要的 jobs: checkin, notify")
        else:
            print("❌ 缺少必要的 jobs")
            return False
        
        # 检查 checkin job 的输出
        checkin_job = jobs.get('checkin', {})
        outputs = checkin_job.get('outputs', {})
        if 'checkin_result' in outputs and 'checkin_success' in outputs:
            print("✅ checkin job 包含必要的输出")
        else:
            print("❌ checkin job 缺少必要的输出")
            return False
        
        # 检查 notify job 的依赖
        notify_job = jobs.get('notify', {})
        if notify_job.get('needs') == 'checkin':
            print("✅ notify job 正确依赖 checkin job")
        else:
            print("❌ notify job 依赖配置错误")
            return False
        
        print("✅ Workflow 配置验证通过")
        return True
        
    except yaml.YAMLError as e:
        print(f"❌ YAML 格式错误: {e}")
        return False
    except Exception as e:
        print(f"❌ 配置验证失败: {e}")
        return False


def test_environment_variables():
    """测试环境变量配置"""
    print("\n=== 环境变量测试 ===")
    
    required_vars = ['URL', 'CONFIG']
    optional_vars = ['REPO_ACCESS_TOKEN', 'NOTIFICATION_REPO']
    
    all_good = True
    
    for var in required_vars:
        if os.environ.get(var):
            print(f"✅ {var} 已设置")
        else:
            print(f"❌ {var} 未设置（必需）")
            all_good = False
    
    for var in optional_vars:
        if os.environ.get(var):
            print(f"✅ {var} 已设置")
        else:
            print(f"⚠️  {var} 未设置（可选，用于通知功能）")
    
    return all_good


def test_main_script():
    """测试主脚本的基本功能"""
    print("\n=== 主脚本测试 ===")
    
    try:
        # 尝试导入主模块
        import main
        print("✅ main.py 可以正常导入")
        
        # 检查必要的类和函数
        required_items = [
            'Account', 'CheckinResult', 'AirportCheckin',
            'parse_config', 'format_results', 'main'
        ]
        
        for item in required_items:
            if hasattr(main, item):
                print(f"✅ {item} 存在")
            else:
                print(f"❌ {item} 不存在")
                return False
        
        # 测试配置解析
        test_config = "test@example.com\npassword123"
        accounts = main.parse_config(test_config)
        if len(accounts) == 1 and accounts[0].email == "test@example.com":
            print("✅ 配置解析功能正常")
        else:
            print("❌ 配置解析功能异常")
            return False
        
        print("✅ 主脚本测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 主脚本测试失败: {e}")
        return False


def main():
    """主测试函数"""
    print("=== GitHub Actions Workflow 配置测试 ===\n")
    
    tests = [
        ("Workflow 配置", test_workflow_config),
        ("环境变量", test_environment_variables),
        ("主脚本", test_main_script)
    ]
    
    all_passed = True
    
    for test_name, test_func in tests:
        print(f"=== {test_name}测试 ===")
        if not test_func():
            all_passed = False
        print()
    
    if all_passed:
        print("🎉 所有测试通过！")
        sys.exit(0)
    else:
        print("❌ 部分测试失败，请检查配置")
        sys.exit(1)


if __name__ == '__main__':
    main()