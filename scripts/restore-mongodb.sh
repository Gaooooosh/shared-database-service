#!/bin/bash
# MongoDB 恢复脚本

set -e

BACKUP_FILE=$1

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_file.tar.gz>"
    echo "Example: $0 /opt/backups/mongodb/mongodb_backup_20240101_020000.tar.gz"
    exit 1
fi

if [ ! -f "$BACKUP_FILE" ]; then
    echo "Error: Backup file not found: $BACKUP_FILE"
    exit 1
fi

# 从环境变量读取配置
if [ -f .env ]; then
    source .env
elif [ -f .env.production ]; then
    source .env.production
else
    echo "Error: .env file not found"
    exit 1
fi

echo "WARNING: This will replace the current MongoDB data!"
read -p "Are you sure? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Restore cancelled"
    exit 0
fi

# 解压备份
echo "Extracting backup..."
gunzip -c "${BACKUP_FILE}" > /tmp/restore.tar

# 复制到容器
echo "Copying to container..."
docker compose cp /tmp/restore.tar mongo:/data/backup/restore.tar

# 停止后端服务 (避免数据冲突)
echo "Stopping backend service..."
docker compose stop backend

# 执行恢复
echo "Restoring database..."
docker compose exec mongo mongorestore \
  --uri="mongodb://${MONGO_ROOT_USERNAME}:${MONGO_ROOT_PASSWORD}@localhost:27017/?authSource=admin" \
  --archive=/data/backup/restore.tar

# 重启后端服务
echo "Starting backend service..."
docker compose start backend

# 清理临时文件
rm /tmp/restore.tar

echo "Restore completed successfully!"
echo "Please verify the data: curl http://localhost:3002/api/v1/records"
