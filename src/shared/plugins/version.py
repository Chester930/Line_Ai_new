from dataclasses import dataclass
from typing import Dict, Any, Optional, List
import semver
import json
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

@dataclass
class PluginVersion:
    """插件版本信息"""
    version: str
    description: str
    author: str
    dependencies: Dict[str, str]  # 依賴的其他插件及其版本要求
    requirements: List[str]  # Python 包依賴
    changes: str  # 版本變更說明

class PluginVersionManager:
    """插件版本管理器"""
    
    def __init__(self, version_file: str = "config/plugin_versions.json"):
        self.version_file = Path(version_file)
        self.versions: Dict[str, Dict[str, PluginVersion]] = {}
        self.load_versions()
    
    def load_versions(self) -> None:
        """載入版本信息"""
        try:
            if not self.version_file.exists():
                return
            
            with open(self.version_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            for plugin_name, versions in data.items():
                self.versions[plugin_name] = {
                    ver: PluginVersion(**info)
                    for ver, info in versions.items()
                }
                
        except Exception as e:
            logger.error(f"載入版本信息失敗: {str(e)}")
    
    def save_versions(self) -> None:
        """保存版本信息"""
        try:
            data = {
                plugin: {
                    ver: vars(version)
                    for ver, version in versions.items()
                }
                for plugin, versions in self.versions.items()
            }
            
            self.version_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.version_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"保存版本信息失敗: {str(e)}")
    
    def add_version(
        self,
        plugin_name: str,
        version: PluginVersion
    ) -> None:
        """添加新版本"""
        if plugin_name not in self.versions:
            self.versions[plugin_name] = {}
        
        # 驗證版本號格式
        try:
            semver.VersionInfo.parse(version.version)
        except ValueError:
            raise ValueError("無效的版本號格式")
        
        self.versions[plugin_name][version.version] = version
        self.save_versions()
    
    def get_latest_version(self, plugin_name: str) -> Optional[PluginVersion]:
        """獲取最新版本"""
        if plugin_name not in self.versions:
            return None
            
        versions = list(self.versions[plugin_name].keys())
        if not versions:
            return None
            
        latest = max(versions, key=lambda v: semver.VersionInfo.parse(v))
        return self.versions[plugin_name][latest]
    
    def check_compatibility(
        self,
        plugin_name: str,
        version: str
    ) -> List[str]:
        """檢查版本兼容性"""
        if plugin_name not in self.versions:
            return []
            
        plugin_version = self.versions[plugin_name].get(version)
        if not plugin_version:
            return []
        
        issues = []
        
        # 檢查依賴的插件版本
        for dep_name, dep_version in plugin_version.dependencies.items():
            dep_latest = self.get_latest_version(dep_name)
            if not dep_latest:
                issues.append(f"缺少依賴插件: {dep_name}")
                continue
                
            try:
                required = semver.VersionInfo.parse(dep_version)
                current = semver.VersionInfo.parse(dep_latest.version)
                if current < required:
                    issues.append(
                        f"插件 {dep_name} 版本過低: "
                        f"需要 {dep_version}，當前 {dep_latest.version}"
                    )
            except ValueError:
                issues.append(f"無效的版本號格式: {dep_version}")
        
        return issues
    
    def get_upgrade_path(
        self,
        plugin_name: str,
        current_version: str,
        target_version: Optional[str] = None
    ) -> List[PluginVersion]:
        """獲取升級路徑"""
        if plugin_name not in self.versions:
            return []
            
        versions = self.versions[plugin_name]
        if not versions:
            return []
        
        try:
            current = semver.VersionInfo.parse(current_version)
            if target_version:
                target = semver.VersionInfo.parse(target_version)
            else:
                # 使用最新版本
                latest = self.get_latest_version(plugin_name)
                if not latest:
                    return []
                target = semver.VersionInfo.parse(latest.version)
            
            if current >= target:
                return []
            
            # 找出所有可用版本
            available_versions = []
            for ver, info in versions.items():
                try:
                    version = semver.VersionInfo.parse(ver)
                    if current < version <= target:
                        available_versions.append((version, info))
                except ValueError:
                    continue
            
            # 按版本號排序
            available_versions.sort(key=lambda x: x[0])
            return [info for _, info in available_versions]
            
        except ValueError:
            return [] 