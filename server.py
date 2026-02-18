#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Workspace File Browser
Run: python3 server.py
Access: http://localhost:18888
"""

import os
import sys
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from datetime import datetime
from urllib.parse import unquote, parse_qs, urlparse

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

PORT = 18888
WORKSPACE = "/home/yuan/.openclaw/workspace"

class WorkspaceBrowserHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WORKSPACE, **kwargs)
    
    def translate_path(self, path):
        path = unquote(path, errors='surrogateescape')
        return super().translate_path(path)
    
    def do_GET(self):
        path = self.translate_path(self.path)
        
        # 文件预览
        if os.path.isfile(path):
            return self.preview_file(path)
        
        # 目录浏览
        if os.path.isdir(path):
            if not self.path.endswith('/'):
                self.send_response(301)
                self.send_header('Location', self.path + '/')
                self.end_headers()
                return
            return self.list_directory(path)
        
        return super().do_GET()
    
    def list_directory(self, path):
        try:
            # 解析排序参数
            parsed = urlparse(self.path)
            params = parse_qs(parsed.query)
            sort = params.get('sort', ['name'])[0]
            order = params.get('order', ['asc'])[0]
            
            entries = list(Path(path).iterdir())
            # 过滤隐藏文件
            entries = [e for e in entries if not e.name.startswith('.')]
            
            # 混合排序（目录在前或统一混合）
            reverse = order == 'desc'
            
            if sort == 'time':
                entries.sort(key=lambda x: x.stat().st_mtime, reverse=reverse)
            elif sort == 'type':
                entries.sort(key=lambda x: (not x.is_dir(), x.suffix.lower(), x.name.lower()))
            else:  # name
                entries.sort(key=lambda x: (not x.is_dir(), x.name.lower()), reverse=reverse)
            
            # 相对路径
            rel_path = os.path.relpath(path, WORKSPACE)
            if rel_path == '.':
                breadcrumb = '/'
                title = 'Workspace'
            else:
                breadcrumb = '/' + rel_path.replace(os.sep, '/') + '/'
                title = os.path.basename(path.rstrip('/'))
            
            # 面包屑
            breadcrumb_html = ''
            if rel_path != '.':
                parts = rel_path.split('/')
                cumulative = ''
                for part in parts:
                    cumulative += '/' + part
                    breadcrumb_html += f' / <a href="{cumulative}/">{part}</a>'
            
            # 文件列表
            files_html = ''
            
            # 父目录
            if path != WORKSPACE:
                parent = os.path.dirname(path)
                rel_parent = os.path.relpath(parent, WORKSPACE)
                parent_url = '/' + rel_parent.replace(os.sep, '/') + '/' if rel_parent != '.' else '/'
                files_html += f'''
                <li class="file-item" data-url="{parent_url}">
                    <span class="file-icon dir-icon">📂</span>
                    <span class="file-name"><a href="{parent_url}">..</a></span>
                    <span class="file-type">Parent</span>
                    <span class="file-modified">-</span>
                </li>
'''
            
            for entry in entries:
                name = entry.name
                url = '/' + os.path.relpath(entry, WORKSPACE).replace(os.sep, '/')
                if entry.is_dir():
                    url += '/'
                    icon = '📂'
                    icon_class = 'dir-icon'
                    ftype = 'Directory'
                else:
                    icon, icon_class = self.get_file_icon(name)
                    ftype = self.get_file_type(name)
                
                size = self.format_size(entry.stat().st_size) if entry.is_file() else '-'
                mtime = datetime.fromtimestamp(entry.stat().st_mtime).strftime('%Y-%m-%d %H:%M')
                
                files_html += f'''
                <li class="file-item" data-url="{url}">
                    <span class="file-icon {icon_class}">{icon}</span>
                    <span class="file-name">{name}</span>
                    <span class="file-type">{ftype}</span>
                    <span class="file-size">{size}</span>
                    <span class="file-modified">{mtime}</span>
                </li>
'''
            
            # 排序链接 - 更友好的展示
            sort_options = [('name', '名称'), ('time', '时间'), ('type', '类型')]
            sort_links = ''
            for s, label in sort_options:
                active = 'active' if s == sort else ''
                asc_url = f'{breadcrumb}?sort={s}&order=asc'
                desc_url = f'{breadcrumb}?sort={s}&order=desc'
                asc_active = 'active' if sort == s and order == 'asc' else ''
                desc_active = 'active' if sort == s and order == 'desc' else ''
                sort_links += f'''
                <div class="sort-group {active}">
                    <a href="{asc_url}" class="sort-btn {asc_active}" title="{label} ↑">↑</a>
                    <a href="{desc_url}" class="sort-btn {desc_active}" title="{label} ↓">↓</a>
                </div>
'''
            
            html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{title} - Workspace</title>
    <!-- CodeMirror -->
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/codemirror@5.65.16/lib/codemirror.min.css">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/codemirror@5.65.16/theme/dracula.css">
    <script src="https://cdn.jsdelivr.net/npm/codemirror@5.65.16/lib/codemirror.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/codemirror@5.65.16/mode/python/python.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/codemirror@5.65.16/mode/javascript/javascript.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/codemirror@5.65.16/mode/xml/xml.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/codemirror@5.65.16/mode/css/css.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/codemirror@5.65.16/mode/markdown/markdown.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/codemirror@5.65.16/mode/yaml/yaml.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/codemirror@5.65.16/mode/shell/shell.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/codemirror@5.65.16/mode/json/json.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/codemirror@5.65.16/mode/htmlmixed/htmlmixed.js"></script>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        html, body {{ height: 100%; overflow: hidden; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #1a1a2e; color: #eee; }}
        
        .container {{ display: flex; flex-direction: column; height: 100vh; }}
        
        /* 头部 */
        .header {{
            background: #16213e;
            padding: 10px 20px;
            border-bottom: 1px solid #0f3460;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}
        .header-left {{
            display: flex;
            align-items: center;
            gap: 15px;
        }}
        .header h1 {{ font-size: 16px; color: #00d9ff; }}
        .breadcrumb {{ font-size: 13px; color: #888; }}
        .breadcrumb a {{ color: #00d9ff; text-decoration: none; }}
        .breadcrumb a:hover {{ text-decoration: underline; }}
        .current-dir {{ color: #eee; font-weight: 500; }}
        
        /* 工具栏 */
        .toolbar {{
            background: #1a1a2e;
            padding: 6px 20px;
            border-bottom: 1px solid #0f3460;
            display: flex;
            align-items: center;
            gap: 5px;
        }}
        .toolbar span {{ color: #666; font-size: 12px; margin-right: 5px; }}
        .search-input {{
            background: #16213e;
            border: 1px solid #0f3460;
            color: #eee;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            width: 80px;
        }}
        .search-input:focus {{ outline: none; border-color: #00d9ff; width: 120px; }}
        .sort-group {{
            display: inline-flex;
            gap: 2px;
            margin-right: 10px;
        }}
        .sort-btn {{
            color: #555;
            text-decoration: none;
            font-size: 11px;
            padding: 3px 6px;
            border-radius: 3px;
            background: #16213e;
        }}
        .sort-btn:hover {{ color: #aaa; }}
        .sort-group.active .sort-btn {{ color: #00d9ff; }}
        .sort-btn.active {{ background: #0f3460; color: #00d9ff; }}
        
        /* 主内容 */
        .content {{
            flex: 1;
            display: flex;
            overflow: hidden;
        }}
        
        /* 分隔条 */
        .resizer {{
            width: 6px;
            background: #0f3460;
            cursor: col-resize;
            transition: background 0.2s;
            flex-shrink: 0;
        }}
        .resizer:hover, .resizer.dragging {{ background: #00d9ff; }}
        
        /* 文件列表 */
        .file-list {{
            flex: 1;
            overflow-y: auto;
            padding: 10px;
        }}
        .file-item {{
            display: flex;
            align-items: center;
            padding: 10px 15px;
            margin: 3px 0;
            background: #16213e;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.2s;
        }}
        .file-item:hover {{ background: #1f3460; }}
        .file-item.active {{ background: #0f3460; border-left: 3px solid #00d9ff; }}
        .file-icon {{ font-size: 20px; margin-right: 12px; width: 28px; text-align: center; }}
        .file-name {{ flex: 1; font-size: 14px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
        .file-type {{ color: #666; font-size: 11px; width: 80px; text-align: center; }}
        .file-size {{ color: #666; font-size: 11px; width: 70px; text-align: right; }}
        .file-modified {{ color: #666; font-size: 11px; width: 120px; text-align: right; }}
        .dir-icon {{ color: #ffc107; }}
        
        /* 预览区 */
        .preview {{
            width: 60%;
            border-left: 1px solid #0f3460;
            display: flex;
            flex-direction: column;
            background: #282a36;
        }}
        .preview-header {{
            padding: 10px 20px;
            background: #16213e;
            border-bottom: 1px solid #0f3460;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}
        .preview-header h2 {{ font-size: 14px; color: #50fa7b; }}
        .preview-close {{
            color: #666;
            cursor: pointer;
            font-size: 18px;
        }}
        .preview-close:hover {{ color: #ff5555; }}
        .preview-content {{ flex: 1; overflow: hidden; }}
        .preview-empty {{
            flex: 1;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #666;
            font-size: 14px;
        }}
        .CodeMirror {{ height: 100%; font-size: 13px; }}
        
        .file-icon-img {{ color: #4caf50; }}
        .file-icon-code {{ color: #2196f3; }}
        .file-icon-doc {{ color: #9c27b0; }}
        
        /* 空状态 */
        .empty {{ text-align: center; padding: 40px; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <!-- 头部 -->
        <div class="header">
            <div class="header-left">
                <h1>📁 Workspace</h1>
                <div class="breadcrumb">
                    <a href="/">Home</a>{breadcrumb_html}
                    <span class="current-dir">{title}</span>
                </div>
            </div>
        </div>
        
        <!-- 工具栏 -->
        <div class="toolbar">
            <input type="text" id="search" class="search-input" oninput="filterFiles()" placeholder>
            <span>排序:</span>
            {sort_links}
        </div>
        
        <!-- 主内容 -->
        <div class="content">
            <ul class="file-list">
                {files_html}
            </ul>
            
            <!-- 分隔条 -->
            <div class="resizer" id="resizer"></div>
            
            <!-- 预览区 -->
            <div class="preview" id="preview">
                <div class="preview-header">
                    <h2 id="preview-title">Preview</h2>
                    <span class="preview-close" onclick="closePreview()">✕</span>
                </div>
                <div class="preview-content">
                    <div class="preview-empty" id="preview-empty">
                        👆 Click a file to preview
                    </div>
                    <textarea id="code" style="display:none;"></textarea>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        // 文件预览
        let editor = null;
        
        document.querySelectorAll('.file-item').forEach(item => {{
            item.addEventListener('click', async (e) => {{
                // 如果点击的是链接(a标签)，让默认行为生效
                if (e.target.tagName === 'A') return;
                
                const url = item.dataset.url;
                if (!url) return;
                
                // 判断是目录还是文件
                if (url.endsWith('/')) {{
                    // 目录 - 跳转
                    window.location.href = url;
                    return;
                }}
                
                // 文件 - 预览
                const name = url.split('/').pop();
                
                // 高亮选中
                document.querySelectorAll('.file-item').forEach(i => i.classList.remove('active'));
                item.classList.add('active');
                
                document.getElementById('preview-title').textContent = '📄 ' + name;
                document.getElementById('preview-empty').style.display = 'none';
                document.getElementById('code').style.display = 'block';
                
                try {{
                    const response = await fetch(url);
                    const text = await response.text();
                    
                    const ext = name.split('.').pop().toLowerCase();
                    const textExts = ['md', 'txt', 'py', 'js', 'ts', 'json', 'html', 'css', 'sh', 'yaml', 'yml', 'xml', 'log', 'cfg', 'conf', 'ini'];
                    
                    if (textExts.includes(ext)) {{
                        const langMap = {{
                            'py': 'python', 'js': 'javascript', 'ts': 'typescript',
                            'json': 'json', 'html': 'htmlmixed', 'css': 'css',
                            'md': 'markdown', 'xml': 'xml', 'yaml': 'yaml',
                            'yml': 'yaml', 'sh': 'shell', 'ini': 'properties',
                            'cfg': 'properties', 'conf': 'properties',
                            'log': 'text', 'txt': 'text'
                        }};
                        
                        const mode = langMap[ext] || 'text';
                        
                        if (editor) {{
                            editor.toTextArea();
                        }}
                        
                        document.getElementById('code').value = text;
                        editor = CodeMirror.fromTextArea(document.getElementById('code'), {{
                            mode: mode,
                            theme: 'dracula',
                            lineNumbers: true,
                            readOnly: true,
                            viewportMargin: Infinity
                        }});
                    }} else {{
                        document.getElementById('preview-empty').innerHTML = 
                            'Preview not available<br><a href="' + url + '" style="color:#00d9ff">Download</a>';
                        document.getElementById('preview-empty').style.display = 'flex';
                        document.getElementById('code').style.display = 'none';
                    }}
                }} catch (err) {{
                    document.getElementById('preview-empty').textContent = 'Error: ' + err.message;
                    document.getElementById('preview-empty').style.display = 'flex';
                }}
            }});
        }});
        
        function closePreview() {{
            document.getElementById('preview').style.display = 'none';
            document.querySelector('.file-list').style.width = '100%';
        }}
        
        // 分隔条拖动
        const resizer = document.getElementById('resizer');
        const fileList = document.querySelector('.file-list');
        const preview = document.getElementById('preview');
        let isResizing = false;
        
        resizer.addEventListener('mousedown', (e) => {{
            isResizing = true;
            resizer.classList.add('dragging');
            document.body.style.cursor = 'col-resize';
            document.body.style.userSelect = 'none';
        }});
        
        document.addEventListener('mousemove', (e) => {{
            if (!isResizing) return;
            const containerWidth = document.querySelector('.content').offsetWidth;
            const newFileListWidth = e.clientX - document.querySelector('.content').getBoundingClientRect().left;
            if (newFileListWidth > 150 && newFileListWidth < containerWidth - 150) {{
                fileList.style.flex = 'none';
                fileList.style.width = newFileListWidth + 'px';
            }}
        }});
        
        document.addEventListener('mouseup', () => {{
            if (isResizing) {{
                isResizing = false;
                resizer.classList.remove('dragging');
                document.body.style.cursor = '';
                document.body.style.userSelect = '';
            }}
        }});
    </script>
</body>
</html>'''
            
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(html.encode())))
            self.end_headers()
            self.wfile.write(html.encode())
            
        except Exception as e:
            self.send_error(500, str(e))
    
    def preview_file(self, path):
        """直接预览文件"""
        import cgi
        ext = os.path.basename(path).rsplit('.', 1)[-1].lower() if '.' in path else ''
        text_extensions = {'md', 'txt', 'py', 'js', 'ts', 'json', 'html', 'css', 'sh', 'yaml', 'yml', 'xml', 'log', 'cfg', 'conf', 'ini'}
        
        lang_map = {
            'py': 'python', 'js': 'javascript', 'ts': 'typescript',
            'json': 'json', 'html': 'htmlmixed', 'css': 'css',
            'md': 'markdown', 'xml': 'xml', 'yaml': 'yaml',
            'yml': 'yaml', 'sh': 'shell', 'ini': 'properties',
            'cfg': 'properties', 'conf': 'properties',
            'log': 'text', 'txt': 'text',
        }
        lang = lang_map.get(ext, 'text')
        
        if ext in text_extensions:
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                content = content.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')
                
                filename = os.path.basename(path)
                dir_path = os.path.dirname(path)
                rel_dir = os.path.relpath(dir_path, WORKSPACE)
                back_url = '/' + rel_dir.replace(os.sep, '/') + '/' if rel_dir != '.' else '/'
                
                html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{filename}</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/codemirror@5.65.16/lib/codemirror.min.css">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/codemirror@5.65.16/theme/dracula.css">
    <script src="https://cdn.jsdelivr.net/npm/codemirror@5.65.16/lib/codemirror.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/codemirror@5.65.16/mode/{lang}/{lang}.js"></script>
    <style>
        body {{ margin: 0; background: #282a36; }}
        .header {{ background: #44475a; padding: 10px 20px; display: flex; align-items: center; justify-content: space-between; }}
        .header h1 {{ color: #50fa7b; font-size: 16px; }}
        .back-btn {{ color: #f8f8f2; text-decoration: none; padding: 6px 12px; background: #6272a4; border-radius: 4px; }}
        .back-btn:hover {{ background: #8be9fd; color: #282a36; }}
        .CodeMirror {{ height: calc(100vh - 50px); font-size: 14px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📄 {filename}</h1>
        <a href="{back_url}" class="back-btn">← Back</a>
    </div>
    <textarea id="code">{content}</textarea>
    <script>
        var editor = CodeMirror.fromTextArea(document.getElementById("code"), {{
            mode: "{lang}",
            theme: "dracula",
            lineNumbers: true,
            readOnly: true,
            viewportMargin: Infinity
        }});
        
        // 文件搜索过滤
        function filterFiles() {{
            const q = document.getElementById('search').value.toLowerCase();
            document.querySelectorAll('.file-item').forEach(item => {{
                const name = item.querySelector('.file-name').textContent.toLowerCase();
                item.style.display = name.includes(q) ? '' : 'none';
            }});
        }}
    </script>
</body>
</html>'''
                
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.send_header('Content-Length', str(len(html.encode('utf-8'))))
                self.end_headers()
                self.wfile.write(html.encode('utf-8'))
                
            except UnicodeDecodeError:
                return super().do_GET()
            except Exception as e:
                self.send_error(500, str(e))
        else:
            return super().do_GET()
    
    def format_size(self, size):
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"
    
    def get_file_type(self, name):
        ext = name.rsplit('.', 1)[-1].lower() if '.' in name else ''
        types = {
            'py': 'Python', 'js': 'JavaScript', 'ts': 'TypeScript',
            'json': 'JSON', 'html': 'HTML', 'css': 'CSS',
            'md': 'Markdown', 'xml': 'XML', 'yaml': 'YAML',
            'yml': 'YAML', 'sh': 'Shell', 'ini': 'Config',
            'cfg': 'Config', 'conf': 'Config', 'log': 'Log',
            'txt': 'Text', 'png': 'Image', 'jpg': 'Image',
            'jpeg': 'Image', 'gif': 'Image', 'svg': 'Image',
            'pdf': 'PDF', 'zip': 'Archive', 'tar': 'Archive',
        }
        return types.get(ext, ext.upper() if ext else 'File')
    
    def get_file_icon(self, name):
        ext = name.rsplit('.', 1)[-1].lower() if '.' in name else ''
        icons = {
            'py': ('🐍', 'file-icon-code'),
            'js': ('📜', 'file-icon-code'),
            'ts': ('📜', 'file-icon-code'),
            'md': ('📝', 'file-icon-doc'),
            'json': ('📋', 'file-icon-code'),
            'html': ('🌐', 'file-icon-code'),
            'css': ('🎨', 'file-icon-code'),
            'png': ('🖼️', 'file-icon-img'),
            'jpg': ('🖼️', 'file-icon-img'),
            'jpeg': ('🖼️', 'file-icon-img'),
            'gif': ('🖼️', 'file-icon-img'),
            'svg': ('🖼️', 'file-icon-img'),
            'pdf': ('📕', 'file-icon-doc'),
            'txt': ('📄', 'file-icon-doc'),
            'sh': ('⚡', 'file-icon-code'),
        }
        return icons.get(ext, ('📄', ''))

def main():
    os.chdir(WORKSPACE)
    server = HTTPServer(('0.0.0.0', PORT), WorkspaceBrowserHandler)
    print(f"🚀 Workspace Browser running at http://0.0.0.0:{PORT}")
    print(f"📁 Serving: {WORKSPACE}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Stopped")

if __name__ == '__main__':
    main()
