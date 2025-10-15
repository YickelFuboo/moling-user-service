# User-Service

用户认证与权限管理微服务

## 🚀 快速开始

### 使用Docker启动

```bash
# 在项目根目录下
docker-compose up user-service

# 或者启动所有服务
docker-compose up -d
```

### 本地开发

```bash
# 安装poetry（如果还没有安装）
curl -sSL https://install.python-poetry.org | python3 -

# 安装依赖
poetry install

# 配置环境变量
cp env.example .env
# 编辑 .env 文件

# 运行开发服务器
./run.sh dev

# 或者直接运行
poetry run uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

## 📋 功能特性

- ✅ 用户注册、登录、管理
- ✅ JWT认证
- ✅ 角色权限管理
- ✅ 头像上传（支持S3、MinIO、本地存储）
- ✅ 健康检查
- ✅ 完整的API文档

## 🔧 配置说明

### 环境变量

复制 `env.example` 到 `.env` 并配置：

```bash
# 数据库配置
DATABASE_URL=postgresql://user:password@localhost:5432/dbname

# JWT配置
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# 存储配置
STORAGE_TYPE=s3  # s3, minio, local
S3_ENDPOINT_URL=http://localhost:9000
S3_ACCESS_KEY_ID=your-access-key
S3_SECRET_ACCESS_KEY=your-secret-key
S3_REGION=us-east-1
```

### 存储类型

支持三种存储类型：

1. **S3**: 兼容S3的对象存储
2. **MinIO**: MinIO对象存储
3. **Local**: 本地文件存储

## 📚 API文档

启动服务后访问：
- Swagger UI: http://localhost:8001/docs
- ReDoc: http://localhost:8001/redoc

### 主要接口

- `POST /api/v1/auth/register` - 用户注册
- `POST /api/v1/auth/login` - 用户登录
- `GET /api/v1/users/me` - 获取当前用户信息
- `POST /api/v1/avatar/upload/{user_id}` - 上传头像
- `GET /api/v1/avatar/{file_id}` - 获取头像

## 🧪 测试

```bash
# 运行所有测试
./run.sh test

# 或者直接运行
poetry run pytest tests/ -v
```

## 📦 Docker

### 构建镜像

```bash
docker build -t user-service .
```

### 运行容器

```bash
docker run -p 8001:8001 user-service
```

### 使用docker-compose

```bash
# 启动User-Service
docker-compose up user-service

# 启动所有服务
docker-compose up -d
```

## 🔍 健康检查

```bash
curl http://localhost:8001/health
```

返回示例：
```json
{
  "status": "healthy",
  "service": "User-Service",
  "version": "1.0.0",
  "database": "connected",
  "storage": "connected"
}
```

## 📁 项目结构

```
User-Service/
├── app/
│   ├── api/              # API路由
│   ├── service/          # 业务逻辑
│   ├── db/              # 数据库和存储
│   ├── config/          # 配置管理
│   └── logger/          # 日志管理
├── tests/               # 测试文件
├── Dockerfile           # Docker配置
├── run.sh              # 启动脚本
├── pyproject.toml      # Poetry项目配置
└── env.example         # 环境变量示例
```

## 🤝 贡献

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。 