# 用户身份传递方案设计

## 概述

本方案实现了一个统一的用户身份传递机制，支持在微服务架构中通过 JWT Token 在 Gateway 层解析用户信息，并通过 HTTP Header 传递给下游服务。

## 架构图

```
客户端
  ↓ (携带 JWT Token)
Gateway (JwtAuthFilter)
  ↓ (解析 Token，提取 userId 和 platform)
  ↓ (添加到 Header: X-User-Id, X-Platform)
下游服务 (user-service, storage-service 等)
  ↓ (从 Header 或 Token 获取用户信息)
  ↓ (使用 UserContext.getCurrentUserId())
```

## 核心组件

### 1. commons-api 模块

#### 1.1 JwtUtil (通用 JWT 工具类)

位置：`commons-api/src/main/java/com/baseball/commons/util/JwtUtil.java`

功能：
- 生成 JWT Token
- 解析 Token 获取用户信息
- 验证 Token 有效性

使用示例：
```java
// 生成 Token
String token = JwtUtil.generateToken(userId, "app");

// 解析 Token
Long userId = JwtUtil.getUserIdFromToken(token);
String platform = JwtUtil.getPlatformFromToken(token);

// 验证 Token
boolean isValid = JwtUtil.validateToken(token);
```

#### 1.2 UserContext (用户上下文工具类)

位置：`commons-api/src/main/java/com/baseball/commons/util/UserContext.java`

功能：
- 获取当前登录用户ID
- 获取当前登录平台
- 检查登录状态

使用示例：
```java
// 获取当前用户ID
Long userId = UserContext.getCurrentUserId();

// 获取当前平台
String platform = UserContext.getCurrentPlatform();

// 检查是否已登录
if (UserContext.isLoggedIn()) {
    // 已登录逻辑
}

// 检查平台类型
if (UserContext.isFromWechat()) {
    // 微信小程序逻辑
}
```

### 2. gateway-service 模块

#### 2.1 JwtAuthFilter (JWT 认证过滤器)

位置：`gateway-service/src/main/java/com/baseball/gateway/filter/JwtAuthFilter.java`

功能：
- 拦截所有请求（除白名单外）
- 验证 JWT Token
- 解析用户信息
- 将用户信息添加到 Header 传递给下游

白名单路径（不需要认证）：
- `/api/user/login`
- `/api/user/register`
- `/api/health`
- `/swagger-resources`
- `/v2/api-docs`
- `/webjars`

### 3. user-service 模块

#### 3.1 JwtUtil (简化版)

位置：`user-service/src/main/java/com/baseball/user/config/JwtUtil.java`

功能：
- 委托给 commons-api 的通用实现
- 保持向后兼容

#### 3.2 UserContext (简化版)

位置：`user-service/src/main/java/com/baseball/user/config/UserContext.java`

功能：
- 委托给 commons-api 的通用实现
- 保持向后兼容

## 使用方式

### 方式一：通过 Gateway 访问（推荐）

客户端请求：
```bash
curl -X GET http://localhost:8001/api/user/info \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiJ9..."
```

Gateway 处理流程：
1. 从 Header 提取 Token
2. 验证 Token 有效性
3. 解析 userId 和 platform
4. 添加到 Header：`X-User-Id: 123`, `X-Platform: app`
5. 转发给下游服务

下游服务获取用户信息：
```java
@RestController
@RequestMapping("/api/user")
public class UserController {
    
    @GetMapping("/info")
    public BaseResponse<UserResponse> getUserInfo() {
        // 从 Header 获取用户ID
        Long userId = UserContext.getCurrentUserId();
        String platform = UserContext.getCurrentPlatform();
        
        // 业务逻辑
        UserResponse response = userService.getUserInfo(userId);
        return BaseResponse.success(response);
    }
}
```

### 方式二：直接访问服务（开发/测试）

客户端请求：
```bash
curl -X GET http://localhost:8002/api/user/info \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiJ9..."
```

服务处理流程：
1. 从 Header 提取 Token
2. 解析 userId 和 platform
3. 执行业务逻辑

### 方式三：URL 参数传递 Token

```bash
curl -X GET "http://localhost:8002/api/user/info?token=eyJhbGciOiJIUzI1NiJ9..."
```

## 在不同服务中使用

### 1. user-service

```java
@RestController
@RequestMapping("/api/user")
public class UserController {
    
    @GetMapping("/info")
    public BaseResponse<UserResponse> getUserInfo() {
        Long userId = UserContext.getCurrentUserId();
        // ...
    }
    
    @PutMapping("/update")
    public BaseResponse<String> updateUser(@RequestBody UserUpdateRequest request) {
        Long userId = UserContext.getCurrentUserId();
        // ...
    }
}
```

