# 微信小程序部署指南

## 项目结构

前端项目已改造为支持微信小程序部署的架构：

```
frontend/
├── src/
│   ├── router/          # 路由配置
│   │   └── index.js
│   ├── utils/           # 工具类
│   │   ├── api.js       # API 接口封装
│   │   └── auth.js      # 认证管理
│   ├── views/           # 页面组件
│   │   ├── Login.vue           # 登录页
│   │   ├── Training.vue        # 训练信息页（主页）
│   │   ├── Profile.vue         # 用户信息页
│   │   └── AnalysisDetail.vue  # 分析详情页
│   ├── App.vue          # 根组件
│   └── main.js          # 入口文件
├── package.json
└── vite.config.js
```

## 页面说明

### 1. 登录页 (Login.vue)
- 支持手机号登录和微信登录
- 用户注册功能
- 验证码发送（需要后端接口支持）

### 2. 训练信息页 (Training.vue)
- 用户统计信息展示（分析次数、积分、VIP等级）
- 视频上传分析功能
- 分析记录列表
- 底部导航栏

### 3. 用户信息页 (Profile.vue)
- 用户头像和基本信息
- 统计数据展示
- 编辑资料功能
- 积分记录查看
- 退出登录

### 4. 分析详情页 (AnalysisDetail.vue)
- 分析结果详细展示
- 基础数据（手臂速度、挥棒速度等）
- 高级分析数据（速度曲线、对称性、轨迹平滑度、能量传递）
- 骨骼视频播放

## 部署到微信小程序

### 方案一：使用 uni-app 转换（推荐）

1. **安装 uni-app CLI**
```bash
npm install -g @dcloudio/uvm
uvm
```

2. **创建 uni-app 项目**
```bash
vue create -p dcloudio/uni-preset-vue my-wechat-app
```

3. **迁移页面**
将 `src/views/` 下的 Vue 文件复制到 uni-app 项目的 `pages/` 目录

4. **调整代码**
- 将 `el-*` 组件替换为 uni-app 组件
- 将 `axios` 替换为 `uni.request`
- 将 `localStorage` 替换为 `uni.setStorageSync`

5. **编译为微信小程序**
```bash
npm run build:mp-weixin
```

### 方案二：使用 Taro 转换

1. **安装 Taro CLI**
```bash
npm install -g @tarojs/cli
```

2. **创建 Taro 项目**
```bash
taro init my-wechat-app
```

3. **迁移页面**
Taro 支持 React/Vue 语法，可以直接迁移大部分代码

4. **编译为微信小程序**
```bash
npm run build:weapp
```

### 方案三：WebView 方式（最简单）

1. **部署前端到服务器**
```bash
npm run build
# 将 dist 目录部署到 Nginx/Apache
```

2. **在微信小程序中使用 WebView**
```javascript
// 小程序页面
Page({
  data: {
    url: 'https://your-domain.com'
  }
})
```

```html
<!-- 小程序页面 -->
<web-view src="{{url}}"></web-view>
```

## 关键代码调整

### 1. API 请求适配

**当前代码 (axios)**
```javascript
import axios from 'axios'

const response = await axios.get('/api/user/info')
```

**微信小程序版本**
```javascript
const request = (url, method, data) => {
  return new Promise((resolve, reject) => {
    uni.request({
      url: `https://your-domain.com${url}`,
      method,
      data,
      header: {
        'Authorization': `Bearer ${uni.getStorageSync('token')}`
      },
      success: (res) => {
        resolve(res)
      },
      fail: (err) => {
        reject(err)
      }
    })
  })
}

