#!/bin/bash
# 操作系统智能代理启动脚本

# 检查 Python 环境
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到 python3，请安装 Python 3.9+"
    exit 1
fi

# 检查 API Key
if [ -z "$SILICONFLOW_API_KEY" ]; then
    echo "警告: 未设置 SILICONFLOW_API_KEY 环境变量"
    echo "请设置环境变量: export SILICONFLOW_API_KEY=your_api_key_here"
    read -p "是否继续？(y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 运行代理
echo "正在启动操作系统智能代理..."
echo "使用配置: config.yaml"
echo "API 模型: $(grep 'model:' config.yaml | cut -d'"' -f2)"
echo "执行模式: $(grep 'mode:' config.yaml | cut -d' ' -f2)"

python3 src/main.py --config config.yaml

echo "代理已停止"