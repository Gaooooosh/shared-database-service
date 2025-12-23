/* =============================================================================
   Service Monitor - 统一后端平台
   服务监控模块
   ============================================================================= */

/**
 * 服务监控类
 * 实时监控各服务运行状态
 * 通过后端代理 API 检查所有服务状态，避免 CORS 问题
 */
class ServiceMonitor {
    constructor() {
        this.autoRefreshInterval = null;
        this.lastCheckTime = null;
    }

    /**
     * 检查所有服务（通过后端代理）
     */
    async checkAll() {
        this.lastCheckTime = new Date();

        try {
            // 调用后端健康检查代理 API
            const response = await fetch('/api/health/services');
            const data = await response.json();

            const results = data.services || [];

            console.log('服务检查结果:', results);

            // 更新 UI
            this.updateUI(results);

            // 更新页脚状态
            this.updateFooterStatus(results);

            return results;
        } catch (error) {
            console.error('服务检查失败:', error);

            // 失败时显示错误状态
            const errorResults = [
                { name: 'Backend API', status: 'error', message: '检查失败', statusId: 'status-Backend API' },
                { name: 'Casdoor SSO', status: 'error', message: '检查失败', statusId: 'status-Casdoor SSO' },
                { name: 'Mongo Express', status: 'error', message: '检查失败', statusId: 'status-Mongo Express' },
                { name: 'MinIO Console', status: 'error', message: '检查失败', statusId: 'status-MinIO Console' }
            ];

            this.updateUI(errorResults);
            return errorResults;
        }
    }

    /**
     * 更新 UI 显示
     */
    updateUI(results) {
        results.forEach(result => {
            const statusElement = document.getElementById(result.statusId);
            const cardElement = document.getElementById(result.cardId);

            console.log(`更新状态: ${result.name}, statusId: ${result.statusId}, 找到元素: ${!!statusElement}`);

            if (statusElement) {
                const indicator = statusElement.querySelector('.status-indicator');
                const text = statusElement.querySelector('.status-text');

                if (indicator && text) {
                    // 更新状态指示器
                    indicator.className = 'status-indicator';
                    if (result.status === 'healthy') {
                        indicator.classList.add('healthy');
                    } else if (result.status === 'error') {
                        indicator.classList.add('error');
                    }

                    // 更新状态文本
                    if (result.responseTime) {
                        text.textContent = `${result.message} (${result.responseTime}ms)`;
                    } else {
                        text.textContent = result.message;
                    }
                }
            }

            // 更新卡片样式
            if (cardElement) {
                cardElement.classList.remove('status-healthy', 'status-error');
                if (result.status === 'healthy') {
                    cardElement.classList.add('status-healthy');
                } else if (result.status === 'error') {
                    cardElement.classList.add('status-error');
                }
            }
        });
    }

    /**
     * 更新页脚状态
     */
    updateFooterStatus(results) {
        const footerStatus = document.getElementById('footer-status');
        const lastUpdate = document.getElementById('last-update');

        if (footerStatus) {
            const healthyCount = results.filter(r => r.status === 'healthy').length;
            const totalCount = results.length;

            if (healthyCount === totalCount) {
                footerStatus.textContent = '✓ 所有服务正常';
                footerStatus.style.color = 'var(--success-color)';
            } else {
                footerStatus.textContent = `⚠ ${healthyCount}/${totalCount} 服务正常`;
                footerStatus.style.color = 'var(--warning-color)';
            }
        }

        if (lastUpdate) {
            lastUpdate.textContent = this.lastCheckTime.toLocaleString('zh-CN');
        }
    }

    /**
     * 启动自动刷新
     */
    startAutoRefresh(interval = 30000) {
        // 先清除已有的定时器
        this.stopAutoRefresh();

        // 立即检查一次
        this.checkAll();

        // 设置定时器
        this.autoRefreshInterval = setInterval(() => {
            this.checkAll();
        }, interval);

        console.log(`服务监控已启动，刷新间隔: ${interval}ms`);
    }

    /**
     * 停止自动刷新
     */
    stopAutoRefresh() {
        if (this.autoRefreshInterval) {
            clearInterval(this.autoRefreshInterval);
            this.autoRefreshInterval = null;
            console.log('服务监控已停止');
        }
    }

    /**
     * 获取服务状态摘要
     */
    getStatusSummary() {
        return {
            lastCheck: this.lastCheckTime,
            isMonitoring: this.autoRefreshInterval !== null,
            serviceCount: this.services.length,
        };
    }
}

/**
 * 页面加载完成后自动启动监控
 */
if (typeof document !== 'undefined') {
    document.addEventListener('DOMContentLoaded', () => {
        // 检查是否存在服务监控元素
        const hasServiceMonitor = document.querySelector('.service-status');

        if (hasServiceMonitor) {
            // 创建监控实例
            window.serviceMonitor = new ServiceMonitor();

            // 启动监控（30 秒刷新间隔）
            window.serviceMonitor.startAutoRefresh(30000);
        }
    });
}

// 导出供其他模块使用
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { ServiceMonitor };
}
