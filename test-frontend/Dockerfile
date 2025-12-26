# =============================================================================
# 测试前端 Dockerfile
# =============================================================================
FROM node:20-alpine

WORKDIR /app

# 安装 openssl（用于密钥生成）
RUN apk add --no-cache openssl python3 py3-pip

# 复制 package 文件
COPY package*.json ./

# 安装依赖
RUN npm install

# 复制源代码
COPY . .

# 暴露端口
EXPOSE 3002

# 默认命令
CMD ["npm", "run", "dev"]
