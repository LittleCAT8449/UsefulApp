# B站 UP主追踪服务器

订阅 B站 UP主，自动追踪视频/文章更新，支持视频下载，为手机 App 提供 REST API 和 WebSocket 实时推送。

## 快速开始

### 环境要求

- Python >= 3.12
- ffmpeg（视频下载合并需要，[下载地址](https://ffmpeg.org/download.html)）

### 1. 安装依赖

```bash
cd F:\PythonProject
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 2. 配置

编辑 `.env` 文件，按需修改：

```env
# 数据库（默认 SQLite，无需改动）
DATABASE_URL=sqlite+aiosqlite:///./data/bilibili_tracker.db

# JWT 密钥（生产环境请修改为随机字符串）
SECRET_KEY=change-me-to-a-random-secret-key

# 设备配对码（手机 App 首次连接用）
DEVICE_PAIR_CODE=123456

# 爬虫检查间隔（分钟）
CHECK_INTERVAL_MINUTES=30

# 下载路径
DOWNLOAD_PATH=./data/downloads
COVER_PATH=./data/covers

# 最大同时下载数
MAX_CONCURRENT_DOWNLOADS=2

# 请求频率限制（次/秒）
RATE_LIMIT_PER_SECOND=3

# 是否自动下载新视频
AUTO_DOWNLOAD_NEW_VIDEOS=false

# 日志级别
LOG_LEVEL=INFO

# B站 Cookie（可选，填了可以下载高画质视频）
BILIBILI_SESSDATA=
BILIBILI_BILI_JCT=
```

### 3. 启动服务器

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

启动后访问：
- **API 文档 (Swagger UI)**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/

---

## 认证（JWT）

### 开发模式（默认）

`.env` 中 `AUTH_ENABLED=false`，所有 API 免认证访问，方便开发调试。

### 生产模式

修改 `.env`：

```env
AUTH_ENABLED=true
SECRET_KEY=你的随机密钥（至少32字符）
DEVICE_PAIR_CODE=你的配对码（建议6位以上数字）
```

重启服务器后，所有 API 需要 JWT 认证。

### 设备登录（手机 App 首次连接）

```bash
curl -X POST http://localhost:8000/api/v1/auth/device/login \
  -H "Content-Type: application/json" \
  -d '{"pair_code": "123456"}'
```

成功返回 JWT Token：
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 2592000
}
```

### 携带 Token 访问

```bash
curl http://localhost:8000/api/v1/up/list \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
```

### WebSocket 认证

```
ws://localhost:8000/ws/notifications?token=eyJhbGciOiJIUzI1NiIs...
```

### 认证状态查询

```bash
curl http://localhost:8000/api/v1/auth/status
```

---

## API 使用指南

所有 API 前缀为 `/api/v1`。

### UP主管理

#### 添加追踪

```bash
curl -X POST http://localhost:8000/api/v1/up/add \
  -H "Content-Type: application/json" \
  -d '{"bilibili_uid": 2}'
```

响应示例：
```json
{
  "id": 1,
  "bilibili_uid": 2,
  "name": "碧诗",
  "face_url": "https://i2.hdslb.com/bfs/face/...",
  "level": 6,
  "follower_count": 0,
  "video_count": 0,
  "is_active": true,
  "notify_new_video": true,
  "notify_new_article": true,
  "last_checked_at": null,
  "created_at": "2026-06-04T12:29:03"
}
```

#### 获取追踪列表

```bash
# 全部列表
curl http://localhost:8000/api/v1/up/list

# 分页 + 搜索
curl "http://localhost:8000/api/v1/up/list?page=1&page_size=20&search=碧诗"
```

#### 获取 UP主详情

```bash
curl http://localhost:8000/api/v1/up/2
```

#### 更新追踪设置

```bash
curl -X PUT http://localhost:8000/api/v1/up/2 \
  -H "Content-Type: application/json" \
  -d '{"notify_new_video": true, "notify_new_article": false}'
```

可更新字段：
| 字段 | 类型 | 说明 |
|---|---|---|
| `is_active` | bool | 是否启用追踪 |
| `notify_new_video` | bool | 新视频通知 |
| `notify_new_article` | bool | 新文章通知 |
| `notify_video_download` | bool | 自动下载新视频 |

#### 立即刷新（强制检查更新）

```bash
curl -X POST http://localhost:8000/api/v1/up/2/refresh
```

响应：
```json
{"message": "刷新完成: UP信息=已更新, 新视频=42, 新文章=0"}
```

#### 移除追踪

```bash
# 软删除（保留数据，停止追踪）
curl -X DELETE http://localhost:8000/api/v1/up/2

# 硬删除（删除所有关联数据）
curl -X DELETE "http://localhost:8000/api/v1/up/2?hard=true"
```

---

### 视频

#### 视频列表

```bash
# 全部视频（按发布时间倒序）
curl "http://localhost:8000/api/v1/videos?page=1&page_size=20"

# 按 UP主筛选
curl "http://localhost:8000/api/v1/videos?up_uid=2"

# 自定义排序
curl "http://localhost:8000/api/v1/videos?sort_by=view_count&order=desc"
```

支持的排序字段：`pubdate`（默认）、`view_count`、`danmaku_count`、`like_count`、`created_at`

#### 某 UP主的视频

```bash
curl "http://localhost:8000/api/v1/up/2/videos?page=1&page_size=20"
```

#### 视频详情

```bash
curl http://localhost:8000/api/v1/videos/BV172421f7Km
```

#### 请求下载视频

```bash
curl -X POST http://localhost:8000/api/v1/videos/BV172421f7Km/download \
  -H "Content-Type: application/json" \
  -d '{"quality": 80}'
```

画质代码：

| qn | 画质 | 需要登录 |
|---|---|---|
| 16 | 360P | 否 |
| 32 | 480P | 否 |
| 64 | 720P | 否 |
| 80 | 1080P | 否 |
| 112 | 1080P+ | 是 |
| 116 | 1080P60 | 是 |
| 120 | 4K | 是 |

#### 删除视频

```bash
curl -X DELETE http://localhost:8000/api/v1/videos/BV172421f7Km
```

---

### 专栏文章

#### 文章列表

```bash
curl "http://localhost:8000/api/v1/articles?page=1&page_size=20"

# 按 UP主筛选
curl "http://localhost:8000/api/v1/articles?up_uid=2"
```

#### 某 UP主的文章

```bash
curl "http://localhost:8000/api/v1/up/2/articles"
```

#### 文章详情（含正文）

```bash
curl http://localhost:8000/api/v1/articles/12345
```

---

### 下载管理

#### 下载任务列表

```bash
curl "http://localhost:8000/api/v1/downloads?page=1&page_size=20"

# 按状态筛选
curl "http://localhost:8000/api/v1/downloads?status=completed"
```

状态值：`pending`、`downloading_video`、`downloading_audio`、`merging`、`completed`、`failed`

#### 下载任务详情（含进度）

```bash
curl http://localhost:8000/api/v1/downloads/1
```

#### 重试失败任务

```bash
curl -X POST http://localhost:8000/api/v1/downloads/1/retry
```

#### 取消下载

```bash
curl -X POST http://localhost:8000/api/v1/downloads/1/cancel
```

#### 获取已下载视频文件

```bash
# 浏览器直接打开或 curl 下载
curl -O http://localhost:8000/api/v1/files/downloads/BVxxxxx/BVxxxxx.mp4
```

#### 删除下载任务及文件

```bash
curl -X DELETE http://localhost:8000/api/v1/downloads/1
```

---

### 通知

#### 通知列表

```bash
# 全部通知
curl "http://localhost:8000/api/v1/notifications?page=1&page_size=20"

# 只看未读
curl "http://localhost:8000/api/v1/notifications?is_read=false"

# 按类型筛选
curl "http://localhost:8000/api/v1/notifications?type=new_video"
```

通知类型：`new_video`、`new_article`、`video_update`、`download_complete`、`download_failed`、`system`

#### 未读数量

```bash
curl http://localhost:8000/api/v1/notifications/unread-count
```

#### 标记已读

```bash
# 单条已读
curl -X PUT http://localhost:8000/api/v1/notifications/1/read

# 全部已读
curl -X PUT http://localhost:8000/api/v1/notifications/read-all
```

---

### WebSocket 实时推送

#### 连接

```
ws://localhost:8000/ws/notifications?token=<jwt_token>
```

> 当前 Phase 1-3 阶段无需 token，可直接连接。

#### 接收消息格式

**新内容通知：**
```json
{
  "type": "notification",
  "data": {
    "id": 1,
    "type": "new_video",
    "title": "新视频: xxx",
    "message": "UP主 碧诗 发布了新视频「xxx」",
    "up_user": {"uid": 2, "name": "碧诗"},
    "reference_type": "video",
    "reference_id": 5,
    "thumbnail_url": "/api/v1/files/covers/BVxxxxx.jpg",
    "created_at": "2026-06-04T12:00:00Z"
  }
}
```

**下载进度：**
```json
{
  "type": "download_progress",
  "data": {
    "task_id": 1,
    "video_id": 5,
    "bvid": "BVxxxxx",
    "progress": 0.65,
    "status": "downloading_video"
  }
}
```

**心跳：**
```json
{"type": "ping"}
```

客户端收到 `ping` 后应回复 `{"type": "pong"}`。

#### JavaScript 示例

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/notifications');

ws.onopen = () => console.log('已连接');
ws.onmessage = (event) => {
  const msg = JSON.parse(event.data);
  if (msg.type === 'notification') {
    console.log('新通知:', msg.data.title);
  } else if (msg.type === 'download_progress') {
    console.log(`下载进度: ${(msg.data.progress * 100).toFixed(0)}%`);
  } else if (msg.type === 'ping') {
    ws.send(JSON.stringify({type: 'pong'}));
  }
};
ws.onclose = () => console.log('已断开');
```

---

### 系统

#### 运行状态

```bash
curl http://localhost:8000/api/v1/system/status
```

响应：
```json
{
  "status": "running",
  "uptime_display": "2h 15m 30s",
  "active_up_count": 5,
  "video_count": 230,
  "article_count": 12,
  "download_pending": 1,
  "download_completed": 3,
  "ws_connections": 2
}
```

#### 系统配置

```bash
# 查看配置
curl http://localhost:8000/api/v1/system/config

# 修改配置
curl -X PUT http://localhost:8000/api/v1/system/config \
  -H "Content-Type: application/json" \
  -d '{"check_interval_minutes": "15", "auto_download_new_videos": "true"}'
```

---

## 文件服务

### 封面图片

```
GET /api/v1/files/covers/{bvid}.jpg
```

例如：`http://localhost:8000/api/v1/files/covers/BV172421f7Km.jpg`

### 已下载视频

```
GET /api/v1/files/downloads/{bvid}/{bvid}.mp4
```

支持 HTTP Range 请求（拖动进度条），适合移动端播放。

---

## 爬虫工作原理

1. 服务器每 **30 分钟**（可配置）自动检查所有活跃 UP主
2. 按"最久未检查"顺序逐个处理，UP主之间间隔 1 秒
3. 对每个 UP主：更新基本信息 → 拉取视频列表 → 对比已有数据 → 只保存新内容
4. 发现新视频/文章时：自动下载封面 + 生成数据库通知 + WebSocket 广播
5. 低频更新的 UP主会被自动延长检查间隔

---

## 目录结构

```
F:\PythonProject\
├── app/                     # 应用代码
│   ├── main.py              # FastAPI 入口
│   ├── config.py            # 配置
│   ├── database.py          # 数据库
│   ├── models/              # ORM 模型（6张表）
│   ├── schemas/             # Pydantic 模型
│   ├── api/                 # API 路由
│   ├── services/            # 业务逻辑
│   ├── crawler/             # 爬虫引擎
│   └── notifications/       # WebSocket 管理
├── data/                    # 运行时数据
│   ├── covers/              # 封面图缓存
│   └── downloads/           # 下载视频
├── requirements.txt
├── .env                     # 环境配置
└── README.md
```

---

## 常见问题

### Q: 如何获取 UP主的 UID？

打开 UP主的 B站空间页，URL 中的数字即为 UID：
- `https://space.bilibili.com/2` → UID = `2`

### Q: 为什么 follower_count 显示为 0？

部分 B站 API 返回的字段名随库版本变化。刷新一次即可获取正确的统计数据。不影响核心功能。

### Q: 如何下载高画质视频？

在 `.env` 中配置你的 B站 Cookie：
1. 浏览器登录 B站
2. F12 → Application → Cookies → 复制 `SESSDATA` 和 `bili_jct` 的值
3. 填入 `.env` 中的 `BILIBILI_SESSDATA` 和 `BILIBILI_BILI_JCT`

### Q: 如何让手机 App 连接到服务器？

1. 确保手机和服务器在同一网络
2. 将 `host` 设为 `0.0.0.0`
3. 手机 App 通过局域网 IP 访问，如 `http://192.168.1.100:8000/api/v1/`

### Q: 如何修改检查频率？

```bash
curl -X PUT http://localhost:8000/api/v1/system/config \
  -H "Content-Type: application/json" \
  -d '{"check_interval_minutes": "10"}'
```

