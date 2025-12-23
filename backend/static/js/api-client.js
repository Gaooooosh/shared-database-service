/* =============================================================================
   API Client - 统一后端平台
   API 调用封装模块
   ============================================================================= */

/**
 * API 客户端类
 * 封装所有后端 API 调用
 */
class APIClient {
    constructor(baseURL = '/api/v1') {
        this.baseURL = baseURL;
        this.token = null;
    }

    /**
     * 设置认证 Token
     */
    setToken(token) {
        this.token = token;
        if (token) {
            localStorage.setItem('auth_token', token);
        } else {
            localStorage.removeItem('auth_token');
        }
    }

    /**
     * 获取存储的 Token
     */
    getToken() {
        if (!this.token) {
            this.token = localStorage.getItem('auth_token');
        }
        return this.token;
    }

    /**
     * 获取请求头
     */
    getHeaders() {
        const headers = {
            'Content-Type': 'application/json',
        };

        const token = this.getToken();
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        return headers;
    }

    /**
     * 通用请求方法
     */
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            ...options,
            headers: {
                ...this.getHeaders(),
                ...options.headers,
            },
        };

        try {
            const response = await fetch(url, config);
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || '请求失败');
            }

            return data;
        } catch (error) {
            console.error('API 请求错误:', error);
            throw error;
        }
    }

    /**
     * GET 请求
     */
    async get(endpoint, params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const url = queryString ? `${endpoint}?${queryString}` : endpoint;
        return this.request(url, { method: 'GET' });
    }

    /**
     * POST 请求
     */
    async post(endpoint, data) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }

    /**
     * PUT 请求
     */
    async put(endpoint, data) {
        return this.request(endpoint, {
            method: 'PUT',
            body: JSON.stringify(data),
        });
    }

    /**
     * PATCH 请求
     */
    async patch(endpoint, data) {
        return this.request(endpoint, {
            method: 'PATCH',
            body: JSON.stringify(data),
        });
    }

    /**
     * DELETE 请求
     */
    async delete(endpoint) {
        return this.request(endpoint, { method: 'DELETE' });
    }

    // ==================== 健康检查 ====================

    /**
     * 后端健康检查
     */
    async healthCheck() {
        return this.get('/health');
    }

    // ==================== 记录 CRUD ====================

    /**
     * 创建记录
     */
    async createRecord(data) {
        return this.post('/records', data);
    }

    /**
     * 获取记录列表
     */
    async getRecords(params = {}) {
        return this.get('/records', params);
    }

    /**
     * 获取单条记录
     */
    async getRecord(id) {
        return this.get(`/records/${id}`);
    }

    /**
     * 更新记录
     */
    async updateRecord(id, data) {
        return this.put(`/records/${id}`, data);
    }

    /**
     * 删除记录
     */
    async deleteRecord(id) {
        return this.delete(`/records/${id}`);
    }

    // ==================== 批量操作 ====================

    /**
     * 批量创建记录
     */
    async batchCreateRecords(items, stopOnError = false) {
        return this.post('/records/batch', {
            items,
            stop_on_error: stopOnError,
        });
    }

    /**
     * 批量更新记录
     */
    async batchUpdateRecords(ids, updates, stopOnError = false) {
        return this.put('/records/batch', {
            ids,
            updates,
            stop_on_error: stopOnError,
        });
    }

    /**
     * 批量删除记录
     */
    async batchDeleteRecords(ids, stopOnError = false) {
        return this.delete('/records/batch', {
            ids,
            stop_on_error: stopOnError,
        });
    }

    // ==================== 文件管理 ====================

    /**
     * 上传文件
     */
    async uploadFile(file, metadata = {}) {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('app_identifier', metadata.app_identifier || 'default-app');

        if (metadata.title) {
            formData.append('title', metadata.title);
        }
        if (metadata.description) {
            formData.append('description', metadata.description);
        }
        if (typeof metadata.is_public === 'boolean') {
            formData.append('is_public', String(metadata.is_public));
        }

        const url = `${this.baseURL}/files/upload`;
        const token = this.getToken();

        const response = await fetch(url, {
            method: 'POST',
            headers: {
                ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
            },
            body: formData,
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || '上传失败');
        }

        return response.json();
    }

    /**
     * 获取预签名上传 URL
     */
    async getPresignedUploadUrl(filename, contentType, fileSize, appIdentifier = 'default-app') {
        return this.post('/files/upload/presigned', {
            filename,
            content_type: contentType,
            file_size: fileSize,
            app_identifier: appIdentifier,
        });
    }

    /**
     * 确认预签名上传完成
     */
    async confirmPresignedUpload(fileId) {
        return this.post('/files/upload/confirm', { file_id: fileId });
    }

    /**
     * 获取文件列表
     */
    async getFiles(params = {}) {
        return this.get('/files', params);
    }

    /**
     * 获取文件详情
     */
    async getFile(fileId) {
        return this.get(`/files/${fileId}`);
    }

    /**
     * 获取文件下载链接
     */
    async getFileDownloadUrl(fileId) {
        const result = await this.get(`/files/${fileId}/download`);
        return result.download_url;
    }

    /**
     * 更新文件元数据
     */
    async updateFile(fileId, data) {
        return this.patch(`/files/${fileId}`, data);
    }

    /**
     * 删除文件
     */
    async deleteFile(fileId, deleteFromStorage = false) {
        return this.delete(`/files/${fileId}?delete_from_storage=${deleteFromStorage}`);
    }
}

// 创建全局实例
const apiClient = new APIClient();
