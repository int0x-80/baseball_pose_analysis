# 视频记录查询 API 文档

## 概述

本文档描述了视频记录查询相关的 API 接口，支持分页查询和日历展示功能。

## 接口列表

### 1. 查询用户视频记录（分页）

**接口地址**: `POST /api/video/records`

**功能描述**: 分页查询当前登录用户的视频分析记录，支持按日期范围、动作类型、状态等条件筛选。

**请求参数**:

```json
{
  "startDate": "2026-07-01",
  "endDate": "2026-07-31",
  "actionType": "batting",
  "status": 1,
  "pageNum": 1,
  "pageSize": 10,
  "sortBy": "createTime",
  "sortOrder": "desc"
}
```

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| startDate | String | 否 | 开始日期，格式：yyyy-MM-dd |
| endDate | String | 否 | 结束日期，格式：yyyy-MM-dd |
| actionType | String | 否 | 动作类型：batting-击球, pitching-投球 |
| status | Integer | 否 | 状态：0-分析中, 1-已完成, 2-失败 |
| pageNum | Integer | 否 | 页码，默认 1，最小 1 |
| pageSize | Integer | 否 | 每页大小，默认 10，范围 1-100 |
| sortBy | String | 否 | 排序字段：createTime-创建时间, updateTime-更新时间，默认 createTime |
| sortOrder | String | 否 | 排序方向：asc-升序, desc-降序，默认 desc |

**响应示例**:

```json
{
  "code": "200",
  "message": "success",
  "data": {
    "records": [
      {
        "recordId": "20260707141200abc123",
        "actionType": "batting",
        "status": 1,
        "overallScore": 85.5,
        "grade": "A",
        "skeletonVideoName": "videos/20260707141200abc123.mp4",
        "createTime": "2026-07-07T14:12:00",
        "updateTime": "2026-07-07T14:15:30"
      }
    ],
    "total": 25,
    "pageNum": 1,
    "pageSize": 10,
    "totalPages": 3,
    "hasNext": true,
    "hasPrevious": false
  }
}
```

**响应字段说明**:

| 字段名 | 类型 | 说明 |
|--------|------|------|
| records | Array | 记录列表 |
| records[].recordId | String | 记录ID |
| records[].actionType | String | 动作类型 |
| records[].status | Integer | 状态：0-分析中, 1-已完成, 2-失败 |
| records[].overallScore | Double | 总评分（仅已完成时有值） |
| records[].grade | String | 等级（仅已完成时有值） |
| records[].skeletonVideoName | String | 骨骼视频文件名 |
| records[].createTime | String | 创建时间 |
| records[].updateTime | String | 更新时间 |
| total | Long | 总记录数 |
| pageNum | Integer | 当前页码 |
| pageSize | Integer | 每页大小 |
| totalPages | Integer | 总页数 |
| hasNext | Boolean | 是否有下一页 |
| hasPrevious | Boolean | 是否有上一页 |

---

### 2. 查询每日记录数（日历展示）

**接口地址**: `GET /api/video/records/daily-count`

**功能描述**: 查询指定月份的每日记录数，用于日历展示。

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| year | Integer | 是 | 年份，如：2026 |
| month | Integer | 是 | 月份，范围 1-12 |

**请求示例**:

```
GET /api/video/records/daily-count?year=2026&month=7
```

**响应示例**:

```json
{
  "code": "200",
  "message": "success",
  "data": {
    "1": 3,
    "5": 2,
    "7": 1,
    "10": 4,
    "15": 2,
    "20": 1,
    "25": 3,
    "30": 2
  }
}
```

**响应字段说明**:

- key: 日期（1-31）
- value: 当天的记录数

---

## 使用场景

### 场景 1: 日历展示

1. 前端加载页面时，调用 `/api/video/records/daily-count` 获取当月每日记录数
2. 在日历上标记有记录的日期（显示记录数或不同颜色）
3. 用户点击某个日期时，调用 `/api/video/records` 查询当天的记录

**示例代码**:

