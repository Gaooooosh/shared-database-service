/* =============================================================================
   Main Application - 统一后端平台
   主应用逻辑
   ============================================================================= */

/**
 * 应用主类
 */
class App {
    constructor() {
        this.monitoring = null;
        this.init();
    }

    /**
     * 初始化应用
     */
    init() {
        // 初始化服务监控
        this.initMonitoring();

        // 初始化平滑滚动
        this.initSmoothScroll();

        // 初始化导航高亮
        this.initNavHighlight();

        // 初始化 FAQ 折叠面板
        this.initFAQ();

        // 初始化当前时间
        this.updateCurrentTime();

        // 每分钟更新一次时间
        setInterval(() => this.updateCurrentTime(), 60000);
    }

    /**
     * 初始化服务监控
     */
    initMonitoring() {
        if (typeof ServiceMonitor !== 'undefined') {
            this.monitoring = new ServiceMonitor();
            this.monitoring.startAutoRefresh(30000);
        }
    }

    /**
     * 初始化平滑滚动
     */
    initSmoothScroll() {
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', (e) => {
                const href = anchor.getAttribute('href');

                // 跳过空锚点和外部链接
                if (!href || href === '#' || href.startsWith('#http')) {
                    return;
                }

                const target = document.querySelector(href);

                if (target) {
                    e.preventDefault();

                    // 计算偏移量（考虑固定头部）
                    const headerOffset = 80;
                    const elementPosition = target.getBoundingClientRect().top;
                    const offsetPosition = elementPosition + window.pageYOffset - headerOffset;

                    window.scrollTo({
                        top: offsetPosition,
                        behavior: 'smooth'
                    });
                }
            });
        });
    }

    /**
     * 初始化导航高亮
     */
    initNavHighlight() {
        const sections = document.querySelectorAll('section[id]');
        const navLinks = document.querySelectorAll('.nav a[href^="#"]');

        const highlightNav = () => {
            const scrollPosition = window.pageYOffset + 100;

            sections.forEach(section => {
                const sectionTop = section.offsetTop;
                const sectionHeight = section.offsetHeight;
                const sectionId = section.getAttribute('id');

                if (scrollPosition >= sectionTop && scrollPosition < sectionTop + sectionHeight) {
                    navLinks.forEach(link => {
                        link.classList.remove('active');
                        if (link.getAttribute('href') === `#${sectionId}`) {
                            link.classList.add('active');
                        }
                    });
                }
            });
        };

        // 滚动时检查
        window.addEventListener('scroll', highlightNav);

        // 初始检查
        highlightNav();
    }

    /**
     * 初始化 FAQ 折叠面板
     */
    initFAQ() {
        const faqItems = document.querySelectorAll('.faq-item');

        faqItems.forEach(item => {
            const summary = item.querySelector('summary');

            if (summary) {
                summary.addEventListener('click', () => {
                    // 关闭其他打开的项
                    faqItems.forEach(otherItem => {
                        if (otherItem !== item && otherItem.open) {
                            otherItem.removeAttribute('open');
                        }
                    });
                });
            }
        });
    }

    /**
     * 更新当前时间
     */
    updateCurrentTime() {
        const timeElements = document.querySelectorAll('[data-current-time]');

        timeElements.forEach(element => {
            const now = new Date();
            element.textContent = now.toLocaleString('zh-CN', {
                year: 'numeric',
                month: '2-digit',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit',
                hour12: false
            });
        });
    }

    /**
     * 显示通知消息
     */
    showNotification(message, type = 'info', duration = 3000) {
        // 创建通知元素
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <span class="notification-message">${message}</span>
            <button class="notification-close" aria-label="关闭">&times;</button>
        `;

        // 添加到页面
        document.body.appendChild(notification);

        // 添加关闭事件
        const closeBtn = notification.querySelector('.notification-close');
        closeBtn.addEventListener('click', () => {
            this.closeNotification(notification);
        });

        // 自动关闭
        setTimeout(() => {
            this.closeNotification(notification);
        }, duration);

        // 动画进入
        requestAnimationFrame(() => {
            notification.classList.add('show');
        });
    }

    /**
     * 关闭通知
     */
    closeNotification(notification) {
        notification.classList.remove('show');
        notification.classList.add('hide');

        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 300);
    }

    /**
     * 显示加载指示器
     */
    showLoading(message = '加载中...') {
        const loader = document.createElement('div');
        loader.className = 'loading-overlay';
        loader.innerHTML = `
            <div class="loading-spinner"></div>
            <div class="loading-text">${message}</div>
        `;

        document.body.appendChild(loader);
        requestAnimationFrame(() => {
            loader.classList.add('show');
        });

        return loader;
    }

    /**
     * 隐藏加载指示器
     */
    hideLoading(loader) {
        if (loader && loader.parentElement) {
            loader.classList.remove('show');
            setTimeout(() => {
                loader.remove();
            }, 300);
        }
    }

    /**
     * 确认对话框
     */
    confirm(message, title = '确认') {
        return new Promise((resolve) => {
            const modal = document.createElement('div');
            modal.className = 'confirm-modal';
            modal.innerHTML = `
                <div class="confirm-dialog">
                    <div class="confirm-header">
                        <h3>${title}</h3>
                    </div>
                    <div class="confirm-body">
                        <p>${message}</p>
                    </div>
                    <div class="confirm-footer">
                        <button class="btn btn-secondary confirm-cancel">取消</button>
                        <button class="btn btn-primary confirm-ok">确认</button>
                    </div>
                </div>
            `;

            document.body.appendChild(modal);

            const okBtn = modal.querySelector('.confirm-ok');
            const cancelBtn = modal.querySelector('.confirm-cancel');

            const close = (result) => {
                modal.classList.remove('show');
                setTimeout(() => {
                    modal.remove();
                    resolve(result);
                }, 300);
            };

            okBtn.addEventListener('click', () => close(true));
            cancelBtn.addEventListener('click', () => close(false));

            // 点击背景关闭
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    close(false);
                }
            });

            // ESC 键关闭
            const escapeHandler = (e) => {
                if (e.key === 'Escape') {
                    close(false);
                    document.removeEventListener('keydown', escapeHandler);
                }
            };
            document.addEventListener('keydown', escapeHandler);

            requestAnimationFrame(() => {
                modal.classList.add('show');
            });
        });
    }

    /**
     * 获取应用状态
     */
    getStatus() {
        return {
            monitoring: this.monitoring ? this.monitoring.getStatusSummary() : null,
            version: '1.0.0',
            buildDate: '2024-12-23'
        };
    }
}

/**
 * 页面加载完成后初始化应用
 */
if (typeof document !== 'undefined') {
    document.addEventListener('DOMContentLoaded', () => {
        // 创建全局应用实例
        window.app = new App();

        // 添加页面加载完成标记
        document.body.classList.add('loaded');

        console.log('统一后端平台 - 开发者中心已加载完成');

        // 输出应用状态到控制台（便于调试）
        console.log('应用状态:', window.app.getStatus());
    });
}

/**
 * 性能监控
 */
if (typeof window !== 'undefined') {
    // 页面加载完成时间
    window.addEventListener('load', () => {
        const timing = window.performance.timing;
        const loadTime = timing.loadEventEnd - timing.navigationStart;

        console.log(`页面加载时间: ${loadTime}ms`);
    });

    // 监控资源加载
    if (window.PerformanceObserver) {
        const observer = new PerformanceObserver((list) => {
            list.getEntries().forEach((entry) => {
                if (entry.duration > 1000) {
                    console.warn(`资源加载缓慢: ${entry.name} (${Math.round(entry.duration)}ms)`);
                }
            });
        });

        try {
            observer.observe({ entryTypes: ['resource'] });
        } catch (e) {
            // PerformanceObserver 观察资源在某些浏览器可能不支持
        }
    }
}

// 导出供其他模块使用
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { App };
}
