#!/bin/bash
# MongoDB 自动备份脚本

set -e

BACKUP_DIR="/opt/backups/mongodb"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="mongodb_backup_${TIMESTAMP}"

# 从环境变量读取配置
if [ -f .env ]; then
    source .env
elif [ -f .env.production ]; then
    source .env.production
else
    echo "Error: .env file not found"
    exit 1
fi

# 创建备份目录
mkdir -p "${BACKUP_DIR}"

echo "Starting MongoDB backup: ${BACKUP_NAME}"

# 执行备份到容器内
docker compose exec -T mongo mongodump \
  --uri="mongodb://${MONGO_ROOT_USERNAME}:${MONGO_ROOT_PASSWORD}@localhost:27017/?authSource=admin" \
  --archive=/data/backup/${BACKUP_NAME}.tar

# 从容器复制出来
docker compose cp mongo:/data/backup/${BACKUP_NAME}.tar "${BACKUP_DIR}/"

# 压缩备份
gzip "${BACKUP_DIR}/${BACKUP_NAME}.tar"

# 删除 30 天前的备份
find "${BACKUP_DIR}" -name "*.tar.gz" -mtime +30 -delete

echo "Backup completed: ${BACKUP_NAME}.tar.gz"
echo "Location: ${BACKUP_DIR}/${BACKUP_NAME}.tar.gz"
