# Port Guardian - 端口守护者

Port Guardian 是一个轻量级的端口监控工具，用于定期检查服务器端口的可达性状态，并在状态发生变化时通过 Webhook 发送通知。

## 🎯 核心功能

- **多协议支持**：支持 TCP 和 UDP 端口检查
- **实时监控**：定期检查配置的服务器端口状态
- **状态变更通知**：当端口状态发生变化时发送 Webhook 通知
- **多平台 Webhook 支持**：适配飞书、钉钉等平台
- **Docker 化部署**：支持容器化部署，便于运维管理
- **可配置重试机制**：支持 Webhook 发送失败重试
- **详细日志记录**：提供完整的操作日志和错误日志

## 目录结构
```
port-guardian/
├── config/ # 配置文件目录
│ └── config.json # 主配置文件 
├── checker/ # 端口检查模块 
├── notifier/ # 通知模块 
├── scheduler/ # 任务调度模块 
├── utils/ # 工具模块 
├── logs/ # 日志目录 
├── main.py # 主程序入口 
├── requirements.txt # Python 依赖 
├── Dockerfile # Docker 镜像构建文件 
├── .dockerignore # Docker 忽略文件 
└── README.md # 项目说明文档
```
## 环境要求

- Python 3.7+
- Docker (可选，用于容器化部署)
- 网络访问权限

## 安装部署

### 方法一：直接运行（推荐用于开发测试）

1. 克隆项目：
```bash
   git clone <repository-url>
   cd port-guardian
   ```
2. 安装依赖：
```bash
    pip install -r requirements.txt
```
3. 配置 `config/config.json` 文件（参考配置说明章节）
4. 运行程序：
```bash
    python main.py
```

### 方法二：Docker 部署（推荐用于生产环境）

1. 构建镜像：
```bash
    docker build -t port-guardian .
```
2. 运行容器：
```bash
 docker run -d
 --name port-guardian 
 -v $(pwd)/config:/app/config 
 -v $(pwd)/logs:/app/logs 
 --restart unless-stopped 
 port-guardian
```
# 配置说明

配置文件位于 `config/config.json`，包含以下主要配置项：
```json
{
  "check_interval": 6,
  "timeout": 5,
  "log_level": "INFO",
  "log_file": "port_guardian.log",
  "servers": [
    {
      "name": "Web服务器",
      "host": "127.0.0.1",
      "port": 8080,
      "protocol": "tcp"
    },
    {
      "name": "HTTPS服务器",
      "host": "127.0.0.1",
      "port": 443,
      "protocol": "tcp"
    },
    {
      "name": "DNS服务器",
      "host": "8.8.8.8",
      "port": 53,
      "protocol": "udp"
    }
  ],
  "webhook": {
    "url": "",
    "method": "POST",
    "msg_type": "text",
    "retry_count": 3,
    "retry_interval": 10
  }
}
```

### 配置项详解

1. **check_interval**：端口检查的时间间隔，单位为秒
2. **timeout**：连接超时时间，单位为秒
3. **log_level**：日志记录级别
4. **log_file**：日志文件名
5. **servers**：要监控的服务器列表
   - **name**：服务器名称，用于标识和日志显示
   - **host**：服务器IP地址或域名
   - **port**：端口号
   - **protocol**：协议类型，支持 tcp 或 udp
6. **webhook**：Webhook通知配置
   - **url**：Webhook地址
   - **method**：HTTP请求方法
   - **msg_type**：消息类型（根据不同平台要求设置）
   - **retry_count**：发送失败时的重试次数
   - **retry_interval**：重试间隔时间（秒）
   - **headers**：自定义HTTP头（可选）

## Webhook 支持

目前支持以下平台的 Webhook：

### 飞书（Lark）
自动识别包含 `feishu.cn` 或 `larksuite.com` 的 URL，使用飞书专用格式发送消息。

### 钉钉
自动识别包含 `dingtalk.com` 的 URL，使用钉钉专用格式发送消息。

### 通用 Webhook
其他平台使用通用格式，适用于大多数 Webhook 服务。


## 日志说明

程序会生成两种日志：

1. **控制台日志**：实时输出到标准输出
2. **文件日志**：保存在 `logs/port_guardian.log` 文件中

日志级别可通过配置文件中的 `log_level` 参数调整，支持 DEBUG、INFO、WARNING、ERROR、CRITICAL。

日志示例：
```log
2023-01-01 12:00:00 - PortGuardian - INFO - PortGuardian 初始化完成 
2023-01-01 12:00:01 - PortChecker - INFO - 初始化端口检查器，超时时间: 5秒 
2023-01-01 12:00:01 - WebhookNotifier - INFO - 初始化Webhook通知器 - URL: https://open.feishu.cn/open-apis/bot/v2/hook/****, 方法: POST, msg_type: text
```

### 常见问题

1. **Webhook 发送失败**
   - 检查 Webhook URL 是否正确
   - 确认网络连接是否正常
   - 查看日志中的错误详情
   - 验证 Webhook 服务是否正常工作

2. **端口检查失败**
   - 确认目标服务器地址和端口是否正确
   - 检查防火墙设置
   - 验证网络连通性
   - 确认目标服务是否正常运行

3. **Docker 部署问题**
   - 确保正确挂载配置文件和日志目录
   - 检查容器日志：`docker logs port-guardian`
   - 确认容器网络配置是否正确

### 查看日志
```json
直接运行方式
tail -f logs/port_guardian.log
Docker 方式
docker logs -f port-guardian
```
