# 后端测试前端

完整的后端 API 测试前端应用，用于验证 Unified Backend Platform 的所有功能。

## 功能特性

- ✅ **Casdoor SSO 登录** - 集成单点登录认证
- ✅ **用户认证** - JWT Token 管理和自动刷新
- ✅ **记录 CRUD** - 统一记录的增删改查测试
- ✅ **批量操作** - 批量创建、更新、删除测试
- ✅ **文件上传** - 支持 MinIO 对象存储
- ✅ **权限系统** - RBAC 权限控制测试
- ✅ **自动化测试** - 一键运行所有功能测试

## 技术栈

- **框架**: Vite + React 18 + TypeScript
- **UI**: Ant Design 5
- **路由**: React Router v6
- **状态管理**: Zustand
- **HTTP 客户端**: Axios
- **认证**: Casdoor JS SDK

## 快速开始

### 1. 环境准备

确保后端服务已启动:

```bash
# 在项目根目录
cd /home/gaooooosh/shared-database-service
docker compose up -d
```

### 2. 配置 Casdoor 测试环境

```bash
# 进入测试前端目录
cd test-frontend

# 运行一键设置脚本
chmod +x scripts/setup.sh
./scripts/setup.sh
```

这个脚本会自动:
- 生成 JWT RSA 密钥对
- 配置 Casdoor 测试组织和应用
- 创建测试用户
- 安装前端依赖

### 3. 启动前端应用

```bash
npm run dev
```

访问: http://localhost:3002

## 测试账号

设置脚本会创建以下测试账号:

| 用户名 | 邮箱 | 密码 | 角色 |
|--------|------|------|------|
| test-admin | admin@test.com | Admin123! | 管理员 |
| test-user | user@test.com | User123! | 普通用户 |
| test-editor | editor@test.com | Editor123! | 编辑 |

## 功能测试

### 1. 登录测试

使用任意测试账号登录，验证 Casdoor SSO 认证流程。

### 2. 记录管理测试

- 创建测试记录
- 编辑记录内容
- 删除记录（软删除）
- 测试批量操作

### 3. 文件管理测试

- 上传各种类型文件（图片、视频、文档）
- 查看文件列表
- 下载文件
- 删除文件

### 4. 权限系统测试

- 查看当前用户权限
- 测试权限检查
- 创建自定义角色

### 5. 自动化测试

点击"测试报告"页面中的"运行所有测试"按钮，自动执行所有功能测试。

## 目录结构

```
test-frontend/
├── src/
│   ├── components/       # React 组件
│   │   └── Layout/      # 布局组件
│   ├── pages/           # 页面组件
│   │   ├── LoginPage.tsx
│   │   ├── DashboardPage.tsx
│   │   ├── RecordsPage.tsx
│   │   ├── FilesPage.tsx
│   │   ├── PermissionsPage.tsx
│   │   └── TestReportPage.tsx
│   ├── services/        # API 服务
│   │   ├── api.ts
│   │   ├── authService.ts
│   │   ├── recordService.ts
│   │   ├── fileService.ts
│   │   └── permissionService.ts
│   ├── store/           # 状态管理
│   │   └── authStore.ts
│   ├── types/           # TypeScript 类型
│   │   └── index.ts
│   ├── utils/           # 工具函数
│   │   └── testRunner.ts
│   ├── config/          # 配置文件
│   │   └── index.ts
│   ├── styles/          # 样式文件
│   │   └── global.css
│   ├── App.tsx
│   └── main.tsx
├── scripts/             # 脚本文件
│   ├── setup.sh        # 一键设置脚本
│   ├── setup-casdoor.py
│   ├── generate-jwt-keys.py
│   └── generate-jwt-keys.sh
├── keys/               # 密钥目录 (自动生成)
│   ├── private.pem
│   └── public.pem
├── package.json
├── vite.config.ts
├── tsconfig.json
└── .env
```

## 环境变量

主要配置在 `.env` 文件:

```bash
# Casdoor 配置
VITE_CASDOOR_ORIGIN=http://localhost:8000
VITE_CASDOOR_CLIENT_ID=test-client-id
VITE_CASDOOR_CLIENT_SECRET=test-client-secret
VITE_CASDOOR_APP_NAME=test-app
VITE_CASDOOR_ORGANIZATION=test-org

# 后端 API 配置
VITE_API_BASE_URL=http://localhost:9000/api/v1

# 应用配置
VITE_APP_NAME=后端测试前端
VITE_APP_IDENTIFIER=test-app
```

## 手动设置

如果自动设置脚本失败，可以手动执行:

### 1. 生成 JWT 密钥

```bash
cd test-frontend
python3 scripts/generate-jwt-keys.py
```

### 2. 配置 Casdoor

1. 访问 http://localhost:8000
2. 使用 admin/admin 登录
3. 创建组织 `test-org`
4. 创建应用 `test-app`
5. 将公钥粘贴到应用证书配置中
6. 创建测试用户

### 3. 安装依赖

```bash
npm install
```

## 常见问题

### Q: 登录后显示 401 错误?

A: 检查以下配置:
1. Casdoor 应用是否启用 RS256 算法
2. 后端 JWT_ALGORITHM 是否设置为 RS256
3. 公钥是否正确配置到 Casdoor

### Q: 文件上传失败?

A: 确保 MinIO 服务正常运行:
```bash
docker compose ps minio
```

### Q: 权限检查失败?

A: 检查 Casdoor 权限组是否正确配置并同步到后端。

## 开发

### 构建生产版本

```bash
npm run build
```

### 预览生产版本

```bash
npm run preview
```

### 代码检查

```bash
npm run lint
```

## 测试覆盖

测试覆盖以下后端功能:

- ✅ 用户认证和登录
- ✅ JWT Token 验证
- ✅ 记录 CRUD 操作
- ✅ 批量记录操作
- ✅ 文件上传和管理
- ✅ 权限系统
- ✅ 权限检查
- ✅ 角色管理

## 相关文档

- [Casdoor 文档](https://casdoor.org/)
- [后端 API 文档](http://localhost:9000/api/v1/docs)
- [项目开发指南](../docs/DEVELOPER_GUIDE.md)
