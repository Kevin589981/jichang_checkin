import unittest
from unittest.mock import Mock, patch, MagicMock
import json
from main import Account, CheckinResult, AirportCheckin, parse_config, format_results


class TestAccount(unittest.TestCase):
    """测试 Account 数据模型"""
    
    def test_account_creation(self):
        """测试账号创建"""
        account = Account(email="test@example.com", password="password123")
        self.assertEqual(account.email, "test@example.com")
        self.assertEqual(account.password, "password123")


class TestCheckinResult(unittest.TestCase):
    """测试 CheckinResult 数据模型"""
    
    def test_checkin_result_success(self):
        """测试成功的签到结果"""
        result = CheckinResult(
            account="test@example.com",
            success=True,
            message="签到成功"
        )
        self.assertEqual(result.account, "test@example.com")
        self.assertTrue(result.success)
        self.assertEqual(result.message, "签到成功")
        self.assertIsNone(result.error)
    
    def test_checkin_result_failure(self):
        """测试失败的签到结果"""
        result = CheckinResult(
            account="test@example.com",
            success=False,
            message="签到失败",
            error="网络错误"
        )
        self.assertEqual(result.account, "test@example.com")
        self.assertFalse(result.success)
        self.assertEqual(result.message, "签到失败")
        self.assertEqual(result.error, "网络错误")


class TestParseConfig(unittest.TestCase):
    """测试配置解析功能"""
    
    def test_parse_valid_config(self):
        """测试解析有效配置"""
        config = "user1@example.com\npassword1\nuser2@example.com\npassword2"
        accounts = parse_config(config)
        
        self.assertEqual(len(accounts), 2)
        self.assertEqual(accounts[0].email, "user1@example.com")
        self.assertEqual(accounts[0].password, "password1")
        self.assertEqual(accounts[1].email, "user2@example.com")
        self.assertEqual(accounts[1].password, "password2")
    
    def test_parse_empty_config(self):
        """测试解析空配置"""
        accounts = parse_config("")
        self.assertEqual(len(accounts), 0)
    
    def test_parse_invalid_config(self):
        """测试解析无效配置（奇数行）"""
        config = "user1@example.com\npassword1\nuser2@example.com"
        with self.assertRaises(ValueError):
            parse_config(config)
    
    def test_parse_config_with_whitespace(self):
        """测试解析带空白字符的配置"""
        config = "  user1@example.com  \n  password1  \n  user2@example.com  \n  password2  "
        accounts = parse_config(config)
        
        self.assertEqual(len(accounts), 2)
        self.assertEqual(accounts[0].email, "user1@example.com")
        self.assertEqual(accounts[0].password, "password1")


class TestFormatResults(unittest.TestCase):
    """测试结果格式化功能"""
    
    def test_format_empty_results(self):
        """测试格式化空结果"""
        result = format_results([])
        self.assertEqual(result, "没有签到结果")
    
    def test_format_single_success_result(self):
        """测试格式化单个成功结果"""
        results = [
            CheckinResult(
                account="test@example.com",
                success=True,
                message="签到成功，获得 10MB 流量"
            )
        ]
        
        formatted = format_results(results)
        self.assertIn("总计: 1 个账号，成功: 1 个", formatted)
        self.assertIn("test@example.com", formatted)
        self.assertIn("✅ 成功", formatted)
        self.assertIn("签到成功，获得 10MB 流量", formatted)
    
    def test_format_mixed_results(self):
        """测试格式化混合结果"""
        results = [
            CheckinResult(
                account="success@example.com",
                success=True,
                message="签到成功"
            ),
            CheckinResult(
                account="failed@example.com",
                success=False,
                message="签到失败",
                error="网络超时"
            )
        ]
        
        formatted = format_results(results)
        self.assertIn("总计: 2 个账号，成功: 1 个", formatted)
        self.assertIn("success@example.com", formatted)
        self.assertIn("failed@example.com", formatted)
        self.assertIn("✅ 成功", formatted)
        self.assertIn("❌ 失败", formatted)
        self.assertIn("网络超时", formatted)


