#!/bin/bash
# =============================================================================
# Unified Backend Platform - 完整备份脚本
# =============================================================================
# 备份所有关键数据：MongoDB、PostgreSQL、MinIO、Redis
# =============================================================================

set -e

# 配置
BACKUP_DIR="${BACKUP_DIR:-/home/gaooooosh/shared-database-service/backups}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS="${RETENTION_DAYS:-7}"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 创建备份目录
mkdir -p "$BACKUP_DIR"

# =============================================================================
# 1. MongoDB 备份
# =============================================================================
log_info "开始备份 MongoDB..."

MONGO_USER="yonggaoxiao"
MONGO_PASSWORD="233e619e96476734ef033d757fefedd4768a13e8d9e1667e"
MONGO_BACKUP_FILE="$BACKUP_DIR/mongodb_$TIMESTAMP.tar.gz"

docker exec unified-mongo mongodump \
    --username="$MONGO_USER" \
    --password="$MONGO_PASSWORD" \
    --authenticationDatabase=admin \
    --archive="$MONGO_BACKUP_FILE" \
    --gzip

if [ $? -eq 0 ]; then
    log_info "MongoDB 备份完成: $MONGO_BACKUP_FILE"
    log_info "MongoDB 备份大小: $(du -h "$MONGO_BACKUP_FILE" | cut -f1)"
else
    log_error "MongoDB 备份失败"
fi

# =============================================================================
# 2. PostgreSQL 备份
# =============================================================================
log_info "开始备份 PostgreSQL..."

POSTGRES_USER="casdoor"
POSTGRES_PASSWORD="oyrROHvzD1o1o4eCwl0N1NDx8mNHjtTxaJoqw8zoI"
POSTGRES_BACKUP_FILE="$BACKUP_DIR/postgres_$TIMESTAMP.sql.gz"

docker exec unified-postgres pg_dump \
    -U "$POSTGRES_USER" \
    -d casdoor \
    | gzip > "$POSTGRES_BACKUP_FILE"

if [ $? -eq 0 ]; then
    log_info "PostgreSQL 备份完成: $POSTGRES_BACKUP_FILE"
    log_info "PostgreSQL 备份大小: $(du -h "$POSTGRES_BACKUP_FILE" | cut -f1)"
else
    log_error "PostgreSQL 备份失败"
fi

# =============================================================================
# 3. MinIO 备份
# =============================================================================
log_info "开始备份 MinIO..."

MINIO_BACKUP_DIR="$BACKUP_DIR/minio_$TIMESTAMP"
mkdir -p "$MINIO_BACKUP_DIR"

# 使用 MinIO 客户端镜像备份
docker run --rm \
    --network shared-database-service_unified-network \
    minio/mc \
    mirror \
    --overwrite \
    unified-minio/unified-files \
    "$MINIO_BACKUP_DIR/unified-files"

docker run --rm \
    --network shared-database-service_unified-network \
    minio/mc \
    mirror \
    --overwrite \
    unified-minio/unified-thumbnails \
    "$MINIO_BACKUP_DIR/unified-thumbnails"

# 压缩 MinIO 备份
tar -czf "$BACKUP_DIR/minio_$TIMESTAMP.tar.gz" -C "$BACKUP_DIR" "minio_$TIMESTAMP"
rm -rf "$MINIO_BACKUP_DIR"

if [ $? -eq 0 ]; then
    log_info "MinIO 备份完成: $BACKUP_DIR/minio_$TIMESTAMP.tar.gz"
    log_info "MinIO 备份大小: $(du -h "$BACKUP_DIR/minio_$TIMESTAMP.tar.gz" | cut -f1)"
else
    log_error "MinIO 备份失败"
fi

# =============================================================================
# 4. Redis 备份
# =============================================================================
log_info "开始备份 Redis..."

REDIS_BACKUP_FILE="$BACKUP_DIR/redis_$TIMESTAMP.rdb"

# 直接复制 RDB 文件
docker cp unified-redis:/data/dump.rdb "$REDIS_BACKUP_FILE"

if [ $? -eq 0 ]; then
    log_info "Redis 备份完成: $REDIS_BACKUP_FILE"
    log_info "Redis 备份大小: $(du -h "$REDIS_BACKUP_FILE" | cut -f1)"
else
    log_error "Redis 备份失败"
fi

# =============================================================================
# 5. 清理旧备份
# =============================================================================
log_info "清理 $RETENTION_DAYS 天前的旧备份..."

find "$BACKUP_DIR" -name "mongodb_*.tar.gz" -mtime +$RETENTION_DAYS -delete
find "$BACKUP_DIR" -name "postgres_*.sql.gz" -mtime +$RETENTION_DAYS -delete
find "$BACKUP_DIR" -name "minio_*.tar.gz" -mtime +$RETENTION_DAYS -delete
find "$BACKUP_DIR" -name "redis_*.rdb" -mtime +$RETENTION_DAYS -delete

# =============================================================================
# 6. 备份汇总
# =============================================================================
log_info "========================================"
log_info "备份完成！汇总信息:"
log_info "========================================"
ls -lh "$BACKUP_DIR" | tail -10
log_info "========================================"
log_info "备份目录: $BACKUP_DIR"
log_info "保留天数: $RETENTION_DAYS"
log_info "========================================"
