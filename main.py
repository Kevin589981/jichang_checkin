import requests
import json
import os
import sys
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime


@dataclass
class Account:
    """机场账号数据模型"""
    email: str
    password: str


@dataclass
class CheckinResult:
    """签到结果数据模型"""
    account: str
    success: bool
    message: str
    error: Optional[str] = None


class AirportCheckin:
    """通用机场签到类"""
    
    def __init__(self, url: str, accounts: List[Account]):
        self.url = url
        self.accounts = accounts
        self.login_url = f'{url}/auth/login'
        self.check_url = f'{url}/user/checkin'
        self.session = requests.Session()
        self.headers = {
            'origin': url,
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36'
        }
    
    def login(self, account: Account) -> bool:
        """登录机场账号"""
        data = {
            'email': account.email,
            'passwd': account.password
        }
        
        try:
            response = self.session.post(
                url=self.login_url,
                headers=self.headers,
                data=data
            )
            response.raise_for_status()
            result = response.json()
            return result.get('ret') == 1
        except Exception as e:
            print(f"登录失败: {e}")
            return False
    
    def checkin(self, account: Account) -> CheckinResult:
        """执行单个账号签到"""
        print(f'===开始处理账号: {account.email}===')
        
        try:
            # 登录
            if not self.login(account):
                return CheckinResult(
                    account=account.email,
                    success=False,
                    message="登录失败",
                    error="Authentication failed"
                )
            
            print(f'账号 {account.email} 登录成功')
            
            # 签到
            response = self.session.post(
                url=self.check_url,
                headers=self.headers
            )
            response.raise_for_status()
            result = response.json()
            
            message = result.get('msg', '签到完成')
            success = result.get('ret') == 1
            
            print(f'签到结果: {message}')
            
            return CheckinResult(
                account=account.email,
                success=success,
                message=message
            )
            
        except Exception as e:
            error_msg = f"签到异常: {str(e)}"
            print(error_msg)
            return CheckinResult(
                account=account.email,
                success=False,
                message="签到失败",
                error=error_msg
            )
        finally:
            print(f'===账号 {account.email} 处理结束===\n')
    
    def batch_checkin(self) -> List[CheckinResult]:
        """批量执行多账号签到"""
        results = []
        
        for account in self.accounts:
            result = self.checkin(account)
            results.append(result)
        
        return results


def parse_config(config_str: str) -> List[Account]:
    """解析配置字符串为账号列表"""
    if not config_str:
        return []
    
    configs = config_str.strip().splitlines()
    
    if len(configs) % 2 != 0 or len(configs) == 0:
        raise ValueError('配置文件格式错误：账号和密码必须成对出现')
    
    accounts = []
    for i in range(0, len(configs), 2):
        email = configs[i].strip()
        password = configs[i + 1].strip()
        accounts.append(Account(email=email, password=password))
    
    return accounts


def format_results(results: List[CheckinResult]) -> str:
    """格式化签到结果为通知内容"""
    if not results:
        return "没有签到结果"
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    content_lines = [f"机场签到结果 - {timestamp}\n"]
    
    success_count = sum(1 for r in results if r.success)
    total_count = len(results)
    
    content_lines.append(f"总计: {total_count} 个账号，成功: {success_count} 个\n")
    
    for i, result in enumerate(results, 1):
        status = "✅ 成功" if result.success else "❌ 失败"
        content_lines.append(f"{i}. {result.account}")
        content_lines.append(f"   状态: {status}")
        content_lines.append(f"   消息: {result.message}")
        
        if result.error:
            content_lines.append(f"   错误: {result.error}")
        
        content_lines.append("")
    
    return "\n".join(content_lines)


def main():
    """主函数"""
    # 获取环境变量
    url = os.environ.get('URL')
    config = os.environ.get('CONFIG')
    
    if not url:
        print("错误: 未设置 URL 环境变量")
        sys.exit(1)
    
    if not config:
        print("错误: 未设置 CONFIG 环境变量")
        sys.exit(1)
    
    try:
        # 解析账号配置
        accounts = parse_config(config)
        print(f"解析到 {len(accounts)} 个账号")
        
        # 执行批量签到
        checkin_client = AirportCheckin(url, accounts)
        results = checkin_client.batch_checkin()
        
        # 格式化结果
        formatted_result = format_results(results)
        print("\n" + "="*50)
        print("签到汇总:")
        print("="*50)
        print(formatted_result)
        
        # 输出结果供 GitHub Actions 使用
        # 使用 GitHub Actions 的输出语法
        print(f"::set-output name=result::{formatted_result}")
        
        # 检查是否有失败的签到
        failed_count = sum(1 for r in results if not r.success)
        success_count = len(results) - failed_count
        
        if failed_count > 0:
            print(f"::warning::有 {failed_count} 个账号签到失败，{success_count} 个账号签到成功")
            # 即使有失败也不退出，让通知服务处理结果
        else:
            print("::notice::所有账号签到成功")
            
    except Exception as e:
        error_msg = f"程序执行失败: {str(e)}"
        print(f"::error::{error_msg}")
        sys.exit(1)


if __name__ == '__main__':
    main()