class TestAirportCheckin(unittest.TestCase):
    """测试 AirportCheckin 类"""
    
    def setUp(self):
        """设置测试环境"""
        self.url = "https://example.com"
        self.accounts = [
            Account(email="test1@example.com", password="password1"),
            Account(email="test2@example.com", password="password2")
        ]
        self.checkin = AirportCheckin(self.url, self.accounts)
    
    def test_init(self):
        """测试初始化"""
        self.assertEqual(self.checkin.url, self.url)
        self.assertEqual(self.checkin.accounts, self.accounts)
        self.assertEqual(self.checkin.login_url, f"{self.url}/auth/login")
        self.assertEqual(self.checkin.check_url, f"{self.url}/user/checkin")
    
    @patch('main.requests.Session')
    def test_login_success(self, mock_session_class):
        """测试登录成功"""
        # 设置 mock
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        
        mock_response = Mock()
        mock_response.json.return_value = {"ret": 1, "msg": "登录成功"}
        mock_session.post.return_value = mock_response
        
        # 重新创建实例以使用 mock
        checkin = AirportCheckin(self.url, self.accounts)
        account = self.accounts[0]
        
        result = checkin.login(account)
        
        self.assertTrue(result)
        mock_session.post.assert_called_once()
    
    @patch('main.requests.Session')
    def test_login_failure(self, mock_session_class):
        """测试登录失败"""
        # 设置 mock
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        
        mock_response = Mock()
        mock_response.json.return_value = {"ret": 0, "msg": "登录失败"}
        mock_session.post.return_value = mock_response
        
        # 重新创建实例以使用 mock
        checkin = AirportCheckin(self.url, self.accounts)
        account = self.accounts[0]
        
        result = checkin.login(account)
        
        self.assertFalse(result)
    
    @patch('main.requests.Session')
    def test_checkin_success(self, mock_session_class):
        """测试签到成功"""
        # 设置 mock
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        
        # Mock 登录响应
        login_response = Mock()
        login_response.json.return_value = {"ret": 1, "msg": "登录成功"}
        
        # Mock 签到响应
        checkin_response = Mock()
        checkin_response.json.return_value = {"ret": 1, "msg": "签到成功，获得 10MB 流量"}
        
        mock_session.post.side_effect = [login_response, checkin_response]
        
        # 重新创建实例以使用 mock
        checkin = AirportCheckin(self.url, self.accounts)
        account = self.accounts[0]
        
        result = checkin.checkin(account)
        
        self.assertEqual(result.account, account.email)
        self.assertTrue(result.success)
        self.assertEqual(result.message, "签到成功，获得 10MB 流量")
        self.assertIsNone(result.error)
    
    @patch('main.requests.Session')
    def test_checkin_login_failure(self, mock_session_class):
        """测试签到时登录失败"""
        # 设置 mock
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        
        # Mock 登录失败响应
        login_response = Mock()
        login_response.json.return_value = {"ret": 0, "msg": "登录失败"}
        mock_session.post.return_value = login_response
        
        # 重新创建实例以使用 mock
        checkin = AirportCheckin(self.url, self.accounts)
        account = self.accounts[0]
        
        result = checkin.checkin(account)
        
        self.assertEqual(result.account, account.email)
        self.assertFalse(result.success)
        self.assertEqual(result.message, "登录失败")
        self.assertEqual(result.error, "Authentication failed")
    
    @patch('main.requests.Session')
    def test_checkin_login_exception(self, mock_session_class):
        """测试登录时异常"""
        # 设置 mock
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        
        # Mock 抛出异常
        mock_session.post.side_effect = Exception("网络错误")
        
        # 重新创建实例以使用 mock
        checkin = AirportCheckin(self.url, self.accounts)
        account = self.accounts[0]
        
        result = checkin.checkin(account)
        
        self.assertEqual(result.account, account.email)
        self.assertFalse(result.success)
        self.assertEqual(result.message, "登录失败")
        self.assertEqual(result.error, "Authentication failed")
    
    @patch('main.requests.Session')
    def test_checkin_exception_after_login(self, mock_session_class):
        """测试登录成功后签到时异常"""
        # 设置 mock
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        
        # Mock 登录成功，签到时异常
        login_response = Mock()
        login_response.json.return_value = {"ret": 1, "msg": "登录成功"}
        
        mock_session.post.side_effect = [login_response, Exception("签到网络错误")]
        
        # 重新创建实例以使用 mock
        checkin = AirportCheckin(self.url, self.accounts)
        account = self.accounts[0]
        
        result = checkin.checkin(account)
        
        self.assertEqual(result.account, account.email)
        self.assertFalse(result.success)
        self.assertEqual(result.message, "签到失败")
        self.assertIn("签到网络错误", result.error)
    
    @patch.object(AirportCheckin, 'checkin')
    def test_batch_checkin(self, mock_checkin):
        """测试批量签到"""
        # 设置 mock 返回值
        mock_results = [
            CheckinResult(account="test1@example.com", success=True, message="成功1"),
            CheckinResult(account="test2@example.com", success=False, message="失败1", error="错误1")
        ]
        mock_checkin.side_effect = mock_results
        
        results = self.checkin.batch_checkin()
        
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].account, "test1@example.com")
        self.assertEqual(results[1].account, "test2@example.com")
        self.assertEqual(mock_checkin.call_count, 2)


if __name__ == '__main__':
    unittest.main()