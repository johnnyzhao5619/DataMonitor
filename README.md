# DataMonitor TDS

## 界面预览与使用说明

![Teams 风格主界面](docs/ui_overview.svg)

1. 启动应用：在已准备好 `Config.ini` 的环境中执行 `python mainFrame.py`，默认进入监控视图，顶部导航采用 Teams 风格配色。
2. 监控视图：左侧显示本地时间，右侧显示 UTC 时间；下方实时日志滚动展示最新事件。
3. 配置向导：点击“配置 Configuration”按钮切换到配置视图，可在列表中增删监控项，右侧表单提供实时校验与通知邮件预览，保存后立即写入配置文件。
4. 时区调整：通过“时区 Time Zone”入口输入整数时区值，保存后时钟与日志状态会实时刷新。

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

### 监控项覆盖默认收件人

若某个监控项需要发送给不同的收件人，可在 `Config.ini` 中的对应 `MonitorX` 节点下填写 `email` 字段（支持以逗号分隔多个地址）。运行时程序会优先使用该字段，其次才回退到全局的 `[Mail].to_addrs` 配置。

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

### 邮件主题与正文示例

监控程序根据不同事件类型生成固定的邮件主题前缀，便于运维在收件箱中快速筛选：

- 服务异常告警：`Outage Alert | <服务名称>`
- 服务恢复通知：`Outage Recovery | <服务名称>`

邮件正文首行会明确标注事件状态，常见示例如下：

```
主题: Outage Alert | <服务名称>

状态：告警
服务：<服务名称>
说明：监控检测到服务不可达
发生时间：[UTC 时间戳]
```

```
主题: Outage Recovery | <服务名称>

状态：恢复
服务：<服务名称>
说明：监控检测到服务恢复至正常状态
恢复时间：[UTC 时间戳]
```

## 通知模版配置

为降低硬编码字符串的维护成本，程序在运行时会从配置目录（`<APIMONITOR_HOME>/Config/`）中加载 `Templates.ini`。若文件缺失，则自动回退到内置模版。

- **邮件模版 (`[mail]`)**：
  - `alert_subject` / `alert_body`：服务不可达时发送的邮件内容。
  - `recovery_subject` / `recovery_body`：服务恢复时发送的邮件内容。
- **UI 提示 (`[ui]`)**：
  - `status_line`：写入 GUI 队列与终端输出的统一提示文案。
- **日志模版 (`[log]`)**：
  - `action_line`：`logRecorder.record` 的 Action 行。
  - `detail_line`：记录状态明细的内容。
  - `record_entry`：文本日志整体格式。
  - `csv_header`：CSV 文件首行标题（以逗号分隔）。

所有模版均支持 Python `str.format` 占位符，常用字段包括：

- `{service_name}`：监控项名称。
- `{status_label}` / `{status_text}`：用于 UI 与 CSV 的状态描述。
- `{status_action}`、`{event_description}`、`{time_label}`：邮件正文中使用的语义化字段。
- `{event_timestamp}`：事件发生时间（已格式化）。
- `{interval}`、`{monitor_type}`、`{url}`：日志与表格所需的辅助信息。

一旦修改 `Templates.ini`，重启服务即可生效；如果模版缺失或缺少占位符，程序会提供明确错误信息并回退到安全状态，避免发送不完整的通知。

## 日志目录配置

日志文件及运行时生成的监控 CSV 会存放在“日志根目录”下。程序根据以下优先级确定该目录：

1. 环境变量 `APIMONITOR_HOME`（推荐）。
2. `config.ini` 或 `APIMonitor/Config/Config.ini` 中的 `[Logging].log_file` 配置项。
3. 仓库内默认路径 `APIMonitor/`。

无论采用何种方式，目录路径最终都会被归一化为绝对路径，并保证以分隔符结尾。例如：`/var/log/datamonitor/`。若配置为相对路径，则会基于对应配置文件所在目录解析。

### 生成配置模板

调用 `configuration.writeconfig(config_dir)` 会确保 `config_dir` 存在，并在 `config_dir/Config.ini` 中生成示例模板。模板仅包含占位符，运维需要手工覆盖为真实值或提供独立的外部配置文件。

## 安全建议

- 不要在版本库中提交真实凭证。
- 通过 CI/CD 将凭证注入环境变量或安全的密钥管理服务。
- 定期轮换邮箱密码，并在更新后同步环境变量或外部配置文件。
- 核查部署节点的日志与备份策略，避免凭证被意外写入日志或备份。

## 网络检测权限说明

- `monitor_server` 在检测网络连通性时会优先尝试原始 ICMP Ping。如需启用该功能，运行程序的账户必须具备管理员或 root 权限，否则程序会自动回退到系统 `ping` 命令或仅执行 HTTP 检查。
- 在缺少权限的环境中，无需额外配置即可继续使用 HTTP 检查结果，函数会返回布尔值而非抛出异常。

## 模块划分与扩展指南

### 调度与状态管理

- `monitoring/service.py` 实现调度层，负责读取 `configuration.read_monitor_list()` 返回的结构化监控项，按类型查找已注册的策略并以独立线程循环执行。调度层同时协调状态机、日志写入以及通知分发，使得 UI (`mainFrame.toolsetWindow`) 仅承担展示职责。
- `monitoring/state_machine.py` 提供 `MonitorStateMachine`，根据监控结果驱动状态切换并生成统一的 `MonitorEvent`。事件中包含状态描述、日志内容、CSV 行以及通知模版信息，便于在不同渠道重用。

### 策略注册

- 监控类型通过策略模式解耦，默认提供 `GET`、`POST`、`SERVER` 三种策略，均在 `MonitorScheduler` 初始化时注册。若需新增类型，可实现 `MonitorStrategy.run()` 并调用 `scheduler.register_strategy('NEW_TYPE', strategy)` 即可。

### 配置读取

- `configuration.read_monitor_list()` 现返回 `MonitorItem` 数据类，对 `name`、`url`、`type`、`interval` 等字段完成校验与规范化（类型大写、间隔转为正整数、可选 JSON/键值对解析）。业务层无需再做重复的类型转换或合法性检查。

### 单元测试

- 新增的 `tests/test_monitoring.py` 覆盖调度器和状态机的核心分支，验证状态迁移、通知生成、日志写入回调等行为。
- `tests/test_configuration.py` 增补对结构化配置读取与异常场景的测试，确保基础数据在进入调度层前即被校验。
