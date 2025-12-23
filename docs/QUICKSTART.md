# 统一后端平台 - 5分钟快速接入指南

本指南帮助你在 5 分钟内将应用接入统一后端平台。

---

## 🚀 第一步：创建 Casdoor 应用

### 1. 访问 Casdoor 管理后台

```
http://localhost:8000
```

### 2. 创建新应用

1. 点击左侧 `Applications` → `Add Application`
2. 填写应用信息：

```
名称: my-app
显示名称: 我的应用
```

3. 记录 `Client ID` 和 `Client Secret`

---

## 🔐 第二步：集成用户登录

### 复制粘贴代码（React 示例）

```javascript
// auth.js
import axios from 'axios';

const API_BASE = 'http://localhost:9000/api/v1';
const CASDOOR_URL = 'http://localhost:8000';

// 登录
export function login() {
  window.location.href = `${CASDOOR_URL}/login/oauth/authorize?client_id=YOUR_CLIENT_ID&redirect_uri=${encodeURIComponent('http://localhost:3000/callback')}&response_type=code`;
}

// 处理回调
export async function handleCallback(code) {
  const res = await axios.get(`${CASDOOR_URL}/api/login/oauth/access_token`, {
    params: { client_id: 'YOUR_CLIENT_ID', code, grant_type: 'authorization_code' }
  });
  localStorage.setItem('token', res.data.access_token);
}

// 获取当前用户
export async function getCurrentUser() {
  const token = localStorage.getItem('token');
  const res = await axios.get(`${API_BASE}/auth/me`, {
    headers: { Authorization: `Bearer ${token}` }
  });
  return res.data;
}

// API 请求客户端
const api = axios.create({ baseURL: API_BASE });
api.interceptors.request.use(config => {
  config.headers.Authorization = `Bearer ${localStorage.getItem('token')}`;
  return config;
});
export default api;
```

---

## 📊 第三步：保存数据

### 创建数据

```javascript
import api from './auth';

// 保存一篇文章
async function savePost() {
  const res = await api.post('/records', {
    app_identifier: 'my-app',      // 你的应用标识符
    collection_type: 'post',        // 数据类型
    payload: {                       // 🔥 你的数据（任意结构）
      title: '我的文章',
      content: '文章内容...',
      author: '张三'
    },
    is_published: true
  });
  console.log('保存成功:', res.data);
}
```

### 查询数据

```javascript
// 查询所有文章
async function getPosts() {
  const res = await api.get('/records', {
    params: {
      app_identifier: 'my-app',
      collection_type: 'post'
    }
  });
  console.log('文章列表:', res.data.items);
}

// 查询我的文章
async function getMyPosts() {
  const res = await api.get('/records', {
    params: {
      app_identifier: 'my-app',
      collection_type: 'post',
      owner_id: 'current'  // 自动使用当前用户 ID
    }
  });
  return res.data.items;
}
```

### 更新数据

```javascript
async function updatePost(id) {
  const res = await api.patch(`/records/${id}`, {
    payload: {
      title: '新标题',
      content: '新内容...'
    }
  });
}
```

### 删除数据

```javascript
async function deletePost(id) {
  await api.delete(`/records/${id}`);
}
```

---

## 📁 第四步：上传文件

### 上传图片

```javascript
async function uploadImage(file) {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('app_identifier', 'my-app');

  const res = await api.post('/files/upload', formData);
  console.log('图片 URL:', res.data.public_url);
  return res.data.public_url;
}

// 使用示例
<input type="file" onChange={async (e) => {
  const file = e.target.files[0];
  const url = await uploadImage(file);
  console.log('上传成功:', url);
}} />
```

### 显示图片

```javascript
// 在组件中使用
function PostImage({ imageUrl }) {
  return <img src={imageUrl} alt="文章图片" />;
}
```

---

## 🎯 完整示例：TODO 应用

```javascript
import { useState, useEffect } from 'react';
import api from './auth';

export function TodoApp() {
  const [todos, setTodos] = useState([]);
  const [input, setInput] = useState('');

  // 获取待办事项
  useEffect(() => {
    api.get('/records', {
      params: { app_identifier: 'todo-app', collection_type: 'task' }
    }).then(res => setTodos(res.data.items));
  }, []);

  // 添加待办
  async function addTodo() {
    await api.post('/records', {
      app_identifier: 'todo-app',
      collection_type: 'task',
      payload: { text: input, done: false }
    });
    setInput('');
    // 重新加载...
  }

  // 标记完成
  async function toggleTodo(id, currentDone) {
    await api.patch(`/records/${id}`, {
      payload: { done: !currentDone }
    });
  }

  return (
    <div>
      <input value={input} onChange={e => setInput(e.target.value)} />
      <button onClick={addTodo}>添加</button>

      <ul>
        {todos.map(todo => (
          <li key={todo.id}>
            <input
              type="checkbox"
              checked={todo.payload.done}
              onChange={() => toggleTodo(todo.id, todo.payload.done)}
            />
            {todo.payload.text}
          </li>
        ))}
      </ul>
    </div>
  );
}
```

---

## ❓ 常见问题

**Q: 如何获取 Client ID？**
A: 在 Casdoor 后台创建应用后，在应用详情页面可以看到。

**Q: app_identifier 可以随便写吗？**
A: 可以，建议使用英文、数字和连字符，如 `blog-app`、`shop-app`。

**Q: payload 可以存什么数据？**
A: 任何 JSON 数据：对象、数组、字符串、数字等。

**Q: 如何区分不同用户的数据？**
A: 查询时使用 `owner_id: 'current'`，会自动过滤当前用户的数据。

---

## 📚 下一步

- 阅读完整文档：[DEVELOPER_GUIDE.md](./DEVELOPER_GUIDE.md)
- 查看 API 文档：http://localhost:9000/api/v1/docs

---

**需要帮助？** 查看完整文档或联系技术支持。
