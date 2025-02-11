from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from ..exceptions import ValidationError
import semver
from pathlib import Path
import aiofiles
import json

class PluginConfig(BaseModel):
    """插件配置類"""
    name: str
    enabled: bool = True
    version: str = "1.0.0"
    settings: Dict[str, Any] = {}
    dependencies: List[str] = []
    conflicts: List[str] = []
    validation_rules: Dict[str, Dict[str, Any]] = {}

    def enable(self) -> None:
        """啟用插件"""
        self.enabled = True

    def disable(self) -> None:
        """禁用插件"""
        self.enabled = False

    def validate(self) -> bool:
        """驗證配置"""
        if not self.name:
            raise ValidationError("插件名稱不能為空")
            
        if self.validation_rules:
            self._validate_settings()
            
        return True

    def _validate_settings(self) -> None:
        """驗證設置"""
        for key, rules in self.validation_rules.items():
            if rules.get("required", False) and key not in self.settings:
                raise ValidationError(f"缺少必要配置項: {key}")
                
            if key in self.settings:
                value = self.settings[key]
                
                # 類型檢查
                if "type" in rules and not isinstance(value, rules["type"]):
                    raise ValidationError(f"配置項 {key} 類型錯誤")
                    
                # 字符串長度檢查
                if isinstance(value, str):
                    min_len = rules.get("min_length")
                    if min_len and len(value) < min_len:
                        raise ValidationError(f"配置項 {key} 長度不能小於 {min_len}")
                        
                # 數值範圍檢查
                if isinstance(value, (int, float)):
                    min_val = rules.get("min")
                    max_val = rules.get("max")
                    if min_val is not None and value < min_val:
                        raise ValidationError(f"配置項 {key} 不能小於 {min_val}")
                    if max_val is not None and value > max_val:
                        raise ValidationError(f"配置項 {key} 不能大於 {max_val}")

    async def update_settings(self, settings: Dict[str, Any]) -> None:
        """更新設置"""
        self.settings.update(settings)
        if self.validation_rules:
            self._validate_settings()

    def check_version(self, version_req: str) -> bool:
        """檢查版本"""
        try:
            current = semver.VersionInfo.parse(self.version)
            requirement = version_req.strip()
            
            # 處理特殊比較運算符
            if requirement.startswith(">="):
                min_version = semver.VersionInfo.parse(requirement[2:].strip())
                return current >= min_version
            elif requirement.startswith(">"):
                min_version = semver.VersionInfo.parse(requirement[1:].strip())
                return current > min_version
            elif requirement.startswith("<="):
                max_version = semver.VersionInfo.parse(requirement[2:].strip())
                return current <= max_version
            elif requirement.startswith("<"):
                max_version = semver.VersionInfo.parse(requirement[1:].strip())
                return current < max_version
            else:
                # 精確匹配
                required = semver.VersionInfo.parse(requirement)
                return current == required
            
        except ValueError:
            return False

    async def update_version(self, version: str) -> None:
        """更新版本"""
        try:
            semver.VersionInfo.parse(version)
            self.version = version
        except ValueError:
            raise ValidationError(f"無效的版本號: {version}")

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PluginConfig":
        """從字典創建配置"""
        return cls(**data)

    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return {
            "name": self.name,
            "enabled": self.enabled,
            "version": self.version,
            "settings": self.settings,
            "dependencies": self.dependencies,
            "conflicts": self.conflicts
        }

