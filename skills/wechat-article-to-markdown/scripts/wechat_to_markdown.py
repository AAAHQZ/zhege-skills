#!/usr/bin/env python3
"""
微信公众号文章转 Markdown 格式保存
用法: python wechat_to_markdown.py <ARTICLE_URL> [SAVE_DIR]
"""

import re, html, os, sys


def wechat_to_markdown(html_content):
    """将微信文章 HTML 转换为 Markdown，尽可能保留格式"""

    # 1. 提取标题
    t = re.search(r'<h1[^>]*>(.*?)</h1>', html_content, re.DOTALL)
    title = html.unescape(re.sub(r'<[^>]+>', '', t.group(1) if t else '')).strip()

    # 2. 提取文章主体
    m = re.search(r'class="rich_media_content[^"]*"[^>]*>(.*?)<p\s+style="display:\s*none;"', html_content, re.DOTALL)
    content = m.group(1) if m else ''

    # 3. 处理图片（必须先处理，避免标签嵌套问题）
    def replace_img(match):
        src = match.group(1) or ''
        alt_match = re.search(r'data-src="([^"]+)"', match.group(0))
        if alt_match:
            src = alt_match.group(1)
        if not src:
            return ''
        return f'\n![img]({src})\n'

    # 匹配 <p><img ...> 或 <img ...>，data-src 优先于 src
    content = re.sub(r'<p[^>]*>\s*<img[^>]+>\s*</p>', replace_img, content)
    content = re.sub(r'<img[^>]+data-src="([^"]+)"[^>]*>', replace_img, content)
    content = re.sub(r'<img[^>]+src="([^"]+)"[^>]*>', replace_img, content)

    # 4. 处理链接
    def replace_link(match):
        href = match.group(2) or ''
        text = match.group(1)
        if not href or not text:
            return text
        return f'[{text}]({href})'

    content = re.sub(r'<a[^>]+href="([^"]*)"[^>]*>(.*?)</a>', replace_link, content, flags=re.DOTALL)

    # 5. 处理加粗和斜体（先处理嵌套）
    def replace_strong(match):
        inner = match.group(1)
        inner = re.sub(r'<[^>]+>', '', inner)  # 去除内部标签
        return f'**{inner.strip()}**'

    def replace_em(match):
        inner = match.group(1)
        inner = re.sub(r'<[^>]+>', '', inner)
        return f'*{inner.strip()}*'

    content = re.sub(r'<strong[^>]*>(.*?)</strong>', replace_strong, content, flags=re.DOTALL)
    content = re.sub(r'<b[^>]*>(.*?)</b>', replace_strong, content, flags=re.DOTALL)
    content = re.sub(r'<em[^>]*>(.*?)</em>', replace_em, content, flags=re.DOTALL)
    content = re.sub(r'<i[^>]*>(.*?)</i>', replace_em, content, flags=re.DOTALL)

    # 6. 处理代码块（pre/code）
    def replace_pre(match):
        code = match.group(1)
        code = re.sub(r'<br\s*/?>', '\n', code)
        code = re.sub(r'<[^>]+>', '', code)
        code = html.unescape(code).strip()
        return f'\n```\n{code}\n```\n'

    content = re.sub(r'<pre[^>]*>(.*?)</pre>', replace_pre, content, flags=re.DOTALL)
    content = re.sub(r'<code[^>]*>(.*?)</code>', lambda m: f'`{m.group(1).strip()}`', content)

    # 7. 处理引用
    def replace_blockquote(match):
        inner = match.group(1)
        # 去掉 p 标签但保留换行
        inner = re.sub(r'<p[^>]*>', '', inner)
        inner = re.sub(r'</p>', '\n', inner)
        inner = re.sub(r'<br\s*/?>', '\n', inner)
        inner = re.sub(r'<[^>]+>', '', inner)
        inner = html.unescape(inner).strip()
        lines = [l.strip() for l in inner.split('\n') if l.strip()]
        if not lines:
            return ''
        return '\n' + '\n'.join(f'> {l}' for l in lines) + '\n'

    content = re.sub(r'<blockquote[^>]*>(.*?)</blockquote>', replace_blockquote, content, flags=re.DOTALL)

    # 8. 处理列表
    def replace_ul(match):
        items = re.findall(r'<li[^>]*>(.*?)</li>', match.group(1), re.DOTALL)
        result = []
        for item in items:
            item = re.sub(r'<br\s*/?>', '\n', item)
            item = re.sub(r'<[^>]+>', '', item)
            item = html.unescape(item).strip()
            if item:
                result.append(f'- {item}')
        return '\n' + '\n'.join(result) + '\n' if result else ''

    def replace_ol(match):
        items = re.findall(r'<li[^>]*>(.*?)</li>', match.group(1), re.DOTALL)
        result = []
        for i, item in enumerate(items, 1):
            item = re.sub(r'<br\s*/?>', '\n', item)
            item = re.sub(r'<[^>]+>', '', item)
            item = html.unescape(item).strip()
            if item:
                result.append(f'{i}. {item}')
        return '\n' + '\n'.join(result) + '\n' if result else ''

    content = re.sub(r'<ul[^>]*>(.*?)</ul>', replace_ul, content, flags=re.DOTALL)
    content = re.sub(r'<ol[^>]*>(.*?)</ol>', replace_ol, content, flags=re.DOTALL)

    # 9. 处理段落和换行
    content = re.sub(r'<p[^>]*>', '\n\n', content)
    content = re.sub(r'</p>', '', content)
    content = re.sub(r'<br\s*/?>', '\n', content)

    # 10. 处理 section 标题
    content = re.sub(r'<h[1-6][^>]*>(.*?)</h[1-6]>', lambda m: '\n' + '#' * int(m.group(0)[2]) + ' ' + re.sub(r'<[^>]+>', '', m.group(1)).strip() + '\n', content)

    # 11. 清理剩余标签并解码 HTML 实体
    content = re.sub(r'<[^>]+>', '', content)
    content = html.unescape(content)

    # 12. 清理多余空行
    lines = content.split('\n')
    result_lines = []
    prev_empty = False
    for line in lines:
        line = line.strip()
        is_empty = not line
        if is_empty:
            if not prev_empty:
                result_lines.append('')
            prev_empty = True
        else:
            result_lines.append(line)
            prev_empty = False
    content = '\n'.join(result_lines)

    # 去除开头多余换行
    content = content.lstrip('\n')
    # 保留结尾换行
    if content and not content.endswith('\n'):
        content += '\n'

    return title, content


def main():
    if len(sys.argv) < 2:
        print("用法: python wechat_to_markdown.py <ARTICLE_URL> [SAVE_DIR]")
        sys.exit(1)

    article_url = sys.argv[1]
    save_dir = sys.argv[2] if len(sys.argv) > 2 else "/mnt/d/MyLibrary"
    html_path = "/tmp/wechat_article.html"

    os.makedirs(save_dir, exist_ok=True)

    if not os.path.exists(html_path):
        print(f"错误: {html_path} 不存在，请先运行 curl 爬取 HTML")
        sys.exit(1)

    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()

    title, md_body = wechat_to_markdown(html_content)

    # 生成安全文件名
    safe_title = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9]', '', title)[:50]
    if not safe_title:
        safe_title = 'wechat_article'
    filepath = os.path.join(save_dir, f'{safe_title}.md')

    # 避免覆盖已有文件
    n = 2
    while os.path.exists(filepath):
        filepath = os.path.join(save_dir, f'{safe_title}_{n}.md')
        n += 1

    # 保存文件（顶部加原文链接）
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(f"> 原文链接：{article_url}\n\n# {title}\n\n{md_body}")

    print(f'已保存到: {filepath}')


if __name__ == "__main__":
    main()