const response = await request('/api/user/info', 'GET')
```

### 2. 本地存储适配

**当前代码 (localStorage)**
```javascript
localStorage.setItem('token', token)
const token = localStorage.getItem('token')
```

**微信小程序版本**
```javascript
uni.setStorageSync('token', token)
const token = uni.getStorageSync('token')
```

### 3. 路由适配

**当前代码 (vue-router)**
```javascript
router.push('/profile')
```

**微信小程序版本**
```javascript
uni.navigateTo({
  url: '/pages/profile/profile'
})
```

### 4. 文件上传适配

**当前代码 (FormData)**
```javascript
const formData = new FormData()
formData.append('video', file)
await axios.post('/api/video/analyze', formData)
```

**微信小程序版本**
```javascript
uni.chooseVideo({
  success: (res) => {
    uni.uploadFile({
      url: 'https://your-domain.com/api/video/analyze',
      filePath: res.tempFilePath,
      name: 'video',
      formData: {
        userId: userId,
        actionType: 'batting'
      },
      header: {
        'Authorization': `Bearer ${token}`
      },
      success: (uploadRes) => {
        console.log(uploadRes.data)
      }
    })
  }
})
```

## 后端接口配置

### 1. CORS 配置

确保后端允许微信小程序的请求：

```java
@Configuration
public class WebMvcConfig implements WebMvcConfigurer {
    @Override
    public void addCorsMappings(CorsRegistry registry) {
        registry.addMapping("/**")
                .allowedOriginPatterns("*")
                .allowedMethods("GET", "POST", "PUT", "DELETE", "OPTIONS")
                .allowedHeaders("*")
                .allowCredentials(true)
                .maxAge(3600);
    }
}
```

### 2. 域名配置

在微信小程序后台配置合法域名：
- 登录小程序后台
- 开发 -> 开发管理 -> 开发设置 -> 服务器域名
- 添加 request 合法域名：`https://your-domain.com`

## 微信登录集成

### 1. 小程序端获取 code

```javascript
wx.login({
  success: (res) => {
    const code = res.code
    // 发送 code 到后端
    uni.request({
      url: 'https://your-domain.com/api/user/login/wechat',
      method: 'POST',
      data: { code },
      success: (res) => {
        const { token, userId } = res.data.data
        uni.setStorageSync('token', token)
        uni.setStorageSync('userId', userId)
      }
    })
  }
})
```

### 2. 后端处理微信登录

```java
@PostMapping("/login/wechat")
public BaseResponse<LoginResponse> wechatLogin(@RequestBody WechatLoginRequest request) {
    // 调用微信接口获取 openid
    String url = "https://api.weixin.qq.com/sns/jscode2session" +
                 "?appid=" + appId +
                 "&secret=" + appSecret +
                 "&js_code=" + request.getCode() +
                 "&grant_type=authorization_code";
    
    String response = restTemplate.getForObject(url, String.class);
    JSONObject json = JSON.parseObject(response);
    String openId = json.getString("openid");
    String unionId = json.getString("unionid");
    
    // 查询或创建用户
    UserDTO user = userService.getUserByOpenIdWechat(openId);
    if (user == null) {
        user = new UserDTO();
        user.setOpenIdWechat(openId);
        user.setUnionId(unionId);
        user.setNickname("微信用户");
        // ... 设置其他字段
        userService.save(user);
    }
    
    // 生成 token
    String token = jwtUtil.generateToken(user.getId(), "wechat");
    
    // 返回响应
    LoginResponse loginResponse = new LoginResponse();
    loginResponse.setToken(token);
    loginResponse.setUserId(user.getId());
    // ... 设置其他字段
    
    return BaseResponse.success(loginResponse);
}
```

## 测试清单

### 功能测试
- [ ] 登录功能（手机号、微信）
- [ ] 用户注册
- [ ] 视频上传
- [ ] 分析结果查看
- [ ] 用户信息编辑
- [ ] 积分记录查看
- [ ] 退出登录

### 兼容性测试
- [ ] iOS 微信
- [ ] Android 微信
- [ ] 不同屏幕尺寸

### 性能测试
- [ ] 页面加载速度
- [ ] 视频上传速度
- [ ] 分析结果加载速度

## 常见问题

### Q1: 小程序无法访问后端接口？
A: 检查以下几点：
1. 后端是否配置了 CORS
2. 小程序后台是否配置了合法域名
3. 是否使用了 HTTPS

### Q2: 视频上传失败？
A: 检查以下几点：
1. 视频大小是否超过限制（小程序限制 10MB）
2. 后端是否支持大文件上传
3. 网络是否正常

### Q3: 登录状态丢失？
A: 检查以下几点：
1. Token 是否正确保存到本地存储
2. Token 是否过期
3. 请求头是否正确携带 Token

## 后续优化

1. **离线缓存**
   - 缓存用户信息
   - 缓存分析记录

2. **消息推送**
   - 分析完成通知
   - 系统消息推送

3. **分享功能**
   - 分享分析结果
   - 邀请好友

4. **数据统计**
   - 用户行为分析
   - 使用数据统计

## 参考文档

- [微信小程序官方文档](https://developers.weixin.qq.com/miniprogram/dev/framework/)
- [uni-app 官方文档](https://uniapp.dcloud.net.cn/)
- [Taro 官方文档](https://taro-docs.jd.com/)

---

**更新时间**: 2026-07-06  
**版本**: v1.0  
**作者**: Wang Yinuo
