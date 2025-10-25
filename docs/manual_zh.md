# DataMonitor 用户手册（简体中文）

本手册面向终端用户，聚焦“如何使用 DataMonitor 桌面客户端完成监控配置、任务管理、日志与通知设置”。若需了解开发或部署流程，请参阅仓库根目录的 README。

---

## 1. 软件概述

DataMonitor 是一款桌面级监控工具，结合可视化配置与邮件通知，帮助团队快速接入 HTTP/API/主机可用性探测。主要能力如下：

- **监控仪表盘**：以卡片视图显示本地/UTC 时间与实时日志，支持热切主题与语言。
- **配置向导**：通过表单化操作新增 GET、POST、SERVER 三种监控类型，并提供 JSON 负载编辑、字段校验和邮件预览。
- **偏好中心**：集中管理时区、语言、主题以及日志滚动策略。
- **通知体系**：内置模板化邮件告警，可根据不同监控项使用差异化收件人和语言。
- **文档中心**：在应用内直接查看许可证摘要与双语手册。

---

## 2. 界面导览与工作流

| 导航标签 | 作用 | 常用操作 |
| --- | --- | --- |
| 监控 Monitor | 展示时钟、实时日志、监控状态 | 启动/停止调度、查看最近事件、确认状态栏提示 |
| 配置 Configuration | 管理监控任务 | 新增/删除监控项、编辑 Payload/Headers、预览通知内容 |
| 设置 Preferences | 偏好与日志 | 设置时区、主题语言、日志目录、滚动策略与格式 |
| 文档 Documentation | 内置手册与许可证 | 阅读本手册、查看 Apache 2.0 摘要 |
| 报表 Reports | 功能预留 | 未来用于历史告警与统计图表 |

推荐操作顺序：**设置 SMTP → 创建监控任务 → 启动监控 → 根据日志验证行为**。

---

## 3. 创建监控任务

### 3.1 通用字段

在“配置”页点击“新增”，右侧表单会显示以下字段：

- **名称 Name**：任意可读名称，用于日志、邮件主题和报表。
- **地址 URL**：完整的 HTTP/HTTPS 地址或主机名；SERVER 类型允许输入 `example.com:8443/status` 形态。
- **类型 Type**：从 `GET`、`POST`、`SERVER` 中选择。
- **周期 Interval**：单位为秒，表示调度器轮询间隔。
- **通知邮箱 Email**：可选。留空则使用全局 `[Mail].to_addrs`；支持逗号分隔多个地址。
- **Payload / Headers**：仅对 POST/自定义请求生效，支持 JSON 文本或 `key=value` 多行格式。

输入过程中系统会实时校验必填字段、URL 主机名、邮箱格式等，校验失败时会在“验证信息”区域给出中文提示。

### 3.2 GET 类型示例

- **使用场景**：检查 REST API、健康检查端点或 CDN 可达性。
- **配置示例**：
  - 名称：`商城 API`
  - URL：`https://api.example.com/health`
  - 类型：`GET`
  - 周期：`60`
  - Email：`ops@example.com, dev@example.com`
- **特点**：仅发送 GET 请求，成功状态码 200~399 视为健康；失败会触发异常日志与告警邮件。

### 3.3 POST 类型示例

- **使用场景**：调用需要携带 JSON payload 的服务（如心跳上报、Webhook）。
- **配置示例**：
  - URL：`https://hook.example.com/ping`
  - Payload：
    ```json
    {
      "service": "billing",
      "region": "cn-north-1"
    }
    ```
  - Headers：
    ```json
    {
      "Authorization": "Bearer <token>",
      "Content-Type": "application/json"
    }
    ```
- **注意**：Payload/Headers 会作为请求体与请求头原样发送，确保无敏感信息泄露。

### 3.4 SERVER 类型示例

- **使用场景**：监控服务器端口可用性、网络连通性与 HTTP 响应。
- **配置示例**：
  - URL：`ops.example.com:9443/status`
  - 程序会自动解析协议/主机/端口，并执行：
    1. TCP 端口连通性检查
    2. Ping/ICMP 探测（若系统允许）
    3. HTTP GET 请求（拼接为 `https://ops.example.com:9443/status`）
- **提示**：若部署在 Linux/macOS，记得授予进程使用原始 ICMP 的权限，或接受系统自动回退到 `ping` 命令。

### 3.5 保存与验证

1. 完成表单后，点击“保存”写入 `Config.ini`。
2. 若需要放弃当前编辑，可点击“恢复配置”重新加载磁盘内容。
3. 返回监控页面，点击“启动”即可让调度器读取最新配置并运行；实时日志会列出每个监控项的概况。

---

## 4. 使用场景参考

| 场景 | 推荐类型 | 配置要点 |
| --- | --- | --- |
| API 可用性验证 | GET | 使用 `/health`、`/status` 等轻量端点，周期 30~60 秒 |
| Webhook 连通性 | POST | 设定 JSON Payload，并在 Headers 中配置认证信息 |
| 内网主机巡检 | SERVER | 仅需主机:端口；系统会同时检查 socket、ping 与 HTTP |
| 对外站点监控 | GET/SERVER | 对静态站可用 GET，对多端口服务用 SERVER 并开启邮件通知 |

---

## 5. 邮箱与模板配置

### 5.1 SMTP 凭据

DataMonitor 在加载邮件配置时遵循以下优先级（缺一不可）：

