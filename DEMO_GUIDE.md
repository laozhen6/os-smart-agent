# os-smart-agent 演示操作文档

## 1. 项目说明

`os-smart-agent` 是一个基于自然语言的 Linux 运维代理，支持两种执行模式：

- `本地部署`：在当前 Linux 环境中执行命令
- `远程连接`：通过 SSH 在远程 Linux 主机执行命令

如果宿主机是 Windows，推荐使用 `WSL + Ubuntu` 作为本地运行环境。

---

## 2. 目录关系说明

如果项目在 Windows 路径：

```text
E:\WeChat\os-smart-agent
```

则在 WSL 中对应路径通常为：

```bash
/mnt/e/WeChat/os-smart-agent
```

说明：

- WSL 和 Windows 访问的是同一份文件
- 在 WSL 中修改文件，Windows 中会同步看到变化

---

## 3. 首次环境准备

### 3.1 进入 WSL

在 Windows PowerShell 中执行：

```powershell
wsl
```

### 3.2 进入项目目录

```bash
cd '/mnt/你的文件夹位置
若在E:\WeChat\os-smart-agent
则应输入
cd '/mnt/e/WeChat/os-smart-agent'
```

### 3.3 安装 Python 基础环境

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip
python3 --version
```

### 3.4 创建虚拟环境

```bash
python3 -m venv .venv_local
source .venv_local/bin/activate
```

激活成功后，终端前会出现：

```bash
(.venv_local)
```

### 3.5 安装依赖

```bash
pip install -r requirements.txt
```

---

## 4. 配置文件准备

项目使用 `config.yaml` 作为运行配置。

推荐保留一份通用配置，同时兼容本地模式和远程模式：

```yaml
api:
  base_url: "你的url"
  model: "你的model"
  api_key: "你的_SiliconFlow_API_Key"

execution:
  mode: "local"
  timeout: 300

  ssh:
    host: "你的远程主机IP"
    port: 22
    username: "你的SSH用户名"
    password: "你的SSH密码"

security:
  enable_secondary_confirmation: true
  max_command_timeout: 300
```

说明：

- `api_key`：模型接口密钥
- `mode`：虽然这里写了 `local`，但程序启动后仍会再次让用户选择模式
- `ssh`：远程模式使用，本地模式下会被忽略

---

## 5. 启动前检查

建议先执行：

```bash
python -m unittest tests.test_requirements -v
```

作用：

- 检查 `requirements.txt` 是否覆盖项目运行依赖
- 提前发现依赖缺失问题

---

## 6. 启动项目

执行：

```bash
python src/main.py --config config.yaml
```

程序启动后会提示：

```text
1. 本地部署
2. 远程连接
```

根据演示目标输入：

- 输入 `1`：本地部署
- 输入 `2`：远程连接

---

## 7. 本地部署演示流程

适用场景：

- 在 WSL/Ubuntu 中直接执行 Linux 命令
- 用于演示本地 Linux 环境下的运维能力

启动后输入：

```text
1
```

推荐演示命令：

```text
系统信息
查询当前磁盘使用情况
列出所有进程
查看 80 端口
查找 /var/log 下的 .log 文件
help
history
exit
```

---

## 8. 远程连接演示流程

适用场景：

- 通过 SSH 连接远程 Linux 服务器
- 用于演示远程运维代理能力

启动前建议先手动验证 SSH：

```bash
ssh 用户名@远程主机IP
```

确认 SSH 正常后，再启动程序并输入：

```text
2
```

推荐演示命令：

```text
系统信息
查询当前磁盘使用情况
列出所有进程
查看 80 端口
```

---

## 9. 每次重新运行的最短流程

```bash
wsl
cd '/mnt/e/WeChat/xwechat_files/wxid_pisu04f4x8jn22_8a81/msg/file/2026-04/os-smart-agent(1)'
source .venv_local/bin/activate
python src/main.py --config config.yaml
```

然后根据需要选择：

```text
1
```

或

```text
2
```

---

## 10. 退出方式

### 10.1 退出项目程序

在程序中输入：

```text
exit
```

### 10.2 退出 WSL

在 WSL 终端输入：

```bash
exit
```

或者按：

```text
Ctrl + D
```

### 10.3 关闭整个 WSL 实例

在 Windows PowerShell 中执行：

```powershell
wsl --shutdown
```

---

## 11. 常见问题排查

### 11.1 找不到虚拟环境

```bash
source .venv_local/bin/activate
```

如果报错，说明当前不在项目目录，先检查：

```bash
pwd
ls
```

### 11.2 缺少依赖

```bash
source .venv_local/bin/activate
pip install -r requirements.txt
```

### 11.3 远程模式无法连接

先手动测试：

```bash
ssh 用户名@远程主机IP
```

若失败，优先检查：

- 远程主机 IP 是否正确
- SSH 服务是否启动
- 用户名和密码是否正确
- 防火墙是否放行 22 端口

### 11.4 本地模式执行失败

说明当前运行环境不是 Linux。  
应确认程序是否是在 `WSL/Ubuntu` 中启动，而不是在 Windows 原生命令行中启动。

---

## 12. 演示建议

推荐按以下顺序演示：

1. 启动程序
2. 选择 `1. 本地部署`
3. 演示低风险查询命令
4. 退出程序
5. 重新启动程序
6. 选择 `2. 远程连接`
7. 演示远程 Linux 查询命令

这样可以清晰展示：

- 同一套程序支持两种模式
- 同一份 `config.yaml` 可以复用
- 自然语言请求能够转换为 Linux 运维操作
