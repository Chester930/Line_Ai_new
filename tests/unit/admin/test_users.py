import pytest
from unittest.mock import Mock, patch, AsyncMock
import pandas as pd
from datetime import datetime
from src.admin.pages.users import UserManagementUI
from src.shared.models.user import User

class TestUserManagementUI:
    @pytest.fixture
    def users_ui(self):
        return UserManagementUI()
    
    @pytest.fixture
    def mock_streamlit(self):
        with patch('streamlit.title') as mock_title, \
             patch('streamlit.form') as mock_form, \
             patch('streamlit.text_input') as mock_text_input, \
             patch('streamlit.selectbox') as mock_selectbox, \
             patch('streamlit.form_submit_button') as mock_submit, \
             patch('streamlit.success') as mock_success, \
             patch('streamlit.error') as mock_error, \
             patch('streamlit.dataframe') as mock_df, \
             patch('streamlit.button') as mock_button, \
             patch('streamlit.info') as mock_info, \
             patch('streamlit.expander') as mock_expander:
            yield {
                'title': mock_title,
                'form': mock_form,
                'text_input': mock_text_input,
                'selectbox': mock_selectbox,
                'submit': mock_submit,
                'success': mock_success,
                'error': mock_error,
                'dataframe': mock_df,
                'button': mock_button,
                'info': mock_info,
                'expander': mock_expander
            }
    
    @pytest.fixture
    def mock_db_session(self):
        with patch('src.shared.database.get_session') as mock_session:
            session = Mock()
            mock_session.return_value.__enter__.return_value = session
            yield session
    
    @pytest.fixture
    def sample_users(self):
        return [
            Mock(
                id=1,
                username="test_user",
                email="test@example.com",
                role="user",
                created_at=datetime.now(),
                last_login=datetime.now(),
                is_active=True
            ),
            Mock(
                id=2,
                username="admin_user",
                email="admin@example.com",
                role="admin",
                created_at=datetime.now(),
                last_login=datetime.now(),
                is_active=True
            )
        ]
    
    def test_initialize(self, users_ui):
        """測試初始化"""
        assert isinstance(users_ui, UserManagementUI)
    
    def test_render_add_user_form(self, users_ui, mock_streamlit):
        """測試渲染添加用戶表單"""
        # 模擬表單輸入
        mock_streamlit['text_input'].side_effect = ["new_user", "user@example.com"]
        mock_streamlit['selectbox'].return_value = "user"
        mock_streamlit['submit'].return_value = True
        
        with patch.object(users_ui, '_add_user') as mock_add:
            users_ui.render()
            mock_add.assert_called_once_with("new_user", "user@example.com", "user")
    
    def test_add_user_success(self, users_ui, mock_db_session, mock_streamlit):
        """測試成功添加用戶"""
        result = users_ui._add_user("new_user", "user@example.com", "user")
        
        # 驗證資料庫操作
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()
        
        # 驗證成功提示
        mock_streamlit['success'].assert_called_once_with("用戶添加成功")
    
    def test_add_user_failure(self, users_ui, mock_db_session, mock_streamlit):
        """測試添加用戶失敗"""
        mock_db_session.add.side_effect = Exception("Database error")
        
        users_ui._add_user("new_user", "user@example.com", "user")
        
        # 驗證錯誤提示
        mock_streamlit['error'].assert_called_once()
        assert "添加用戶失敗" in mock_streamlit['error'].call_args[0][0]
    
    def test_render_user_list(self, users_ui, mock_streamlit, mock_db_session, sample_users):
        """測試渲染用戶列表"""
        # 模擬資料庫查詢結果
        mock_db_session.execute().scalars().all.return_value = sample_users
        
        users_ui.render()
        
        # 驗證數據框顯示
        mock_streamlit['dataframe'].assert_called_once()
        df_arg = mock_streamlit['dataframe'].call_args[0][0]
        assert isinstance(df_arg, pd.DataFrame)
        assert len(df_arg) == 2
    
    def test_disable_user(self, users_ui, mock_db_session, mock_streamlit):
        """測試禁用用戶"""
        # 模擬查詢結果
        user = Mock(is_active=True)
        mock_db_session.execute().scalar_one.return_value = user
        
        users_ui._disable_user("test_user")
        
        # 驗證用戶狀態更新
        assert user.is_active == False
        mock_db_session.commit.assert_called_once()
    
    def test_reset_password(self, users_ui, mock_db_session, mock_streamlit):
        """測試重置密碼"""
        # 模擬查詢結果
        user = Mock()
        mock_db_session.execute().scalar_one.return_value = user
        
        new_password = users_ui._reset_password("test_user")
        
        # 驗證密碼重置
        assert new_password is not None
        user.set_password.assert_called_once_with(new_password)
        mock_db_session.commit.assert_called_once()
    
    def test_user_operations(self, users_ui, mock_streamlit, mock_db_session, sample_users):
        """測試用戶操作按鈕"""
        # 模擬用戶選擇
        mock_streamlit['selectbox'].return_value = "test_user"
        
        # 模擬按鈕點擊
        mock_streamlit['button'].side_effect = [True, False]  # 禁用按鈕點擊，重置按鈕不點擊
        
        with patch.object(users_ui, '_disable_user') as mock_disable:
            users_ui.render()
            mock_disable.assert_called_once_with("test_user")
    
    def test_error_handling(self, users_ui, mock_db_session, mock_streamlit):
        """測試錯誤處理"""
        # 模擬資料庫錯誤
        mock_db_session.execute.side_effect = Exception("Database error")
        
        users_ui.render()
        
        # 驗證錯誤提示
        mock_streamlit['error'].assert_called_once() 