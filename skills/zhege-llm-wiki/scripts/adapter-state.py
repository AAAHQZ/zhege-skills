#!/usr/bin/env python3
"""外挂状态检测脚本：统一判断可选外挂的安装/环境/运行状态。

状态取值：not_installed / env_unavailable / runtime_failed / unsupported / empty_result
（另有 available 表示可用）

用法：
    python adapter-state.py [--skill-root <path>] check <source_id>
    python adapter-state.py [--skill-root <path>] summary
    python adapter-state.py [--skill-root <path>] summary-human
    python adapter-state.py [--skill-root <path>] classify-run <source_id> <exit_code> <output_path>

stdout 是 TSV：check / summary / classify-run 先打一行 8 列表头，再打状态行。
退出码：
    0  正常
    1  用法错误、未知来源、exit_code 非整数，或来源总表校验失败
"""

from __future__ import annotations

import pathlib
import shutil
import socket
import sys

if hasattr(sys.stdout, "reconfigure"):
    # Windows 控制台默认 GBK 且会把 \n 翻译成 \r\n；统一 UTF-8 + LF，
    # 保证 stdout 字节与 Linux/bash 原版一致（末列不会多出 \r）
    sys.stdout.reconfigure(encoding="utf-8", errors="replace", newline="\n")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace", newline="\n")

SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
# scripts/.. = skill 根；再取 dirname = skills/ 目录（bundled 依赖所在层）
DEFAULT_SKILL_ROOT = SCRIPT_DIR.parent.parent
REGISTRY_FILE = SCRIPT_DIR / "source-registry.tsv"

# 原 shared-config.sh 的唯一内容，已内联（该文件随移植删除）
WECHAT_TOOL_URL = "git+https://github.com/jackwener/wechat-article-to-markdown.git"

CHROME_DEBUG_HOST = "127.0.0.1"
CHROME_DEBUG_PORT = 9222
CHROME_DEBUG_TIMEOUT = 1

HEADER = [
    "source_id",
    "source_label",
    "state",
    "state_label",
    "detail",
    "recovery_action",
    "install_hint",
    "fallback_hint",
]

REGISTRY_HEADER = [
    "source_id",
    "source_label",
    "source_category",
    "input_mode",
    "match_rule",
    "raw_dir",
    "adapter_name",
    "dependency_name",
    "dependency_type",
    "fallback_hint",
]
VALID_CATEGORIES = ("core_builtin", "optional_adapter", "manual_only")
VALID_INPUT_MODES = ("url", "file", "text", "asset")

USAGE = """用法：
  python scripts/adapter-state.py [--skill-root <path>] check <source_id>
  python scripts/adapter-state.py [--skill-root <path>] summary
  python scripts/adapter-state.py [--skill-root <path>] summary-human
  python scripts/adapter-state.py [--skill-root <path>] classify-run <source_id> <exit_code> <output_path>
"""


def usage_exit() -> int:
    sys.stdout.write(USAGE)
    return 1


def field(row: list[str], index: int) -> str:
    """1 起始的 awk 风格取值。"""
    return row[index - 1] if len(row) >= index else ""


def read_rows() -> list[list[str]]:
    rows: list[list[str]] = []
    for line in REGISTRY_FILE.read_text(encoding="utf-8-sig").splitlines():
        if not line.strip():
            continue
        cells = line.split("\t")
        cells += [""] * (10 - len(cells))
        rows.append(cells)
    return rows


