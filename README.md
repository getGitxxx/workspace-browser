# Workspace File Browser

一个基于 Python 标准库实现的轻量级本地文件浏览器，提供目录浏览与代码文件在线预览能力。

默认运行后可通过浏览器访问：

- `http://localhost:18888`

## 功能特性

- 浏览工作区目录（目录优先，按名称排序）
- 过滤隐藏文件（以 `.` 开头的文件/目录）
- 文件列表前端搜索过滤
- 文件列表前端排序（名称/时间/类型）
- 文件预览面板（支持点击文件侧边预览）
- 文本类文件语法高亮（CodeMirror）
- 非文本文件回退为下载/原始响应

## 项目结构

```text
.
├── server.py    # 单文件 HTTP 服务与页面逻辑
└── README.md
```

## 运行要求

- Python 3.8+（建议 3.10+）
- 可访问外部 CDN（用于加载 CodeMirror 资源）

## 快速开始

1. 启动服务

```bash
python3 server.py
```

2. 打开浏览器访问

```text
http://localhost:18888
```

## 当前默认配置

`server.py` 中的关键常量：

- `PORT = 18888`
- `WORKSPACE = "/home/yuan/.openclaw/workspace"`

如果你要改端口或工作区目录，直接修改这两个常量即可。

## 支持预览的文本文件类型

`md`, `txt`, `py`, `js`, `ts`, `json`, `html`, `css`, `sh`, `yaml`, `yml`, `xml`, `log`, `cfg`, `conf`, `ini`

## 实现说明

- 服务框架：`http.server.HTTPServer + SimpleHTTPRequestHandler`
- 核心类：`WorkspaceBrowserHandler`
- 目录页面：`list_directory()`
- 文件页面：`preview_file()`

## 已知限制

- 工作区路径硬编码在代码中，不支持启动参数配置
- 页面样式与脚本内嵌在 Python 字符串中，维护成本较高
- 依赖公网 CDN；离线环境下语法高亮可能不可用
- 未提供鉴权，不适合直接暴露到公网

## 安全建议

- 仅在本机或受信任内网使用
- 如需远程访问，建议在反向代理层增加鉴权与访问控制
- 避免将敏感目录作为 `WORKSPACE`
