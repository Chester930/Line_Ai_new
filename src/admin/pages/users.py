import streamlit as st
from src.shared.models.user import User
from src.shared.database import get_session
from sqlalchemy import select
import pandas as pd

class UserManagementUI:
    def render(self):
        st.title("用戶管理")
        
        # 添加新用戶表單
        with st.expander("添加新用戶"):
            with st.form("new_user_form"):
                username = st.text_input("用戶名")
                email = st.text_input("電子郵件")
                role = st.selectbox("角色", ["user", "admin"])
                
                if st.form_submit_button("添加"):
                    self._add_user(username, email, role)
        
        # 顯示用戶列表
        st.subheader("用戶列表")
        users = self._get_users()
        
        if users:
            df = pd.DataFrame([
                {
                    "ID": user.id,
                    "用戶名": user.username,
                    "電子郵件": user.email,
                    "角色": user.role,
                    "創建時間": user.created_at,
                    "最後登入": user.last_login
                }
                for user in users
            ])
            
            # 顯示用戶表格
            st.dataframe(df)
            
            # 用戶操作
            selected_user = st.selectbox("選擇用戶", df["用戶名"])
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("禁用用戶"):
                    self._disable_user(selected_user)
                    st.success(f"已禁用用戶: {selected_user}")
            
            with col2:
                if st.button("重置密碼"):
                    new_password = self._reset_password(selected_user)
                    st.info(f"新密碼: {new_password}")
    
    def _get_users(self):
        """獲取所有用戶"""
        with get_session() as session:
            result = session.execute(select(User))
            return result.scalars().all()
    
    def _add_user(self, username: str, email: str, role: str):
        """添加新用戶"""
        try:
            user = User(
                username=username,
                email=email,
                role=role
            )
            with get_session() as session:
                session.add(user)
                session.commit()
            st.success("用戶添加成功")
        except Exception as e:
            st.error(f"添加用戶失敗: {str(e)}")
    
    def _disable_user(self, username: str):
        """禁用用戶"""
        with get_session() as session:
            user = session.execute(
                select(User).where(User.username == username)
            ).scalar_one()
            user.is_active = False
            session.commit()
    
    def _reset_password(self, username: str) -> str:
        """重置用戶密碼"""
        import secrets
        new_password = secrets.token_urlsafe(8)
        
        with get_session() as session:
            user = session.execute(
                select(User).where(User.username == username)
            ).scalar_one()
            user.set_password(new_password)
            session.commit()
        
        return new_password

def show():
    ui = UserManagementUI()
    ui.render() 