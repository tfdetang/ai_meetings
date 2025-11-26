# 前端安装说明

## 安装依赖

```bash
cd web-frontend
npm install
```

## 新增依赖说明

### Markdown 渲染相关

- **react-markdown**: React Markdown 渲染组件
- **remark-gfm**: GitHub Flavored Markdown 支持（表格、任务列表等）
- **rehype-raw**: 允许渲染 HTML 标签
- **rehype-sanitize**: 清理危险的 HTML，防止 XSS 攻击

## 启动开发服务器

```bash
npm run dev
```

## 构建生产版本

```bash
npm run build
```

构建产物会生成在 `dist/` 目录。

## 预览生产构建

```bash
npm run preview
```

## 故障排查

### 依赖安装失败

如果 `npm install` 失败，尝试：

```bash
# 清除缓存
npm cache clean --force

# 删除 node_modules 和 package-lock.json
rm -rf node_modules package-lock.json

# 重新安装
npm install
```

### 使用 yarn

如果你更喜欢使用 yarn：

```bash
yarn install
yarn dev
yarn build
```

### 使用 pnpm

如果你更喜欢使用 pnpm：

```bash
pnpm install
pnpm dev
pnpm build
```

## 开发注意事项

### 代理配置

前端开发服务器会自动代理 API 请求到后端：

- `/api/*` → `http://localhost:8888/api/*`
- `/ws/*` → `ws://localhost:8888/ws/*`

配置文件: `vite.config.js`

### 热更新

Vite 支持热模块替换（HMR），修改代码后会自动刷新页面。

### 浏览器兼容性

支持现代浏览器：
- Chrome/Edge 90+
- Firefox 88+
- Safari 14+

## 生产部署

### 使用 Nginx

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    root /path/to/dist;
    index index.html;
    
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    location /api {
        proxy_pass http://localhost:8888;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
    
    location /ws {
        proxy_pass http://localhost:8888;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";
        proxy_set_header Host $host;
    }
}
```

### 使用 Docker

创建 `Dockerfile`:

```dockerfile
FROM node:18-alpine as build

WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

构建和运行:

```bash
docker build -t ai-meeting-frontend .
docker run -p 80:80 ai-meeting-frontend
```

## 环境变量

可以通过环境变量配置：

```bash
# .env.local
VITE_API_BASE_URL=http://localhost:8888
```

在代码中使用:

```javascript
const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || '/api'
```
