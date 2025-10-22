# DataMonitor TDS

## 邮件配置与凭证管理

为避免将敏感凭证写入仓库，应用在加载邮件配置时遵循以下优先级：

1. **环境变量（推荐）**：直接在部署环境中设置以下变量，所有字段必须同时提供。
   - `MAIL_SMTP_SERVER`
   - `MAIL_SMTP_PORT`
   - `MAIL_USERNAME`
   - `MAIL_PASSWORD`
   - `MAIL_FROM`
   - `MAIL_TO`
2. **外部配置文件**：设置环境变量 `MAIL_CONFIG_PATH` 指向一份不纳入版本控制的 `ini` 文件。该文件需包含 `[Mail]` 节点，并提供上表中的全部字段。
3. **项目内默认模板**：仅当未提供上述配置时才会回退到仓库内的 `APIMonitor/Config/Config.ini`。仓库中提供的是占位示例值，部署前务必覆盖。

### 外部配置文件示例

```ini
[Mail]
smtp_server = mail.internal.example.com
smtp_port = 587
username = ops-team@example.com
password = ${MAIL_PASSWORD}
from_addr = ops-team@example.com
to_addrs = alerts@example.com
```

建议将凭证文件放置在仅运维可访问的目录，例如 `/etc/datamonitor/mail.ini`，并通过 `chmod 600` 限制权限：

```bash
export MAIL_CONFIG_PATH=/etc/datamonitor/mail.ini
chmod 600 /etc/datamonitor/mail.ini
```

### 缺失字段的处理方式

若环境变量或外部配置文件缺少任意字段，程序会抛出明确异常并停止发送邮件，以防使用不完整的配置。确保每次变更后执行冒烟测试，验证告警邮件功能正常。

### 生成配置模板

调用 `configuration.writeconfig` 会在 `APIMonitor/Config/Config.ini` 中生成示例模板。模板仅包含占位符，运维需要手工覆盖为真实值或提供独立的外部配置文件。

## 安全建议

- 不要在版本库中提交真实凭证。
- 通过 CI/CD 将凭证注入环境变量或安全的密钥管理服务。
- 定期轮换邮箱密码，并在更新后同步环境变量或外部配置文件。
- 核查部署节点的日志与备份策略，避免凭证被意外写入日志或备份。

## 配置 POST 监控

当监控项的 `type` 为 `POST` 时，可在 `APIMonitor/Config/Config.ini` 中为该任务增加可选字段：

- `payload`：请求体内容。若配置为 JSON 对象或数组（如 `{"message": "hello"}`），程序会以 `application/json` 方式发送；若填写普通字符串，则按原文作为请求体。
- `headers`：自定义请求头，需填写 JSON 对象，例如 `{"Content-Type": "application/json", "X-Token": "demo"}`。

示例配置如下：

```ini
[MonitorPostDemo]
name = HTTPBin POST Demo
url = https://httpbin.org/post
type = POST
interval = 60
email = ops-team@example.com
payload = {"message": "ping"}
headers = {"Content-Type": "application/json"}
```

保存配置后，可运行以下命令进行快速验证，确认示例任务能够成功发起 POST 请求：

```bash
python - <<'PY'
from apiMonitor import monitor_post

monitor_post("https://httpbin.org/post", {"message": "ping"}, {"Content-Type": "application/json"})
PY
```

终端应打印 `POST request to https://httpbin.org/post successful`，表示任务配置生效。
