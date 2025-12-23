/* =============================================================================
   Code Examples - 统一后端平台
   代码示例展示模块
   ============================================================================= */

/**
 * 代码示例管理类
 */
class CodeExampleManager {
    constructor() {
        this.examples = {
            // JavaScript 示例
            javascript: {
                createRecord: {
                    title: '创建记录',
                    code: `fetch('/api/v1/records', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer ' + token,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    app_identifier: 'blog-app',
    collection_type: 'post',
    payload: {
      title: 'Hello World',
      content: '这是我的第一篇文章'
    },
    is_published: true
  })
})
  .then(res => res.json())
  .then(data => console.log(data));`
                },
                queryRecords: {
                    title: '查询记录',
                    code: `fetch('/api/v1/records?app_identifier=blog-app&collection_type=post&page=1&page_size=20', {
  headers: {
    'Authorization': 'Bearer ' + token
  }
})
  .then(res => res.json())
  .then(data => {
    console.log('总数:', data.total);
    console.log('记录:', data.items);
  });`
                },
                uploadFile: {
                    title: '上传文件',
                    code: `const formData = new FormData();
formData.append('file', fileInput.files[0]);
formData.append('app_identifier', 'my-app');
formData.append('title', '我的图片');
formData.append('is_public', 'true');

fetch('/api/v1/files/upload', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer ' + token
  },
  body: formData
})
  .then(res => res.json())
  .then(data => console.log('文件ID:', data.id));`
                }
            },

            // Python 示例
            python: {
                createRecord: {
                    title: '创建记录',
                    code: `import requests

url = 'http://localhost:9000/api/v1/records'
headers = {'Authorization': f'Bearer {token}'}

data = {
    'app_identifier': 'blog-app',
    'collection_type': 'post',
    'payload': {
        'title': 'Hello World',
        'content': '这是我的第一篇文章'
    },
    'is_published': True
}

response = requests.post(url, json=data, headers=headers)
print(response.json())`
                },
                queryRecords: {
                    title: '查询记录',
                    code: `import requests

params = {
    'app_identifier': 'blog-app',
    'collection_type': 'post',
    'page': 1,
    'page_size': 20
}

response = requests.get(
    'http://localhost:9000/api/v1/records',
    params=params,
    headers={'Authorization': f'Bearer {token}'}
)

data = response.json()
print(f"总数: {data['total']}")
print(f"记录: {data['items']}")`
                },
                uploadFile: {
                    title: '上传文件',
                    code: `import requests

files = {'file': open('image.jpg', 'rb')}
data = {
    'app_identifier': 'my-app',
    'title': '我的图片',
    'is_public': 'true'
}

response = requests.post(
    'http://localhost:9000/api/v1/files/upload',
    files=files,
    data=data,
    headers={'Authorization': f'Bearer {token}'}
)

print(f"文件ID: {response.json()['id']}")`
                }
            },

            // cURL 示例
            curl: {
                createRecord: {
                    title: '创建记录',
                    code: `curl -X POST http://localhost:9000/api/v1/records \\
  -H "Authorization: Bearer YOUR_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{
    "app_identifier": "blog-app",
    "collection_type": "post",
    "payload": {
      "title": "Hello World",
      "content": "这是我的第一篇文章"
    },
    "is_published": true
  }'`
                },
                queryRecords: {
                    title: '查询记录',
                    code: `curl "http://localhost:9000/api/v1/records?app_identifier=blog-app&collection_type=post&page=1&page_size=20" \\
  -H "Authorization: Bearer YOUR_TOKEN"`
                },
                uploadFile: {
                    title: '上传文件',
                    code: `curl -X POST http://localhost:9000/api/v1/files/upload \\
  -H "Authorization: Bearer YOUR_TOKEN" \\
  -F "file=@image.jpg" \\
  -F "app_identifier=my-app" \\
  -F "title=我的图片" \\
  -F "is_public=true"`
                }
            }
        };
    }

    /**
     * 获取指定语言的示例列表
     */
    getExamples(language) {
        return this.examples[language] || this.examples.javascript;
    }

    /**
     * 获取单个示例
     */
    getExample(language, exampleId) {
        const langExamples = this.examples[language] || this.examples.javascript;
        return langExamples[exampleId];
    }

