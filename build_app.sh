#!/bin/bash

echo "=== 小铁皮 macOS App 打包工具 ==="
echo ""

# 检查 py2app
if ! pip show py2app > /dev/null 2>&1; then
    echo "安装 py2app..."
    pip install py2app
fi

# 清理旧构建
echo "清理旧构建..."
rm -rf build dist

# 打包
echo "开始打包..."
python setup.py py2app

if [ -d "dist/小铁皮.app" ]; then
    echo ""
    echo "✅ 打包成功！"
    echo ""
    echo "App 位置: dist/小铁皮.app"
    echo ""
    echo "你可以："
    echo "  1. 双击 dist/小铁皮.app 启动"
    echo "  2. 拖到 Applications 文件夹"
    echo "  3. 拖到 Dock 栏"
    echo ""
    echo "首次运行请右键 → 设置 API Key"
else
    echo ""
    echo "❌ 打包失败，请检查错误信息"
fi
