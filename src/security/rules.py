"""安全规则定义"""

# 高风险路径
RISKY_PATHS = [
    '/', '/boot', '/etc', '/usr', '/bin', '/sbin',
    '/lib', '/lib64', '/dev', '/proc', '/sys'
]

# 高风险命令模式
RISKY_COMMANDS = [
    'rm -rf /',
    'rm -rf /boot',
    'rm -rf /etc',
    'rm -rf /usr',
    'dd if=',
    'dd if=/dev/zero',
    'mkfs.',
    'fdisk',
    'chmod -R 777',
    'chmod 777 /',
    'chmod 777 /etc',
    '> /etc/passwd',
    '> /etc/shadow',
    '> /etc/sudoers',
    ':(){ :|:& };:',  # fork bomb
]

# 关键配置文件
CRITICAL_FILES = [
    '/etc/passwd',
    '/etc/shadow',
    '/etc/sudoers',
    '/etc/ssh/sshd_config',
    '/etc/fstab',
    '/boot/grub/grub.cfg',
    '/boot/grub2/grub.cfg',
]

# 系统用户（受保护，不能删除）
PROTECTED_USERS = [
    'root', 'daemon', 'bin', 'sys', 'sync', 'games', 'man',
    'lp', 'mail', 'news', 'uucp', 'proxy', 'www-data',
    'backup', 'list', 'irc', 'gnats', 'nobody', 'systemd-',
]

# 兼容旧导入名
SYSTEM_USERS = PROTECTED_USERS

# 非法用户名模式
ILLEGAL_USERNAMES = [
    'root', 'admin', 'administrator', 'sysadmin',
    'guest', 'anonymous', 'nobody',
    'test', 'demo', 'sample',
    'user', 'operator',
]

# 用户名/用户命令中的危险 Shell 片段
DANGEROUS_USER_TOKENS = [
    ';', '&&', '||', '|', '`', '$(', ')', '<', '>', '\n', '\r',
]

# 风险操作分类
RISK_OPERATIONS = {
    'high': [
        '删除系统目录',
        '删除系统文件',
        '格式化磁盘',
        '修改关键配置',
        '删除系统用户',
        '删除 root 用户',
    ],
    'medium': [
        '删除文件',
        '修改配置',
        '用户权限变更',
        '删除普通用户',
    ],
}
