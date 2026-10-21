# JWT Token 认证使用指南

## 概述

用户系统已实现完整的 JWT (JSON Web Token) 认证机制，用于保护需要登录的 API 接口。

## 实现组件

### 1. JwtUtil.java
JWT 工具类，提供以下功能：
- `generateToken(userId, platform)` - 生成 Token
- `validateToken(token)` - 验证 Token 是否有效
- `getUserIdFromToken(token)` - 从 Token 获取用户ID
- `getPlatformFromToken(token)` - 从 Token 获取平台信息
- `isTokenExpired(token)` - 判断 Token 是否过期

### 2. JwtInterceptor.java
JWT 拦截器，自动拦截需要认证的请求：
- 从请求头或参数中提取 Token
- 验证 Token 的有效性
- 将用户信息存入 request attribute

### 3. WebMvcConfig.java
Web 配置类，配置拦截器规则：
- 拦截所有 `/api/**` 路径
- 放行登录和注册接口
- 配置 CORS 跨域

### 4. UserContext.java
用户上下文工具类，方便获取当前登录用户：
- `getCurrentUserId()` - 获取当前用户ID
- `getCurrentPlatform()` - 获取当前平台

## 配置说明

在 `application.yml` 中配置 JWT：

```yaml
jwt:
  secret: baseball_pose_analysis_secret_key_2026_very_long_secret
  expiration: 86400000  # 24小时（毫秒）
```

**注意**：
- `secret` 是签名密钥，生产环境请使用更复杂的密钥
- `expiration` 是 Token 有效期，单位毫秒，默认 24 小时

## 使用方式

### 1. 登录获取 Token

#### 微信登录
```bash
curl -X POST http://localhost:8002/api/user/login/wechat?platform=wechat \
  -H "Content-Type: application/json" \
  -d '{
    "code": "wx_auth_code",
    "userInfo": "用户信息"
  }'
```

#### 手机号登录
```bash
curl -X POST http://localhost:8002/api/user/login/phone?platform=app \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "13800138000",
    "code": "123456"
  }'
```

#### 用户注册
```bash
curl -X POST http://localhost:8002/api/user/register?platform=app \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "13800138000",
    "code": "123456",
    "password": "123456",
    "nickname": "测试用户",
    "gender": 1
  }'
```

**响应示例**：
```json
{
  "code": "200",
  "message": "success",
  "data": {
    "token": "eyJhbGciOiJIUzI1NiJ9.eyJ1c2VySWQiOjEsInBsYXRmb3JtIjoiYXBwIiwic3ViIjoiMSIsImlhdCI6MTY4ODY3MjQwMCwiZXhwIjoxNjg4NzU4ODAwfQ.xxx",
    "userId": 1,
    "nickname": "测试用户",
    "avatarUrl": "",
    "vipLevel": 0,
    "points": 100,
    "isNewUser": true,
    "platform": "app"
  }
}
```

### 2. 使用 Token 访问需要认证的接口

#### 方式一：在请求头中携带 Token（推荐）
```bash
curl -X GET http://localhost:8002/api/user/info \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiJ9..."
```

#### 方式二：在 URL 参数中携带 Token
```bash
curl -X GET "http://localhost:8002/api/user/info?token=eyJhbGciOiJIUzI1NiJ9..."
```

### 3. 前端使用示例

#### 登录并保存 Token
```javascript
// 登录
const response = await fetch('http://localhost:8002/api/user/login/phone?platform=app', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    phone: '13800138000',
    code: '123456'
  })
});

const data = await response.json();
const token = data.data.token;

// 保存 Token 到 localStorage
localStorage.setItem('token', token);
```

#### 携带 Token 访问接口
```javascript
// 获取 Token
const token = localStorage.getItem('token');

// 访问需要认证的接口
const response = await fetch('http://localhost:8002/api/user/info', {
  method: 'GET',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  }
});

const data = await response.json();
console.log(data);
```

