#!/bin/bash
# =============================================================================
# Unified Backend Platform - 服务监控脚本
# =============================================================================
# 监控所有服务的健康状态，发送告警通知
# =============================================================================

set -e

# 配置
WEBHOOK_URL="${WEBHOOK_URL:-}"  # 企业微信/钉钉/Slack Webhook URL
ALERT_EMAIL="${ALERT_EMAIL:-}" # 告警邮箱
CHECK_INTERVAL=60  # 检查间隔（秒）

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 服务状态
declare -A SERVICES
SERVICES[backend]="http://localhost:9000/health"
SERVICES[casdoor]="http://localhost:8000"
SERVICES[minio]="http://localhost:9100/minio/health/live"
SERVICES[mongo]="unified-mongo"  # Docker 容器名
SERVICES[postgres]="unified-postgres"
SERVICES[redis]="unified-redis"

# 发送告警
send_alert() {
    local service=$1
    local status=$2
    local message="$service 服务异常: $status"

    echo -e "${RED}[ALERT]${NC} $message"

    # 如果配置了 Webhook，发送通知
    if [ -n "$WEBHOOK_URL" ]; then
        curl -X POST "$WEBHOOK_URL" \
            -H "Content-Type: application/json" \
            -d "{\"text\":\"$message\"}" \
            >/dev/null 2>&1
    fi

    # 如果配置了邮箱，发送邮件
    if [ -n "$ALERT_EMAIL" ]; then
        echo "$message" | mail -s "[告警] $service 服务异常" "$ALERT_EMAIL"
    fi
}

# 检查 HTTP 服务
check_http_service() {
    local name=$1
    local url=$2

    local status_code=$(curl -s -o /dev/null -w "%{http_code}" "$url" --max-time 5)

    if [ "$status_code" = "000" ]; then
        send_alert "$name" "连接超时或无法访问"
        return 1
    elif [ "$status_code" != "200" ] && [ "$status_code" != "401" ]; then
        send_alert "$name" "HTTP状态码: $status_code"
        return 1
    else
        echo -e "${GREEN}[OK]${NC} $name (HTTP $status_code)"
        return 0
    fi
}

# 检查 Docker 容器
check_container() {
    local name=$1
    local container=$2

    if ! docker ps --format "{{.Names}}" | grep -q "^${container}$"; then
        send_alert "$name" "容器未运行"
        return 1
    else
        echo -e "${GREEN}[OK]${NC} $name (Container Running)"
        return 0
    fi
}

# 主监控循环
main() {
    echo "========================================"
    echo "  Unified Backend Platform 监控"
    echo "  检查间隔: ${CHECK_INTERVAL}秒"
    echo "========================================"

    while true; do
        echo ""
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] 执行健康检查..."
        echo "----------------------------------------"

        # 检查 Backend API
        check_http_service "Backend" "${SERVICES[backend]}"

        # 检查 Casdoor
        check_http_service "Casdoor" "${SERVICES[casdoor]}"

        # 检查 MinIO
        check_http_service "MinIO" "${SERVICES[minio]}"

        # 检查 MongoDB 容器
        check_container "MongoDB" "${SERVICES[mongo]}"

        # 检查 PostgreSQL 容器
        check_container "PostgreSQL" "${SERVICES[postgres]}"

        # 检查 Redis 容器
        check_container "Redis" "${SERVICES[redis]}"

        echo "----------------------------------------"
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] 检查完成"

        # 等待下一次检查
        sleep "$CHECK_INTERVAL"
    done
}

# 如果直接运行脚本，启动监控
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
    if [ "$1" = "--daemon" ]; then
        # 后台运行模式
        nohup bash "$0" >/var/log/unified-backend-monitor.log 2>&1 &
        echo "监控脚本已在后台启动，PID: $!"
        echo "日志文件: /var/log/unified-backend-monitor.log"
    else
        # 前台运行模式
        main
    fi
fi