def validate_registry() -> list[list[str]]:
    """复刻 source-registry.sh validate 的总表校验（错误文案逐字一致）。"""
    if not REGISTRY_FILE.is_file():
        print(f"缺少文件：{REGISTRY_FILE}", file=sys.stderr)
        raise SystemExit(1)

    lines = REGISTRY_FILE.read_text(encoding="utf-8-sig").splitlines()
    if not lines or lines[0] != "\t".join(REGISTRY_HEADER):
        print(f"表头不匹配：{REGISTRY_FILE}", file=sys.stderr)
        print(f"期望：{'	'.join(REGISTRY_HEADER)}", file=sys.stderr)
        print(f"实际：{lines[0] if lines else ''}", file=sys.stderr)
        raise SystemExit(1)

    failed = False
    seen_ids: set[str] = set()
    category_seen: set[str] = set()

    for number, line in enumerate(lines[1:], start=2):
        if not line.strip():
            continue
        row = line.split("\t")
        row += [""] * (10 - len(row))
        source_id = field(row, 1)
        source_category = field(row, 3)
        input_mode = field(row, 4)
        match_rule = field(row, 5)
        raw_dir = field(row, 6)
        adapter_name = field(row, 7)
        dependency_name = field(row, 8)
        dependency_type = field(row, 9)

        if any(field(row, i) == "" for i in (1, 2, 3, 4, 5, 6, 10)):
            print(f"source-registry.tsv 第 {number} 行存在空字段", file=sys.stderr)
            failed = True
        if source_category not in VALID_CATEGORIES:
            print(f"source-registry.tsv 第 {number} 行存在未知分类：{source_category}", file=sys.stderr)
            failed = True
        if input_mode not in VALID_INPUT_MODES:
            print(f"source-registry.tsv 第 {number} 行存在未知输入模式：{input_mode}", file=sys.stderr)
            failed = True
        if input_mode == "url" and not match_rule.startswith("url_host:"):
            print(f"source-registry.tsv 第 {number} 行 URL 来源必须声明 url_host 规则：{match_rule}", file=sys.stderr)
            failed = True
        if input_mode == "file" and not match_rule.startswith("file_ext:"):
            print(f"source-registry.tsv 第 {number} 行文件来源必须声明 file_ext 规则：{match_rule}", file=sys.stderr)
            failed = True
        if input_mode == "text" and not match_rule.startswith("text:"):
            print(f"source-registry.tsv 第 {number} 行文本来源必须声明 text 规则：{match_rule}", file=sys.stderr)
            failed = True
        if input_mode == "asset" and not match_rule.startswith("asset:"):
            print(f"source-registry.tsv 第 {number} 行附件来源必须声明 asset 规则：{match_rule}", file=sys.stderr)
            failed = True
        if not raw_dir.startswith("raw/"):
            print(f"source-registry.tsv 第 {number} 行 raw_dir 必须位于 raw/ 下：{raw_dir}", file=sys.stderr)
            failed = True
        if source_id in seen_ids:
            print(f"source-registry.tsv source_id 重复：{source_id}", file=sys.stderr)
            failed = True
        seen_ids.add(source_id)
        category_seen.add(source_category)

        if source_category == "optional_adapter":
            if adapter_name == "-" or dependency_name == "-" or dependency_type == "none":
                print(f"source-registry.tsv 第 {number} 行 optional_adapter 缺少依赖信息", file=sys.stderr)
                failed = True
        elif adapter_name != "-" or dependency_name != "-" or dependency_type != "none":
            print(f"source-registry.tsv 第 {number} 行非外挂来源不应声明依赖", file=sys.stderr)
            failed = True

    for category in VALID_CATEGORIES:
        if category not in category_seen:
            print(f"source-registry.tsv 缺少 {category} 来源", file=sys.stderr)
            failed = True

    if failed:
        raise SystemExit(1)

    return read_rows()


def get_record(source_id: str) -> list[str]:
    for row in validate_registry():
        if field(row, 1) == source_id:
            return row
    print(f"未知来源：{source_id}", file=sys.stderr)
    raise SystemExit(1)


def has_uv() -> bool:
    return shutil.which("uv") is not None


def dependency_installed(dependency_name: str, dependency_type: str, skill_root: pathlib.Path) -> bool:
    if dependency_type == "bundled":
        return (skill_root / dependency_name).is_dir()
    if dependency_type == "install_time":
        return shutil.which(dependency_name) is not None
    if dependency_type == "none":
        return True
    return False


def chrome_debug_ready() -> bool:
    """原实现是 `lsof -i :9222 -sTCP:LISTEN`（Linux/macOS 专属）；改用 socket 直连，跨平台且无外部命令依赖。"""
    try:
        with socket.create_connection((CHROME_DEBUG_HOST, CHROME_DEBUG_PORT), timeout=CHROME_DEBUG_TIMEOUT):
            return True
    except OSError:
        return False


def state_label(state: str) -> str:
    return {
        "available": "可用",
        "not_installed": "未安装",
        "env_unavailable": "环境不满足",
        "runtime_failed": "运行失败",
        "unsupported": "不支持自动提取",
        "empty_result": "结果为空",
    }.get(state, state)