class PluginSettings(BaseModel):
    """插件設置類"""
    enabled: bool = True
    version: str = "1.0.0"
    settings: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return {
            "enabled": self.enabled,
            "version": self.version,
            "settings": self.settings
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PluginSettings":
        """從字典創建設置"""
        return cls(**data)

    def update(self, settings: Dict[str, Any]) -> None:
        """更新設置"""
        self.settings.update(settings)

class PluginConfigManager:
    """插件配置管理器"""
    
    def __init__(self, config_path: str = "config/plugins_config.json"):
        self.config_path = Path(config_path)
        self.configs: Dict[str, PluginConfig] = {}
        self._migrations: Dict[str, Dict[str, Any]] = {}
        
    def load_configs(self) -> None:
        """載入配置"""
        if not self.config_path.exists():
            return
        
        with open(self.config_path, 'r') as f:
            data = json.load(f)
        
        for name, config_data in data.get("plugins", {}).items():
            settings = PluginSettings(
                enabled=config_data.get("enabled", True),
                version=config_data.get("version", "1.0.0"),
                settings=config_data.get("settings", {})
            )
            self.configs[name] = settings
            
    def save_configs(self) -> None:
        """保存配置"""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            "plugins": {
                name: config.to_dict()
                for name, config in self.configs.items()
            }
        }
        
        with open(self.config_path, 'w') as f:
            json.dump(data, f, indent=2)
        
    async def add_config(self, config: PluginConfig) -> None:
        """添加配置"""
        # 檢查衝突
        for existing_name, existing_config in self.configs.items():
            # 檢查是否在衝突列表中
            if existing_name in config.conflicts or config.name in existing_config.conflicts:
                raise ValidationError(f"插件 {config.name} 與 {existing_name} 存在衝突")
                
            # 檢查端口衝突
            if ("port" in config.settings and 
                "port" in existing_config.settings and
                config.settings["port"] == existing_config.settings["port"]):
                raise ValidationError(
                    f"插件 {config.name} 的端口 {config.settings['port']} "
                    f"與插件 {existing_name} 衝突"
                )
                
        self.configs[config.name] = config
        
    async def get_config(self, name: str) -> PluginConfig:
        """獲取配置"""
        if name not in self.configs:
            raise KeyError(f"插件配置 {name} 不存在")
        return self.configs[name]
        
    async def update_config(self, name: str, settings: Dict[str, Any]) -> None:
        """更新配置"""
        config = await self.get_config(name)
        await config.update_settings(settings)
        
    async def remove_config(self, name: str) -> None:
        """刪除配置"""
        if name in self.configs:
            del self.configs[name]
            
    async def get_load_order(self) -> List[str]:
        """獲取載入順序"""
        order = []
        visited = set()
        
        async def visit(name: str):
            if name in visited:
                return
            visited.add(name)
            config = self.configs[name]
            for dep in config.dependencies:
                if dep not in self.configs:
                    raise ValidationError(f"依賴的插件 {dep} 不存在")
                await visit(dep)
            order.append(name)
            
        for name in self.configs:
            await visit(name)
        return order
        
    async def validate_dependencies(self) -> None:
        """驗證依賴關係"""
        visited = set()
        path = []
        
        async def check_cycle(name: str):
            if name in path:
                cycle = path[path.index(name):] + [name]
                raise ValidationError(f"檢測到循環依賴: {' -> '.join(cycle)}")
            if name in visited:
                return
            visited.add(name)
            path.append(name)
            config = self.configs[name]
            for dep in config.dependencies:
                await check_cycle(dep)
            path.pop()
            
        for name in self.configs:
            await check_cycle(name)
            
    async def check_port_conflicts(self, port: int) -> bool:
        """檢查端口衝突"""
        for config in self.configs.values():
            if config.settings.get("port") == port:
                return True
        return False
        
    def register_migration(self, from_version: str, to_version: str, migrate_func: Any) -> None:
        """註冊遷移規則"""
        if from_version not in self._migrations:
            self._migrations[from_version] = {}
        self._migrations[from_version][to_version] = migrate_func
        
    async def load_and_migrate(self, config_data: Dict[str, Any]) -> PluginConfig:
        """載入並遷移配置"""
        config = PluginConfig(**config_data)
        current_version = config.version
        
        while current_version in self._migrations:
            migrations = self._migrations[current_version]
            if not migrations:
                break
                
            next_version = max(migrations.keys())
            migrate_func = migrations[next_version]
            config_data = await migrate_func(config.to_dict())
            config = PluginConfig(**config_data)
            current_version = next_version
            
        return config
        
    async def create_backup(self) -> Path:
        """創建備份"""
        backup_path = self.config_path.with_suffix(".bak")
        configs = {name: config.to_dict() for name, config in self.configs.items()}
        async with aiofiles.open(backup_path, "w") as f:
            await f.write(json.dumps(configs, indent=2))
        return backup_path
        
    async def restore_from_backup(self, backup_path: Path) -> None:
        """從備份恢復"""
        async with aiofiles.open(backup_path, "r") as f:
            content = await f.read()
        configs = json.loads(content)
        self.configs = {
            name: PluginConfig(**config_data)
            for name, config_data in configs.items()
        } 