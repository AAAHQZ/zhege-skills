#!/usr/bin/env python3
"""
微信公众号文章转 Markdown 格式保存（本地图片版）
- 下载所有图片到本地，保留原文格式
- 生成的 Markdown 使用本地图片路径，永久可用
用法: python wechat_to_markdown.py <ARTICLE_URL> [SAVE_DIR]
"""

import re, html, os, sys, urllib.request, urllib.error, time
from urllib.parse import urlparse, unquote

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "image/webp,image/apng,image/*,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Referer": "https://mp.weixin.qq.com/",
}


def safe_filename(s: str, max_len: int = 50) -> str:
    """生成安全的文件名（保留中日韩文字）"""
    s = re.sub(r'[\\/:*?"<>|]', '', s)
    return s[:max_len] or 'wechat_article'


def download_image(img_url: str, save_dir: str, index: int, prefix: str = "", timeout: int = 15) -> str:
    """下载单张图片到本地，返回本地文件路径。失败时返回原 URL。"""
    if not img_url or img_url.startswith("data:"):
        return img_url

    # 跳过微信头像等小图（通常是 0×0 或极小尺寸占位图）
    if "wx_fmt=" in img_url:
        parsed = urlparse(img_url)
        qs = dict(p.split("=") for p in parsed.query.split("&") if "=" in p)
        if qs.get("w") and int(qs.get("w", "0")) < 100:
            return img_url

    # 从 URL 提取文件扩展名
    path_part = unquote(urlparse(img_url).path)
    ext = os.path.splitext(path_part)[1].lower()
    if ext not in (".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"):
        ext = ".jpg"

    # 生成文件名：[前缀_]image_001.jpg, [前缀_]image_002.png ...
    # 前缀为文章的安全文件名（如 "AI-Agent工程实践"），无前缀时直接 image_001.jpg
    if prefix:
        filename = f"{prefix}_image_{index:03d}{ext}"
    else:
        filename = f"image_{index:03d}{ext}"
    filepath = os.path.join(save_dir, filename)

    # 已下载过直接返回
    if os.path.exists(filepath):
        return filename

    try:
        req = urllib.request.Request(img_url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = resp.read()
        # 跳过极小图片（通常是占位符）
        if len(data) < 2000:
            return img_url
        with open(filepath, "wb") as f:
            f.write(data)
        return filename
    except Exception:
        return img_url  # 下载失败时降级为 URL 引用


def wechat_to_markdown(html_content: str, save_dir: str) -> tuple:
    """将微信文章 HTML 转换为 Markdown，图片下载到本地。"""

    # ── 1. 提取标题 ──────────────────────────────────────────────
    t = re.search(r'<h1[^>]*>(.*?)</h1>', html_content, re.DOTALL)
    raw_title = t.group(1) if t else ''
    title = html.unescape(re.sub(r'<[^>]+>', '', raw_title)).strip()
    if not title:
        t = re.search(r'var msg_title = "([^"]+)"', html_content)
        title = t.group(1) if t else 'wechat_article'

    # ── 2. 提取文章主体 ─────────────────────────────────────────
    m = re.search(r'class="rich_media_content[^"]*"[^>]*>(.*?)<p\s+style="display:\s*none;"',
                  html_content, re.DOTALL)
    content = m.group(1) if m else ''

    # ── 3. 收集所有图片 URL（data-src 优先）──────────────────────
    img_urls = []
    for match in re.finditer(r'<img[^>]+>', content):
        tag = match.group(0)
        src = ''
        # 优先 data-src（微信 CDN 真实地址）
        m2 = re.search(r'data-src="([^"]+)"', tag)
        if m2:
            src = m2.group(1)
        else:
            m2 = re.search(r'src="([^"]+)"', tag)
            if m2:
                src = m2.group(1)
        if src and src.startswith('http'):
            img_urls.append(src)

    # 生成文章名前缀（用于图片文件名）
    prefix = re.sub(r'[^a-zA-Z0-9\u4e00-\u9fa5]', '', title)

    # 下载图片到本地
    img_dir = save_dir
    local_map = {}  # url -> local_filename
    for i, url in enumerate(img_urls, 1):
        local_name = download_image(url, img_dir, i, prefix=prefix)
        local_map[url] = local_name
        # 避免请求过快
        time.sleep(0.3)

    # ── 4. 处理图片标签 → 本地引用 ───────────────────────────────
    def replace_img(match):
        tag = match.group(0)
        src = ''
        m2 = re.search(r'data-src="([^"]+)"', tag)
        if m2:
            src = m2.group(1)
        else:
            m2 = re.search(r'src="([^"]+)"', tag)
            if m2:
                src = m2.group(1)

        if src and src in local_map:
            local_name = local_map[src]
            if local_name != src:  # 下载成功
                return f'\n![img]({local_name})\n'
        # 降级：保留原始 URL
        if src:
            return f'\n![img]({src})\n'
        return ''

    # 匹配 <p><img ...></p> 和独立 <img ...>
    content = re.sub(r'<p[^>]*>\s*<img[^>]+>\s*</p>', replace_img, content)
    content = re.sub(r'<img[^>]+data-src="[^"]+"[^>]*>', replace_img, content)
    content = re.sub(r'<img[^>]+src="([^"]+)"[^>]*>', lambda m: f'\n![img]({m.group(1)})\n', content)

    # ── 5. 处理链接 ─────────────────────────────────────────────
    def replace_link(match):
        href = match.group(2) or ''
        text = match.group(1)
        if not href or not text:
            return text
        return f'[{text}]({href})'

    content = re.sub(
        r'<a[^>]+href="([^"]*)"[^>]*>(.*?)</a>',
        replace_link, content, flags=re.DOTALL
    )

    # ── 6. 加粗和斜体 ─────────────────────────────────────────────
    def replace_strong(match):
        inner = re.sub(r'<[^>]+>', '', match.group(1))
        return f'**{inner.strip()}**'

    def replace_em(match):
        inner = re.sub(r'<[^>]+>', '', match.group(1))
        return f'*{inner.strip()}*'

    content = re.sub(r'<strong[^>]*>(.*?)</strong>', replace_strong, content, flags=re.DOTALL)
    content = re.sub(r'<b[^>]*>(.*?)</b>', replace_strong, content, flags=re.DOTALL)
    content = re.sub(r'<em[^>]*>(.*?)</em>', replace_em, content, flags=re.DOTALL)
    content = re.sub(r'<i[^>]*>(.*?)</i>', replace_em, content, flags=re.DOTALL)

    # ── 7. 代码块 ────────────────────────────────────────────────
    def replace_pre(match):
        code = match.group(1)
        code = re.sub(r'<br\s*/?>', '\n', code)
        code = re.sub(r'<[^>]+>', '', code)
        code = html.unescape(code).strip()
        return f'\n```\n{code}\n```\n'

    content = re.sub(r'<pre[^>]*>(.*?)</pre>', replace_pre, content, flags=re.DOTALL)
    content = re.sub(r'<code[^>]*>(.*?)</code>',
                     lambda m: f'`{m.group(1).strip()}`', content)

    # ── 8. 引用块 ────────────────────────────────────────────────
    def replace_blockquote(match):
        inner = match.group(1)
        inner = re.sub(r'<p[^>]*>', '', inner)
        inner = re.sub(r'</p>', '\n', inner)
        inner = re.sub(r'<br\s*/?>', '\n', inner)
        inner = re.sub(r'<[^>]+>', '', inner)
        inner = html.unescape(inner).strip()
        lines = [l.strip() for l in inner.split('\n') if l.strip()]
        if not lines:
            return ''
        return '\n' + '\n'.join(f'> {l}' for l in lines) + '\n'

    content = re.sub(r'<blockquote[^>]*>(.*?)</blockquote>',
                     replace_blockquote, content, flags=re.DOTALL)

    # ── 9. 列表 ─────────────────────────────────────────────────
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

    # ── 10. 段落和换行 ───────────────────────────────────────────
    content = re.sub(r'<p[^>]*>', '\n\n', content)
    content = re.sub(r'</p>', '', content)
    content = re.sub(r'<br\s*/?>', '\n', content)

    # ── 11. 标题（h1-h6）─────────────────────────────────────────
    def replace_h(match):
        tag = match.group(0)
        level = int(tag[2])  # h1→1, h2→2, ...
        text = re.sub(r'<[^>]+>', '', match.group(1)).strip()
        return '\n' + '#' * level + ' ' + text + '\n'

    content = re.sub(r'<h[1-6][^>]*>(.*?)</h[1-6]>', replace_h, content, flags=re.DOTALL)

    # ── 12. 清理剩余标签 + HTML 实体 ────────────────────────────
    content = re.sub(r'<[^>]+>', '', content)
    content = html.unescape(content)

    # ── 13. 清理多余空行 ────────────────────────────────────────
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
    content = '\n'.join(result_lines).lstrip('\n')
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

    # 优先读取已下载的 HTML；若无则尝试直接抓取
    if not os.path.exists(html_path):
        print(f"[INFO] {html_path} 不存在，尝试直接抓取...")
        try:
            req = urllib.request.Request(
                article_url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Accept-Language": "zh-CN,zh;q=0.9",
                }
            )
            with urllib.request.urlopen(req, timeout=20) as resp:
                html_content = resp.read().decode('utf-8', errors='replace')
        except Exception as e:
            print(f"[ERROR] 无法抓取页面: {e}")
            sys.exit(1)
    else:
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()

    title, md_body = wechat_to_markdown(html_content, save_dir)

    # 生成 Markdown 文件路径
    sf = safe_filename(title)
    filepath = os.path.join(save_dir, f'{sf}.md')
    n = 2
    while os.path.exists(filepath):
        filepath = os.path.join(save_dir, f'{sf}_{n}.md')
        n += 1

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(f"> 原文链接：{article_url}\n\n# {title}\n\n{md_body}")

    print(f"[OK] 已保存：{filepath}")
    # 列出本地图集
    imgs = [f for f in os.listdir(save_dir)
            if f.startswith(f'{sf}_image_') and f.endswith(('.jpg','.png','.gif','.webp'))]
    if imgs:
        print(f"[OK] 图片已下载到本地 ({len(imgs)} 张): {save_dir}")


if __name__ == "__main__":
    main()