    /**
     * 渲染代码示例到页面
     */
    renderExample(container, language, exampleId) {
        const example = this.getExample(language, exampleId);

        if (!example) {
            console.error(`示例不存在: ${language}.${exampleId}`);
            return;
        }

        const codeBlock = document.createElement('pre');
        const code = document.createElement('code');

        code.className = `language-${language}`;
        code.textContent = example.code;
        codeBlock.appendChild(code);

        container.innerHTML = '';
        container.appendChild(codeBlock);

        // 触发语法高亮
        if (typeof hljs !== 'undefined') {
            hljs.highlightElement(code);
        }
    }

    /**
     * 创建标签页切换
     */
    createTabbedExamples(container, exampleId) {
        const languages = ['javascript', 'python', 'curl'];
        const languageNames = {
            javascript: 'JavaScript',
            python: 'Python',
            curl: 'cURL'
        };

        // 创建标签头
        const tabHeader = document.createElement('div');
        tabHeader.className = 'example-tabs';

        languages.forEach(lang => {
            const tab = document.createElement('button');
            tab.className = 'example-tab';
            tab.textContent = languageNames[lang];
            tab.dataset.language = lang;

            tab.addEventListener('click', () => {
                // 移除所有激活状态
                tabHeader.querySelectorAll('.example-tab').forEach(t => {
                    t.classList.remove('active');
                });

                // 激活当前标签
                tab.classList.add('active');

                // 渲染对应示例
                this.renderExample(codeContainer, lang, exampleId);
            });

            tabHeader.appendChild(tab);
        });

        // 创建代码容器
        const codeContainer = document.createElement('div');
        codeContainer.className = 'example-code';

        // 默认显示第一个语言
        this.renderExample(codeContainer, languages[0], exampleId);
        tabHeader.querySelector('.example-tab').classList.add('active');

        // 组装
        container.innerHTML = '';
        container.appendChild(tabHeader);
        container.appendChild(codeContainer);
    }
}

/**
 * 初始化页面上的所有代码示例
 */
function initCodeExamples() {
    const manager = new CodeExampleManager();

    // 查找所有带有 data-example 属性的元素
    document.querySelectorAll('[data-example]').forEach(element => {
        const exampleId = element.dataset.example;
        const language = element.dataset.language || 'javascript';

        const example = manager.getExample(language, exampleId);
        if (example) {
            const pre = document.createElement('pre');
            const code = document.createElement('code');
            code.className = `language-${language}`;
            code.textContent = example.code;
            pre.appendChild(code);

            element.innerHTML = '';
            element.appendChild(pre);

            // 语法高亮
            if (typeof hljs !== 'undefined') {
                hljs.highlightElement(code);
            }
        }
    });

    // 查找所有带有 data-example-tabs 属性的元素
    document.querySelectorAll('[data-example-tabs]').forEach(element => {
        const exampleId = element.dataset.exampleTabs;
        manager.createTabbedExamples(element, exampleId);
    });

    return manager;
}

/**
 * 复制代码到剪贴板
 */
function copyCodeToClipboard(button) {
    const codeBlock = button.nextElementSibling.querySelector('code');
    const text = codeBlock.textContent;

    navigator.clipboard.writeText(text).then(() => {
        const originalText = button.textContent;
        button.textContent = '已复制!';
        button.classList.add('copied');

        setTimeout(() => {
            button.textContent = originalText;
            button.classList.remove('copied');
        }, 2000);
    }).catch(err => {
        console.error('复制失败:', err);
        button.textContent = '复制失败';
    });
}

/**
 * 页面加载完成后添加复制按钮
 */
if (typeof document !== 'undefined') {
    document.addEventListener('DOMContentLoaded', () => {
        // 为所有代码块添加复制按钮
        document.querySelectorAll('pre code').forEach(codeBlock => {
            const wrapper = codeBlock.parentElement;

            const copyButton = document.createElement('button');
            copyButton.className = 'copy-button';
            copyButton.textContent = '复制';
            copyButton.setAttribute('aria-label', '复制代码到剪贴板');

            copyButton.addEventListener('click', () => {
                copyCodeToClipboard(copyButton);
            });

            wrapper.style.position = 'relative';
            wrapper.insertBefore(copyButton, codeBlock);
        });

        // 初始化代码示例
        window.codeExampleManager = initCodeExamples();
    });
}

// 导出供其他模块使用
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { CodeExampleManager, initCodeExamples };
}
