import os
import sys
from pathlib import Path
from pyngrok import ngrok
import uvicorn
from dotenv import load_dotenv

def setup_python_path():
    """設置 Python 路徑"""
    project_root = Path(__file__).parent.parent.absolute()
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    return project_root

def setup_ngrok():
    """設置並啟動 ngrok"""
    # 加載環境變量
    load_dotenv()
    
    # 設置 ngrok authtoken
    auth_token = os.getenv('NGROK_AUTHTOKEN')
    if not auth_token:
        print("警告: 未設置 NGROK_AUTHTOKEN")
        return None
        
    try:
        # 重置之前的設置
        ngrok.kill()
        
        # 設置新的 token
        ngrok.set_auth_token(auth_token)
        
        # 啟動 ngrok
        public_url = ngrok.connect(5000)
        print(f"\n=== Ngrok URL ===\n{public_url}\n")
        return public_url
    except Exception as e:
        print(f"Ngrok 啟動失敗: {str(e)}")
        return None

def main():
    """主函數"""
    # 設置 Python 路徑
    project_root = setup_python_path()
    
    # 切換到專案根目錄
    os.chdir(project_root)
    
    # 啟動 ngrok
    public_url = setup_ngrok()
    if not public_url:
        print("無法啟動 ngrok，但仍將繼續啟動應用程序")
    
    # 啟動應用程序
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=5000,
        reload=True,
        reload_dirs=[str(project_root / "src")]
    )

if __name__ == "__main__":
    main() 