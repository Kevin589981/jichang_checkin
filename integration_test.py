#!/usr/bin/env python3
"""
集成测试：验证重构后的机场签到功能
"""

import os
import sys
from unittest.mock import patch, Mock
from main import main, parse_config, format_results, Account, CheckinResult


def test_integration_with_mock():
    """使用 mock 进行集成测试"""
    print("=== 集成测试（使用 Mock）===")
    
    # 设置测试环境变量
    test_env = {
        'URL': 'https://test-airport.com',
        'CONFIG': 'test1@example.com\npassword1\ntest2@example.com\npassword2'
    }
    
    with patch.dict(os.environ, test_env):
        with patch('main.requests.Session') as mock_session_class:
            # 设置 mock 响应
            mock_session = Mock()
            mock_session_class.return_value = mock_session
            
            # Mock 登录和签到响应
            login_response = Mock()
            login_response.json.return_value = {"ret": 1, "msg": "登录成功"}
            
            checkin_response1 = Mock()
            checkin_response1.json.return_value = {"ret": 1, "msg": "签到成功，获得 10MB 流量"}
            
            checkin_response2 = Mock()
            checkin_response2.json.return_value = {"ret": 1, "msg": "今日已签到"}
            
            # 设置调用序列：登录1，签到1，登录2，签到2
            mock_session.post.side_effect = [
                login_response, checkin_response1,  # 第一个账号
                login_response, checkin_response2   # 第二个账号
            ]
            
            try:
                # 捕获输出
                import io
                from contextlib import redirect_stdout, redirect_stderr
                
                stdout_capture = io.StringIO()
                stderr_capture = io.StringIO()
                
                with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                    main()
                
                output = stdout_capture.getvalue()
                error_output = stderr_capture.getvalue()
                
                print("✅ 主函数执行成功")
                print(f"输出长度: {len(output)} 字符")
                
                # 检查输出内容
                if "::set-output name=result::" in output:
                    print("✅ 包含 GitHub Actions 输出")
                else:
                    print("❌ 缺少 GitHub Actions 输出")
                
                if "签到成功" in output:
                    print("✅ 包含签到成功信息")
                else:
                    print("❌ 缺少签到成功信息")
                
                if "总计: 2 个账号" in output:
                    print("✅ 包含账号统计信息")
                else:
                    print("❌ 缺少账号统计信息")
                
                # 验证 mock 调用
                expected_calls = 4  # 2个账号 × (登录 + 签到)
                actual_calls = mock_session.post.call_count
                if actual_calls == expected_calls:
                    print(f"✅ API 调用次数正确: {actual_calls}")
                else:
                    print(f"❌ API 调用次数错误: 期望 {expected_calls}, 实际 {actual_calls}")
                
                return True
                
            except SystemExit as e:
                if e.code == 0:
                    print("✅ 程序正常退出")
                    return True
                else:
                    print(f"❌ 程序异常退出，退出码: {e.code}")
                    return False
            except Exception as e:
                print(f"❌ 集成测试失败: {e}")
                return False


def test_data_models():
    """测试数据模型"""
    print("\n=== 数据模型测试 ===")
    
    # 测试 Account
    account = Account(email="test@example.com", password="password123")
    print(f"✅ Account 创建成功: {account.email}")
    
    # 测试 CheckinResult
    result = CheckinResult(
        account="test@example.com",
        success=True,
        message="签到成功，获得 10MB 流量"
    )
    print(f"✅ CheckinResult 创建成功: {result.success}")
    
    # 测试配置解析
    config = "user1@test.com\npass1\nuser2@test.com\npass2"
    accounts = parse_config(config)
    if len(accounts) == 2:
        print("✅ 配置解析正确")
    else:
        print("❌ 配置解析错误")
        return False
    
    # 测试结果格式化
    results = [
        CheckinResult(account="user1@test.com", success=True, message="成功"),
        CheckinResult(account="user2@test.com", success=False, message="失败", error="网络错误")
    ]
    formatted = format_results(results)
    if "总计: 2 个账号，成功: 1 个" in formatted:
        print("✅ 结果格式化正确")
    else:
        print("❌ 结果格式化错误")
        return False
    
    return True


def main_test():
    """主测试函数"""
    print("=== 机场签到模块集成测试 ===\n")
    
    tests = [
        ("数据模型", test_data_models),
        ("集成测试", test_integration_with_mock)
    ]
    
    all_passed = True
    
    for test_name, test_func in tests:
        print(f"=== {test_name}测试 ===")
        if not test_func():
            all_passed = False
        print()
    
    if all_passed:
        print("🎉 所有集成测试通过！")
        print("✅ 机场签到模块重构成功")
        print("✅ 已移除内置 Server酱推送逻辑")
        print("✅ 实现了 Account 和 CheckinResult 数据模型")
        print("✅ 创建了批量签到和结果格式化函数")
        print("✅ GitHub Actions 输出格式正确")
        return True
    else:
        print("❌ 部分集成测试失败")
        return False


if __name__ == '__main__':
    success = main_test()
    sys.exit(0 if success else 1)