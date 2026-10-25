# 安全与隐私 / Security and privacy

## 数据去哪里

词光没有账号、服务器端存储、统计或追踪。学习进度只保存在当前浏览器的 localStorage，可以在「我的」里导出为 JSON 备份。导入备份时会逐字段校验，畸形数据会被丢弃。

Word Atlas has no accounts, server-side storage, analytics or tracking. Progress lives in the browser's localStorage and can be exported as JSON. Imported backups are validated field by field.

## 凭据 / Credentials

网页运行不需要任何 API key。只有 `scripts/atlas/` 中的内容生成脚本需要调用模型服务，它们从环境变量（`SUB2_BASE_URL`、`SUB2_API_KEY`、`ELEVENLABS_API_KEY`）或仓库外的目录（`ATLAS_SECRETS`）读取凭据，不会写入仓库。

- 不要使用 `VITE_*` 变量存放凭据，它们会被打包进浏览器代码。
- 公开前运行 `npm run pack:public`，它会按白名单导出并扫描凭据和个人路径。扫描是辅助手段，不能替代人工检查。
- 如果凭据意外泄露，请立刻在服务商处吊销或轮换。

## 报告问题 / Reporting

发现安全问题请通过 GitHub 私密漏洞报告（Security → Report a vulnerability）联系维护者，不要公开贴出细节。