#### Axios 拦截器配置
```javascript
import axios from 'axios';

// 请求拦截器
axios.interceptors.request.use(
  config => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  error => {
    return Promise.reject(error);
  }
);

// 响应拦截器
axios.interceptors.response.use(
  response => {
    return response;
  },
  error => {
    if (error.response && error.response.status === 401) {
      // Token 无效或过期，跳转到登录页
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);
```

## 接口认证规则

### 不需要认证的接口（已放行）
- `POST /api/user/login/wechat` - 微信登录
- `POST /api/user/login/phone` - 手机号登录
- `POST /api/user/register` - 用户注册
- `GET /api/health` - 健康检查

### 需要认证的接口
- `GET /api/user/info` - 获取用户信息
- `PUT /api/user/update` - 更新用户信息
- `GET /api/user/points` - 获取用户积分
- `GET /api/user/points/log` - 获取积分记录
- 所有其他 `/api/**` 接口

## Token 结构

JWT Token 包含以下信息：

```json
{
  "userId": 1,
  "platform": "app",
  "sub": "1",
  "iat": 1688672400,
  "exp": 1688758800
}
```

- `userId` - 用户ID
- `platform` - 登录平台（wechat/app/web）
- `sub` - 主题（用户ID）
- `iat` - 签发时间
- `exp` - 过期时间

## 错误处理

### Token 未提供
```json
{
  "code": "401",
  "message": "未提供认证Token",
  "data": null
}
```

### Token 无效或过期
```json
{
  "code": "401",
  "message": "Token无效或已过期",
  "data": null
}
```

## 安全建议

1. **密钥管理**
   - 生产环境使用更复杂的密钥（至少 256 位）
   - 不要将密钥硬编码在代码中，使用环境变量或配置中心

2. **Token 存储**
   - 前端使用 localStorage 或 sessionStorage 存储
   - 敏感应用建议使用 httpOnly Cookie

3. **Token 刷新**
   - 建议实现 Token 刷新机制
   - 可以在 Token 即将过期时自动刷新

4. **HTTPS**
   - 生产环境必须使用 HTTPS
   - 防止 Token 在传输过程中被窃取

5. **Token 黑名单**
   - 实现 Token 黑名单机制
   - 用户登出时将 Token 加入黑名单

## 扩展功能

### 1. Token 刷新
可以实现 refresh token 机制，在 access token 过期前自动刷新。

### 2. 多设备登录
可以记录用户的登录设备，实现多设备管理。

### 3. Token 撤销
可以实现 Token 撤销功能，支持用户主动登出。

### 4. 权限控制
可以在 Token 中添加角色信息，实现基于角色的权限控制。

## 常见问题

### Q: Token 过期了怎么办？
A: 重新登录获取新的 Token，或实现 Token 刷新机制。

### Q: 如何在微信小程序中使用？
A: 登录后将 Token 保存到 `wx.setStorageSync('token', token)`，请求时从 storage 中读取。

### Q: 如何获取当前登录用户信息？
A: 在 Controller 中使用 `UserContext.getCurrentUserId()` 获取当前用户ID。

### Q: Token 可以自定义有效期吗？
A: 可以，在 `application.yml` 中修改 `jwt.expiration` 配置。

## 测试命令

```bash
# 1. 注册并获取 Token
TOKEN=$(curl -s -X POST http://localhost:8002/api/user/register?platform=app \
  -H "Content-Type: application/json" \
  -d '{"phone":"13800138000","code":"123456","password":"123456","nickname":"测试用户"}' \
  | jq -r '.data.token')

echo "Token: $TOKEN"

# 2. 使用 Token 获取用户信息
curl -X GET http://localhost:8002/api/user/info \
  -H "Authorization: Bearer $TOKEN"

# 3. 使用 Token 获取积分
curl -X GET http://localhost:8002/api/user/points \
  -H "Authorization: Bearer $TOKEN"
```

---

**更新时间**: 2026-07-06  
**版本**: v1.0  
**作者**: Wang Yinuo
