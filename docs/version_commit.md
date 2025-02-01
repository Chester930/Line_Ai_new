# CAG 系統版本提交規範

## 提交訊息格式

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Type 類型
- feat: 新功能 (feature)
- fix: 修復 Bug
- docs: 文檔變更
- style: 代碼格式調整
- refactor: 代碼重構
- test: 添加測試
- chore: 構建過程或輔助工具的變動

### Scope 範圍
- core: 核心系統
- model: AI 模型
- plugin: 插件系統
- config: 配置系統
- db: 數據庫
- api: API 接口
- ui: 用戶界面
- test: 測試系統
- doc: 文檔

### Subject 主題
- 使用現在時態
- 不超過 50 個字符
- 結尾不加句號

### Body 正文
- 使用現在時態
- 說明代碼變動的動機
- 與上一版本的對比說明

### Footer 頁腳
- Breaking Changes
- Closed Issues
- 相關依賴更新

## 提交範例

```
feat(model): 添加 Claude 模型支持

- 實現 Claude API 調用
- 添加模型配置選項
- 實現流式輸出支持

Breaking Changes:
- 模型配置格式變更，需更新配置文件

Closes #123
```

## 版本標籤規範

### 標籤格式
```
v<major>.<minor>.<patch>[-<stage>]
```

### 階段標記
- alpha: 內部測試版
- beta: 公開測試版
- rc: 候選發布版

### 範例
```
v1.0.0-alpha.1
v1.0.0-beta.2
v1.0.0-rc.1
v1.0.0
```

## 分支管理

### 主要分支
- main: 主分支，穩定版本
- develop: 開發分支
- release: 發布準備分支

### 功能分支
- feature/*: 新功能開發
- bugfix/*: Bug 修復
- hotfix/*: 緊急修復
- docs/*: 文檔更新

### 分支命名
```
<type>/<scope>-<description>
```

範例：
```
feature/model-claude-integration
bugfix/api-timeout-fix
docs/version-control-guide
```

## 合併請求規範

### 標題格式
```
[<type>] <scope>: <description>
```

### 描述內容
1. 變更說明
2. 測試情況
3. 相關文檔
4. 注意事項

### 檢查清單
- [ ] 代碼規範檢查
- [ ] 單元測試通過
- [ ] 集成測試通過
- [ ] 文檔已更新
- [ ] 變更日誌已更新

## 發布流程

1. 版本確認
   - 確認版本號
   - 更新 CHANGELOG.md
   - 更新文檔版本

2. 代碼審查
   - 代碼質量
   - 測試覆蓋
   - 性能影響

3. 發布步驟
   - 合併至發布分支
   - 運行發布測試
   - 打包發布
   - 標記版本
   - 更新主分支

4. 發布後檢查
   - 驗證部署
   - 監控系統
   - 收集反饋 