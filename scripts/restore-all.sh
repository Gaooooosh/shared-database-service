#!/bin/bash
# =============================================================================
# Unified Backend Platform - 完整恢复脚本
# =============================================================================
# 从备份文件恢复所有数据
# =============================================================================

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 显示使用方法
usage() {
    echo "使用方法: $0 <TIMESTAMP>"
    echo ""
    echo "示例:"
    echo "  $0 20241223_120000"
    echo ""
    echo "可用的备份文件:"
    ls -1 backups/*.tar.gz 2>/dev/null | sed 's/backup\///g' | sed 's/_.*//g' | sort -u || echo "  无备份文件"
    exit 1
}

# 检查参数
if [ -z "$1" ]; then
    usage
fi

TIMESTAMP="$1"
BACKUP_DIR="./backups"

# 检查备份文件是否存在
if [ ! -f "$BACKUP_DIR/mongodb_$TIMESTAMP.tar.gz" ]; then
    log_error "备份文件不存在: $BACKUP_DIR/mongodb_$TIMESTAMP.tar.gz"
    exit 1
fi

# 确认操作
log_warn "⚠️  警告: 此操作将覆盖当前所有数据！"
echo ""
read -p "确认恢复备份 $TIMESTAMP? (输入 YES 确认): " confirm

if [ "$confirm" != "YES" ]; then
    log_info "操作已取消"
    exit 0
fi

# 停止所有服务
log_info "停止所有服务..."
docker compose down

# =============================================================================
# 1. 恢复 MongoDB
# =============================================================================
log_info "恢复 MongoDB..."

MONGO_USER="yonggaoxiao"
MONGO_PASSWORD="233e619e96476734ef033d757fefedd4768a13e8d9e1667e"

docker compose up -d mongo

# 等待 MongoDB 就绪
sleep 10

docker exec unified-mongo mongorestore \
    --username="$MONGO_USER" \
    --password="$MONGO_PASSWORD" \
    --authenticationDatabase=admin \
    --archive="$BACKUP_DIR/mongodb_$TIMESTAMP.tar.gz" \
    --gzip

log_info "MongoDB 恢复完成"

# =============================================================================
# 2. 恢复 PostgreSQL
# =============================================================================
log_info "恢复 PostgreSQL..."

POSTGRES_USER="casdoor"
POSTGRES_PASSWORD="oyrROHvzD1o1o4eCwl0N1NDx8mNHjtTxaJoqw8zoI"

docker compose up -d postgres

# 等待 PostgreSQL 就绪
sleep 10

# 删除现有数据库并重新创建
docker exec unified-postgres psql -U "$POSTGRES_USER" -c "DROP DATABASE IF EXISTS casdoor;"
docker exec unified-postgres psql -U "$POSTGRES_USER" -c "CREATE DATABASE casdoor;"

# 恢复数据
gunzip -c "$BACKUP_DIR/postgres_$TIMESTAMP.sql.gz" | \
    docker exec -i unified-postgres psql -U "$POSTGRES_USER" -d casdoor

log_info "PostgreSQL 恢复完成"

# =============================================================================
# 3. 恢复 MinIO
# =============================================================================
log_info "恢复 MinIO..."

if [ -f "$BACKUP_DIR/minio_$TIMESTAMP.tar.gz" ]; then
    docker compose up -d minio

    # 等待 MinIO 就绪
    sleep 10

    # 解压备份
    tar -xzf "$BACKUP_DIR/minio_$TIMESTAMP.tar.gz" -C /tmp

    # 使用 MinIO 客户端恢复
    docker run --rm \
        --network shared-database-service_unified-network \
        -v "/tmp/minio_$TIMESTAMP:/backup" \
        minio/mc \
        mirror --overwrite /backup/unified-files unified-minio/unified-files

    docker run --rm \
        --network shared-database-service_unified-network \
        -v "/tmp/minio_$TIMESTAMP:/backup" \
        minio/mc \
        mirror --overwrite /backup/unified-thumbnails unified-minio/unified-thumbnails

    # 清理临时文件
    rm -rf "/tmp/minio_$TIMESTAMP"

    log_info "MinIO 恢复完成"
else
    log_warn "MinIO 备份文件不存在，跳过"
fi

# =============================================================================
# 4. 恢复 Redis
# =============================================================================
log_info "恢复 Redis..."

if [ -f "$BACKUP_DIR/redis_$TIMESTAMP.rdb" ]; then
    docker compose up -d redis

    # 等待 Redis 就绪
    sleep 5

    # 停止 Redis 以复制 RDB 文件
    docker compose stop redis

    # 复制 RDB 文件
    docker cp "$BACKUP_DIR/redis_$TIMESTAMP.rdb" unified-redis:/data/dump.rdb

    # 启动 Redis
    docker compose start redis

    log_info "Redis 恢复完成"
else
    log_warn "Redis 备份文件不存在，跳过"
fi

# =============================================================================
# 5. 启动所有服务
# =============================================================================
log_info "启动所有服务..."
docker compose up -d

log_info "========================================"
log_info "恢复完成！"
log_info "========================================"
log_info "请验证服务状态:"
log_info "  Backend:  curl http://localhost:9000/health"
log_info "  Casdoor:  curl http://localhost:8000"
log_info "  MinIO:    curl http://localhost:9100/minio/health/live"
log_info "========================================"
