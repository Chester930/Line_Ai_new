import streamlit as st
from .pages import plugins, monitor, users, settings, logs

PAGES = {
    "系統監控": monitor,
    "用戶管理": users,
    "插件管理": plugins,
    "系統配置": settings,
    "系統日誌": logs
}

def main():
    st.sidebar.title("管理後台")
    
    # 檢查登入狀態
    if not check_login():
        show_login()
        return
    
    selection = st.sidebar.radio("選擇功能", list(PAGES.keys()))
    
    # 顯示登出按鈕
    if st.sidebar.button("登出"):
        logout()
        st.experimental_rerun()
    
    page = PAGES[selection]
    page.show()

def check_login() -> bool:
    """檢查登入狀態"""
    return "user" in st.session_state

def show_login():
    """顯示登入表單"""
    st.title("管理後台登入")
    
    username = st.text_input("用戶名")
    password = st.text_input("密碼", type="password")
    
    if st.button("登入"):
        if authenticate(username, password):
            st.session_state["user"] = username
            st.experimental_rerun()
        else:
            st.error("用戶名或密碼錯誤")

def authenticate(username: str, password: str) -> bool:
    """驗證用戶"""
    from src.shared.models.user import User
    from src.shared.database import get_session
    from sqlalchemy import select
    
    with get_session() as session:
        user = session.execute(
            select(User).where(User.username == username)
        ).scalar_one_or_none()
        
        if user and user.check_password(password) and user.role == "admin":
            return True
    return False

def logout():
    """登出"""
    if "user" in st.session_state:
        del st.session_state["user"]

if __name__ == "__main__":
    main() 