1. **环境变量**（生产推荐）：在运行 DataMonitor 的用户或服务中设置：
   ```bash
   export MAIL_SMTP_SERVER=smtp.example.com
   export MAIL_SMTP_PORT=587
   export MAIL_USERNAME=alert@example.com
   export MAIL_PASSWORD='use-app-password-or-secret'
   export MAIL_FROM="DataMonitor <alert@example.com>"
   export MAIL_TO="ops@example.com,dev@example.com"
   ```
   适合 CI/CD 或容器注入机密的场景，可配合 secret 管理平台。
2. **外部配置文件**：若凭据需要持久化但不想写入仓库，可将以下内容保存到 `/etc/datamonitor/mail.ini`，并设置 `MAIL_CONFIG_PATH=/etc/datamonitor/mail.ini`：
   ```ini
   [Mail]
   smtp_server = smtp.internal.local
   smtp_port   = 465
   username    = infra@example.com
   password    = ${MAIL_PASSWORD}   ; 可借助 shell 变量展开
   from_addr   = "InfraBot <infra@example.com>"
   to_addrs    = SRE@example.com, oncall@example.com
   use_ssl     = true
   use_starttls = false
   ```
   建议使用 `chmod 600` 保护该文件：`sudo chmod 600 /etc/datamonitor/mail.ini`。
3. **本地 Config.ini**：用于快速演示或单机测试。当 ENV 与外部文件都未提供时，程序读取 `<APIMONITOR_HOME>/Config/Config.ini` 中的 `[Mail]` 段。仓库默认值是占位符（`<SMTP_SERVER>` 等），请务必改成真实参数，否则启动监控时会抛出 `ValueError`。

> **测试建议**：配置完成后，可临时创建一个间隔 5 秒的 GET 监控指向无效地址，观察故障/恢复邮件是否按期望送达，确认凭据与模板均正确。

### 5.2 每个监控项自定义收件人

- **界面配置**：在“配置”页的表单中填写“通知邮箱 Email”字段，支持多个地址（用逗号分隔）。示例：`db-oncall@example.com, dba@example.com`。
- **INI 配置**：在 `Config.ini` 的对应 `MonitorX` 段添加 `email = ops@example.com`。保存后点击“恢复配置”同步到界面。
- **覆盖策略**：若监控项提供 `email` 字段，则仅向该列表发信，不再使用全局 `[Mail].to_addrs`。适合按团队拆分告警。

### 5.3 邮件模板

模板文件位于 `<APIMONITOR_HOME>/Config/Templates.ini`，结构示例：

```ini
[mail]
alert_subject   = 故障告警 | {service_name}
alert_body      = 状态：{status_action}\n服务：{service_name}\n说明：{event_description}\n{time_label}：{event_timestamp}
recovery_subject = 故障恢复 | {service_name}
recovery_body    = 状态：{status_action}\n服务：{service_name}\n说明：{event_description}\n{time_label}：{event_timestamp}
```

- **可用占位符**：`{service_name}`、`{event_timestamp}`、`{status_action}`、`{event_description}`、`{time_label}`。这些字段由状态机自动填充。
- **自定义语言**：如需英文模板，可新增 `[mail[en_US]]` 段：
  ```ini
  [mail[en_US]]
  alert_subject = Outage Alert | {service_name}
  alert_body    = Status: {status_action}\nService: {service_name}\nDetails: {event_description}\n{time_label}: {event_timestamp}
  ```
  应用在切换语言时会优先使用匹配的段落。
- **修改流程**：
  1. 关闭或暂停监控，打开模板文件进行编辑。
  2. 保存后回到客户端，在配置页点击“恢复配置”或“重新加载配置”按钮。
  3. 重新启动监控确认邮件预览与实际内容一致。

### 5.4 邮件语言

- 默认为当前 UI 语言（“设置 > 语言”）。切换到英文界面后，程序会尝试读取 `[mail[en_US]]`；若不存在，则回退到 `[mail]`。
- 在多语言场景下建议同时维护 `[mail]`（对应默认语言）与 `[mail[en_US]]` 两套模板，以免提醒信息出现夹杂。
- 每次切换语言后，系统会自动刷新模板描述与主题下拉提示，无需额外操作。

---

## 6. 日志与排障

1. **日志目录**：默认位于 `<APIMONITOR_HOME>/Log/`。可在“设置 > 日志配置”里修改目录、文件名、最大大小与备份数。
2. **控制面板**：启用“控制台输出”后，日志会同步打印到终端，便于快速定位异常。
3. **常见问题**：
   - *监控没有启动？* 检查日志中是否提示 “未读取到有效的监控配置”；可能是 `Config.ini` 未保存或格式错误。
   - *邮件未发送？* 查看 `monitoring.send_email` 日志条目，确认 SMTP 凭据与端口配置正确。
   - *SERVER 探测一直失败？* 手动在终端执行 `ping host`、`curl host:port` 验证网络，再调整系统防火墙权限。

---

## 7. 常见问答

1. **如何在无 GUI 服务器上运行？** 可以只部署 `monitoring` 目录并运行相应脚本，但本手册针对桌面客户端。若需无界面运行，请参考 README 中的“Headless 部署”章节。
2. **可以一次性导入大量监控项吗？** 可以直接在 `Config.ini` 中编辑 `MonitorX` 节，随后在应用中点击“恢复配置”同步最新内容。
3. **是否支持英文邮件？** 支持，切换应用语言后模板会使用对应语言。也可以在 `Templates.ini` 中新增 `[mail[en_US]]` 段覆盖默认文本。

---

## 8. 反馈与支持

- **问题反馈**：在项目 Issue 区提交复现步骤、日志片段与配置摘要。
- **功能建议**：欢迎附带使用场景与期望行为，方便产品规划。
- **安全建议**：请勿在公共渠道分享真实 SMTP 凭据或生产日志，可通过私信/邮件联系维护者。

祝您使用顺利！