```javascript
// 获取当月每日记录数
async function loadDailyCount(year, month) {
  const response = await fetch(`/api/video/records/daily-count?year=${year}&month=${month}`, {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  const data = await response.json();
  return data.data; // { 1: 3, 5: 2, ... }
}

// 获取某天的记录
async function loadDailyRecords(date) {
  const response = await fetch('/api/video/records', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({
      startDate: date,
      endDate: date,
      pageNum: 1,
      pageSize: 20
    })
  });
  const data = await response.json();
  return data.data.records;
}
```

### 场景 2: 记录列表展示

1. 前端加载页面时，调用 `/api/video/records` 获取第一页记录
2. 显示记录列表（包含评分、等级、状态等）
3. 用户滚动到底部时，加载下一页

**示例代码**:

```javascript
// 获取记录列表
async function loadRecords(pageNum = 1, filters = {}) {
  const response = await fetch('/api/video/records', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({
      pageNum,
      pageSize: 10,
      ...filters
    })
  });
  const data = await response.json();
  return data.data;
}

// 加载更多
async function loadMoreRecords(currentPage, filters) {
  const data = await loadRecords(currentPage + 1, filters);
  if (data.hasNext) {
    // 继续加载
  }
  return data.records;
}
```

---

## 性能优化

### 数据库索引

已添加以下索引以优化查询性能：

1. **video_metadata 表**:
   - `idx_user_id`: 用户ID索引
   - `idx_create_time`: 创建时间索引
   - `idx_user_create_time`: 复合索引（用户ID + 创建时间）

2. **video_analysis_result 表**:
   - `idx_record_id`: 记录ID索引（唯一）
   - `idx_user_id`: 用户ID索引

### 查询优化

1. **分页查询**: 使用 LIMIT 和 OFFSET 实现分页，避免全表扫描
2. **条件筛选**: 使用动态 SQL，只查询必要的字段
3. **JOIN 优化**: 使用 LEFT JOIN 关联 video_metadata 和 video_analysis_result 表
4. **排序优化**: 支持按创建时间和更新时间排序

### 缓存策略（建议）

对于频繁查询的数据，可以考虑添加 Redis 缓存：

1. **每日记录数缓存**: 缓存当月的每日记录数，TTL 为 1 小时
2. **记录列表缓存**: 缓存第一页记录，TTL 为 5 分钟

---

## 错误处理

### 常见错误

| 错误码 | 说明 | 解决方案 |
|--------|------|----------|
| 401 | 未登录或 Token 无效 | 重新登录获取 Token |
| 400 | 参数错误 | 检查请求参数格式 |
| 500 | 服务器内部错误 | 查看服务器日志 |

### 错误响应示例

```json
{
  "code": "401",
  "message": "未提供认证Token",
  "data": null
}
```

---

## 测试命令

### 测试查询记录列表

```bash
curl -X POST http://localhost:8002/api/video/records \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "pageNum": 1,
    "pageSize": 10,
    "sortBy": "createTime",
    "sortOrder": "desc"
  }'
```

### 测试查询每日记录数

```bash
curl -X GET "http://localhost:8002/api/video/records/daily-count?year=2026&month=7" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 数据库变更

需要执行以下 SQL 脚本来添加必要的字段和索引：

```sql
-- 为 video_analysis_result 表添加评分和等级字段
ALTER TABLE video_analysis_result
ADD COLUMN overall_score DECIMAL(5,2) DEFAULT NULL COMMENT '总评分(0-100)' AFTER action_type,
ADD COLUMN grade VARCHAR(10) DEFAULT NULL COMMENT '等级(A/B/C/D/E)' AFTER overall_score;

-- 为 video_metadata 表添加复合索引以优化查询性能
ALTER TABLE video_metadata
ADD INDEX idx_user_create_time (user_id, create_time);
```

执行脚本：

```bash
mysql -u root -proot pose_analysis < /Users/wangyinuo/workspace/code/ai/baseball_pose_analysis/user-service/src/main/resources/sql/alter_add_score_fields.sql
```

---

**更新时间**: 2026-07-07  
**版本**: v1.0  
**作者**: Wang Yinuo