def default_install_hint(source_id: str, adapter_name: str) -> str:
    if source_id in ("web_article", "x_twitter", "zhihu_article", "youtube_video"):
        return f"重新运行当前平台的 llm-wiki 安装命令，确认 {adapter_name} 已准备到技能目录"
    if source_id == "wechat_article":
        return f"先安装 uv，再执行：uv tool install {WECHAT_TOOL_URL}"
    return "-"


def _chrome_debug_hint() -> str:
    """按当前平台给出带调试端口的 Chrome 启动命令。

    这段文案会直接显示给用户，必须是**他当前平台**能跑的那条命令——
    给 Windows 用户看 `open -na`（macOS 语法）会让他卡在这一步。
    """
    if sys.platform == "darwin":
        return 'open -na "Google Chrome" --args --remote-debugging-port=9222'
    if sys.platform == "win32":
        return (
            '& "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe" '
            "--remote-debugging-port=9222"
        )
    return "google-chrome --remote-debugging-port=9222"


def _uv_install_hint() -> str:
    """uv 的安装命令同样分平台。"""
    if sys.platform == "win32":
        return "先安装 uv：powershell -c \"irm https://astral.sh/uv/install.ps1 | iex\""
    if sys.platform == "darwin":
        return "先安装 uv：brew install uv"
    return "先安装 uv：curl -LsSf https://astral.sh/uv/install.sh | sh"


def env_install_hint(source_id: str) -> str:
    if source_id in ("web_article", "x_twitter", "zhihu_article"):
        return f"启动 Chrome 带调试端口：{_chrome_debug_hint()}"
    if source_id in ("wechat_article", "youtube_video"):
        return _uv_install_hint()
    return "-"


def emit_state_row(
    source_id: str,
    source_label: str,
    state: str,
    detail: str,
    recovery_action: str,
    install_hint: str,
    fallback_hint: str,
) -> None:
    row = [
        source_id,
        source_label,
        state,
        state_label(state),
        detail,
        recovery_action,
        install_hint,
        fallback_hint,
    ]
    sys.stdout.write("\t".join(row) + "\n")


def print_header() -> None:
    sys.stdout.write("\t".join(HEADER) + "\n")


def resolve_preflight_state(source_id: str, skill_root: pathlib.Path) -> tuple:
    """返回 (source_id, source_label, state, detail, recovery_action, install_hint, fallback_hint)"""
    record = get_record(source_id)
    source_id = field(record, 1)
    source_label = field(record, 2)
    source_category = field(record, 3)
    adapter_name = field(record, 7)
    dependency_name = field(record, 8)
    dependency_type = field(record, 9)
    fallback_hint = field(record, 10)

    if source_category == "core_builtin":
        state, detail, recovery_action, install_hint = (
            "available",
            "核心主线可直接进入，不依赖外挂",
            "直接继续主线",
            "-",
        )
    elif source_category == "manual_only":
        state, detail, recovery_action, install_hint = (
            "unsupported",
            "该来源当前只支持手动进入主线",
            "直接走手动入口",
            "-",
        )
    elif source_category == "optional_adapter":
        installed = dependency_installed(dependency_name, dependency_type, skill_root)

        if source_id == "wechat_article":
            if not has_uv():
                state, detail = "env_unavailable", "缺少 uv，当前无法准备微信公众号自动提取环境"
                install_hint = env_install_hint(source_id)
            elif not installed:
                state, detail = "not_installed", f"未找到 {adapter_name}"
                install_hint = default_install_hint(source_id, adapter_name)
            else:
                state, detail, install_hint = "available", f"{adapter_name} 已可用", "-"
        elif source_id in ("web_article", "x_twitter", "zhihu_article"):
            if not installed:
                state, detail = "not_installed", f"未找到 {adapter_name}"
                install_hint = default_install_hint(source_id, adapter_name)
            elif not chrome_debug_ready():
                state, detail = "env_unavailable", "Chrome 调试端口 9222 未监听"
                install_hint = env_install_hint(source_id)
            else:
                state, detail, install_hint = "available", f"{adapter_name} 已可用", "-"
        elif source_id == "youtube_video":
            if not installed:
                state, detail = "not_installed", f"未找到 {adapter_name}"
                install_hint = default_install_hint(source_id, adapter_name)
            elif not has_uv():
                state, detail = "env_unavailable", "缺少 uv，当前无法运行 YouTube 字幕提取"
                install_hint = env_install_hint(source_id)
            else:
                state, detail, install_hint = "available", f"{adapter_name} 已可用", "-"
        else:
            if not installed:
                state, detail = "not_installed", f"未找到 {adapter_name}"
                install_hint = default_install_hint(source_id, adapter_name)
            else:
                state, detail, install_hint = "available", f"{adapter_name} 已可用", "-"

        if state == "available":
            recovery_action = "继续自动提取"
        else:
            recovery_action = "先补安装；现在也可以直接走手动入口" if state == "not_installed" else "先补环境；现在也可以直接走手动入口"
    else:
        print(f"未知来源分类：{source_category}", file=sys.stderr)
        raise SystemExit(1)

    return (source_id, source_label, state, detail, recovery_action, install_hint, fallback_hint)