### 2. storage-service

```java
@RestController
@RequestMapping("/api/storage")
public class StorageController {
    
    @PostMapping("/upload")
    public BaseResponse<VideoResponse> upload(@RequestParam("file") MultipartFile file) {
        Long userId = UserContext.getCurrentUserId();
        String platform = UserContext.getCurrentPlatform();
        
        // 根据用户和平台处理上传逻辑
        // ...
    }
}
```

### 3. card-service

```java
@RestController
@RequestMapping("/api/card")
public class CardController {
    
    @GetMapping("/list")
    public BaseResponse<List<CardResponse>> listCards() {
        Long userId = UserContext.getCurrentUserId();
        
        // 查询用户的球星卡列表
        // ...
    }
}
```

## 前端使用示例

### 1. 登录获取 Token

```javascript
// 微信登录
const response = await fetch('/api/user/login/wechat', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    code: 'wx_auth_code'
  })
});

const data = await response.json();
const token = data.data.token;

// 保存 Token
localStorage.setItem('token', token);
```

### 2. 携带 Token 访问接口

```javascript
// 方式一：使用 Authorization Header
const response = await fetch('/api/user/info', {
  headers: {
    'Authorization': `Bearer ${localStorage.getItem('token')}`
  }
});

// 方式二：使用 URL 参数
const response = await fetch(`/api/user/info?token=${localStorage.getItem('token')}`);
```

### 3. Axios 拦截器配置

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

## Token 结构

```json
{
  "userId": 123,
  "platform": "app",
  "sub": "123",
  "iat": 1688672400,
  "exp": 1688758800
}
```

## 安全建议

1. **Token 存储**
   - 使用 localStorage 或 sessionStorage
   - 敏感应用建议使用 httpOnly Cookie

2. **Token 有效期**
   - 默认 24 小时
   - 建议实现 Token 刷新机制

3. **HTTPS**
   - 生产环境必须使用 HTTPS
   - 防止 Token 在传输过程中被窃取

4. **密钥管理**
   - 使用强密钥（至少 256 位）
   - 不要硬编码在代码中
   - 使用环境变量或配置中心

## 扩展功能

### 1. Token 刷新

可以实现 refresh token 机制，在 access token 过期前自动刷新。

### 2. 多设备登录

可以记录用户的登录设备，实现多设备管理。

### 3. Token 黑名单

可以实现 Token 黑名单机制，支持用户主动登出。

### 4. 权限控制

可以在 Token 中添加角色信息，实现基于角色的权限控制。

## 常见问题

### Q1: 为什么不直接在每个服务中解析 Token？

A: 在 Gateway 统一解析有以下优势：
- 减少重复代码
- 集中管理认证逻辑
- 便于统一更新和维护
- 下游服务无需关心 Token 解析细节

### Q2: 如果 Gateway 挂了怎么办？

A: UserContext 实现了双重机制：
- 优先从 Header 获取（Gateway 已解析）
- 兜底从 Token 解析（直接访问服务时）

### Q3: 如何添加新的白名单路径？

A: 修改 `JwtAuthFilter.java` 中的 `WHITE_LIST` 列表：

```java
private static final List<String> WHITE_LIST = Arrays.asList(
    "/api/user/login",
    "/api/user/register",
    "/api/health",
    "/api/public/xxx"  // 添加新的白名单路径
);
```

### Q4: 如何在服务间调用时传递用户信息？

A: 使用 Feign 拦截器：

```java
@Component
public class FeignUserInterceptor implements RequestInterceptor {
    @Override
    public void apply(RequestTemplate template) {
        Long userId = UserContext.getCurrentUserId();
        String platform = UserContext.getCurrentPlatform();
        
        if (userId != null) {
            template.header("X-User-Id", String.valueOf(userId));
        }
        if (platform != null) {
            template.header("X-Platform", platform);
        }
    }
}
```

## 总结

本方案实现了一个灵活、可扩展的用户身份传递机制：

1. **统一认证**：Gateway 层统一处理 Token 验证
2. **信息传递**：通过 Header 传递用户信息
3. **双重保障**：支持从 Header 或 Token 获取用户信息
4. **易于扩展**：基于 commons-api，所有服务可复用
5. **向后兼容**：保持原有接口不变

这个方案可以很好地支持微服务架构下的用户身份管理需求。
