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

## 协议解析手工验证

更新后的服务监控会根据 URL 中的协议选择默认端口，并保持 HTTP/HTTPS 一致。可以按照以下步骤在本地进行一次端到端验证：

1. **启动 HTTP 测试服务**：
   ```bash
   python -m http.server 8000 --bind 127.0.0.1
   ```
   在监控配置中填入 `http://127.0.0.1:8000`，确认探测端口为 8000，浏览器或命令行可返回 200。
2. **启动 HTTPS 测试服务**：
   ```bash
   openssl req -x509 -nodes -days 1 -newkey rsa:2048 -keyout server.key -out server.crt -subj "/CN=localhost"
   openssl s_server -quiet -accept 8443 -cert server.crt -key server.key -www
   ```
   将监控地址设置为 `https://127.0.0.1:8443`，确认请求会自动使用 443 作为默认端口；若需访问非默认端口，继续使用显式端口号即可。
3. **查看日志输出**：监控面板与日志会同时打印协议、端口与访问 URL，确保 HTTP 与 HTTPS 场景均未出现协议错配。

完成后可删除临时生成的 `server.key` 和 `server.crt` 文件。