def print_state(state_tuple: tuple) -> None:
    emit_state_row(*state_tuple)


def collect_summary(skill_root: pathlib.Path) -> list[tuple]:
    states = []
    for row in validate_registry():
        if field(row, 3) in ("optional_adapter", "manual_only"):
            states.append(resolve_preflight_state(field(row, 1), skill_root))
    return states


def print_summary(skill_root: pathlib.Path) -> None:
    print_header()
    for state in collect_summary(skill_root):
        print_state(state)


def print_summary_human(skill_root: pathlib.Path) -> None:
    # state_tuple = (source_id, source_label, state, detail, recovery_action, install_hint, fallback_hint)
    for state_tuple in collect_summary(skill_root):
        source_label = state_tuple[1]
        detail = state_tuple[3]
        recovery_action = state_tuple[4]
        install_hint = state_tuple[5]
        fallback_hint = state_tuple[6]
        sys.stdout.write(f"- {source_label}：{state_label(state_tuple[2])}。{detail}。\n")
        sys.stdout.write(f"  下一步：{recovery_action}。\n")
        if install_hint != "-":
            sys.stdout.write(f"  安装提示：{install_hint}。\n")
        sys.stdout.write(f"  回退方式：{fallback_hint}。\n")


def output_has_content(output_path: str) -> bool:
    path = pathlib.Path(output_path)
    if not path.is_file():
        return False
    return bool(path.read_text(encoding="utf-8-sig", errors="replace").strip())


def classify_run_state(source_id: str, exit_code: int, output_path: str, skill_root: pathlib.Path) -> None:
    state_tuple = resolve_preflight_state(source_id, skill_root)
    source_label = state_tuple[1]
    state = state_tuple[2]
    fallback_hint = state_tuple[6]

    if state != "available":
        print_state(state_tuple)
        return

    if exit_code != 0:
        emit_state_row(
            source_id,
            source_label,
            "runtime_failed",
            "自动提取执行失败",
            "可以先重试一次；如果还不行，就改走手动入口",
            "-",
            fallback_hint,
        )
        return

    if not output_has_content(output_path):
        emit_state_row(
            source_id,
            source_label,
            "empty_result",
            "自动提取完成，但没有拿到有效正文",
            "请手动补全文本后继续主线",
            "-",
            fallback_hint,
        )
        return

    emit_state_row(
        source_id,
        source_label,
        "available",
        "自动提取已拿到有效正文",
        "继续进入主线",
        "-",
        fallback_hint,
    )


def main(argv: list[str]) -> int:
    skill_root = DEFAULT_SKILL_ROOT
    args = list(argv)

    while args:
        if args[0] == "--skill-root":
            if len(args) < 2:
                return usage_exit()
            skill_root = pathlib.Path(args[1])
            del args[0:2]
            continue
        break

    resolved_skill_root = skill_root
    if not args:
        return usage_exit()

    command = args[0]
    count = len(args)

    if command == "check":
        if count != 2:
            return usage_exit()
        print_header()
        print_state(resolve_preflight_state(args[1], resolved_skill_root))
    elif command == "summary":
        if count != 1:
            return usage_exit()
        print_summary(resolved_skill_root)
    elif command == "summary-human":
        if count != 1:
            return usage_exit()
        print_summary_human(resolved_skill_root)
    elif command == "classify-run":
        if count != 4:
            return usage_exit()
        raw_exit_code = args[2]
        if not raw_exit_code or any(ch not in "0123456789-" for ch in raw_exit_code):
            print(f"exit_code 必须是整数，收到：{raw_exit_code}", file=sys.stderr)
            raise SystemExit(1)
        print_header()
        classify_run_state(args[1], int(raw_exit_code), args[3], resolved_skill_root)
    else:
        return usage_exit()

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
