# Contributing to TenBagger

感谢你对 TenBagger 的关注！我们欢迎所有形式的贡献，包括 Bug 报告、功能建议、文档改进和代码提交。

## 🚀 快速开始

### 环境要求

- Python 3.11+
- Node.js 18+
- Git

### 本地开发

```bash
# 1. Fork 并克隆仓库
git clone https://github.com/your-username/TenBagger.git
cd TenBagger

# 2. 配置环境变量
cp .env.example .env

# 3. 启动后端
cd backend
pip install -r requirements.txt
uvicorn main:app --reload

# 4. 启动前端（新终端）
cd frontend
npm install
npm run dev
```

或使用 Docker 一键启动：

```bash
docker-compose up --build
```

## 📋 贡献流程

1. **Fork** 本仓库
2. 创建功能分支：`git checkout -b feat/your-feature`
3. 提交代码（遵循 [Commit 规范](#commit-规范)）
4. 推送分支：`git push origin feat/your-feature`
5. 创建 **Pull Request**，描述你的改动

## ✍️ Commit 规范

本项目使用 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

```
<type>(<scope>): <subject>

类型（type）：
  feat     新功能
  fix      Bug 修复
  docs     文档更新
  style    代码格式（不影响逻辑）
  refactor 重构
  perf     性能优化
  test     测试相关
  ci       CI/CD 配置
  chore    其他杂项
```

示例：
```
feat(strategy): 增加布林带策略
fix(api): 修复 RSI 计算精度问题
docs: 更新部署文档
```

## 🧪 测试

```bash
# 后端测试
cd backend
pytest

# 前端测试
cd frontend
npm run test
```

提交 PR 前请确保所有测试通过。

## 🐛 报告 Bug

请通过 [GitHub Issues](https://github.com/teng00123/TenBagger/issues) 提交，包含：

- 问题描述
- 复现步骤
- 期望行为 vs 实际行为
- 环境信息（OS、Python/Node 版本）

## 💡 功能建议

同样通过 [GitHub Issues](https://github.com/teng00123/TenBagger/issues) 提交，标记 `enhancement` 标签。

## 📄 License

贡献代码即表示你同意将其以 [MIT License](LICENSE) 授权。
