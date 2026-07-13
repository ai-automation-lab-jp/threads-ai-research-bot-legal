#!/usr/bin/env python3
"""公開前チェックスクリプト（Threads AI副業リサーチBOT 公開情報サイト）。

Python標準ライブラリのみを使用する。外部ライブラリは追加しない。

使い方:
    python scripts/validate_site.py --draft
    python scripts/validate_site.py --release

--draft   : プレースホルダーは警告として扱う。その他の重大な問題は失敗とする。
--release : プレースホルダー・未設定の問い合わせ先/発効日/最終更新日/保持期間・
            秘密情報らしき文字列・内部リンク切れがあれば失敗とする。
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent

REQUIRED_FILES = [
    "index.html",
    "privacy.html",
    "data-deletion.html",
    "styles.css",
    "404.html",
    ".nojekyll",
    "README.md",
    "robots.txt",
    "scripts/validate_site.py",
]

HTML_FILES = ["index.html", "privacy.html", "data-deletion.html", "404.html"]

# 公開前に置換されるべきプレースホルダー
PLACEHOLDERS = [
    "CONTACT_EMAIL_REQUIRED",
    "EFFECTIVE_DATE_REQUIRED",
    "LAST_UPDATED_DATE_REQUIRED",
    "RETENTION_PERIOD_REQUIRED",
]

# 元資料の草案で使われていた全角ブラケット形式のプレースホルダーが
# 誤って残っていないかも検査する。
BRACKET_PLACEHOLDER_RE = re.compile(r"［[^］]*］")

SECRET_PATTERNS = [
    ("access_token_like", re.compile(r"\bTHREADS_ACCESS_TOKEN\b\s*[:=]\s*\S+")),
    ("bearer_token", re.compile(r"\bBearer\s+[A-Za-z0-9_\-\.]{10,}")),
    ("authorization_header", re.compile(r"\bAuthorization\s*:\s*\S+")),
    ("dotenv_reference", re.compile(r"\.env\b")),
    ("windows_user_path", re.compile(r"[A-Za-z]:\\Users\\[^\s\"'<>]+")),
    ("windows_user_path_fwd", re.compile(r"[A-Za-z]:/Users/[^\s\"'<>]+")),
    ("unix_home_path", re.compile(r"/home/[^\s\"'<>]+")),
    ("appdata_path", re.compile(r"AppData\\[^\s\"'<>]+")),
    ("generic_long_token", re.compile(r"\b[A-Za-z0-9_\-]{40,}\b")),
    ("app_secret_like", re.compile(r"\bAPP_SECRET\b\s*[:=]\s*\S+")),
]

# 実投稿データらしい記述の簡易検出（公開JSONの投稿本文引用等を想定）
RAW_DATA_PATTERNS = [
    ("raw_json_username_field", re.compile(r'"username"\s*:\s*"[^"]+"')),
    ("raw_json_access_token_field", re.compile(r'"access_token"\s*:\s*"[^"]+"')),
    ("raw_json_permalink_field", re.compile(r'"permalink"\s*:\s*"https?://[^"]+"')),
]

EXTERNAL_RESOURCE_CHECKS = [
    ("external_script", re.compile(r'<script[^>]+src\s*=\s*["\']https?://', re.I)),
    ("inline_script", re.compile(r"<script(?![^>]*type=[\"']application/ld\+json)[^>]*>\s*\S", re.I)),
    ("external_stylesheet", re.compile(r'<link[^>]+rel=["\']stylesheet["\'][^>]+href\s*=\s*["\']https?://', re.I)),
    ("external_font", re.compile(r"fonts\.googleapis\.com|fonts\.gstatic\.com", re.I)),
    ("cdn_reference", re.compile(r"cdn\.|jsdelivr\.net|unpkg\.com|cloudflare\.com", re.I)),
    ("analytics_reference", re.compile(r"google-analytics\.com|googletagmanager\.com|gtag\(|\bga\(", re.I)),
    ("ad_tag", re.compile(r"adsbygoogle|doubleclick\.net", re.I)),
    ("iframe_tag", re.compile(r"<iframe\b", re.I)),
    ("form_tag", re.compile(r"<form\b", re.I)),
    ("tracking_pixel", re.compile(r'<img[^>]+width=["\']?1["\']?[^>]+height=["\']?1["\']?', re.I)),
]

PRIVATE_REPO_LEAK_RE = re.compile(r"threads-ai-research-bot(?!-legal)")

CONTENT_LABEL_CHECKS = {
    "contact": (
        re.compile(r"問い合わせ|Contact", re.I),
        "問い合わせ先の記載",
    ),
    "effective_date": (
        re.compile(r"発効日|Effective date", re.I),
        "発効日の記載",
    ),
    "last_updated": (
        re.compile(r"最終更新日|Last updated", re.I),
        "最終更新日の記載",
    ),
    "retention": (
        re.compile(r"保持期間|Retention period", re.I),
        "保持期間の記載",
    ),
}


@dataclass
class Issue:
    file: str
    category: str
    line: int
    message: str
    hard: bool  # True: draft/releaseどちらでも失敗。False: draftでは警告のみ。


def line_of(text: str, index: int) -> int:
    return text.count("\n", 0, index) + 1


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def check_required_files() -> list[Issue]:
    issues: list[Issue] = []
    for rel in REQUIRED_FILES:
        p = ROOT / rel
        if not p.is_file():
            issues.append(
                Issue(rel, "missing_file", 0, f"必須ファイルが存在しません: {rel}", hard=True)
            )
    return issues


def check_html_structure(rel: str, text: str) -> list[Issue]:
    issues: list[Issue] = []

    def require(pattern: str, category: str, message: str, flags=re.I):
        m = re.search(pattern, text, flags)
        if not m:
            issues.append(Issue(rel, category, 0, message, hard=True))
        return m

    require(r"<html[^>]+lang\s*=\s*[\"'][a-z\-]+[\"']", "missing_lang", "html要素にlang属性がありません")
    require(r"<meta[^>]+charset\s*=\s*[\"']?utf-8", "missing_charset", "meta charsetがUTF-8で指定されていません")
    require(r'<meta[^>]+name\s*=\s*["\']viewport["\']', "missing_viewport", "viewportメタタグがありません")
    require(r"<title>[^<]+</title>", "missing_title", "titleタグがありません、または空です")
    require(r'<meta[^>]+name\s*=\s*["\']description["\']', "missing_description", "meta descriptionがありません")
    csp_m = require(
        r'<meta[^>]+http-equiv\s*=\s*["\']Content-Security-Policy["\'][^>]+content\s*=\s*(["\'])(.*?)\1',
        "missing_csp",
        "Content-Security-Policyのmetaタグがありません",
    )
    if csp_m:
        csp_value = csp_m.group(2)
        for directive in ["script-src 'none'", "object-src 'none'", "frame-src 'none'", "form-action 'none'"]:
            if directive not in csp_value:
                issues.append(
                    Issue(rel, "weak_csp", line_of(text, csp_m.start()),
                          f"CSPに推奨ディレクティブがありません: {directive}", hard=True)
                )

    if rel in ("index.html", "privacy.html", "data-deletion.html", "404.html"):
        if not re.search(r'id\s*=\s*["\']ja["\'][^>]*lang\s*=\s*["\']ja["\']|lang\s*=\s*["\']ja["\'][^>]*id\s*=\s*["\']ja["\']', text, re.I):
            issues.append(Issue(rel, "missing_ja_section", 0, "日本語セクション(lang=\"ja\")が見つかりません", hard=True))
        if not re.search(r'id\s*=\s*["\']en["\'][^>]*lang\s*=\s*["\']en["\']|lang\s*=\s*["\']en["\'][^>]*id\s*=\s*["\']en["\']', text, re.I):
            issues.append(Issue(rel, "missing_en_section", 0, "英語セクション(lang=\"en\")が見つかりません", hard=True))

    return issues


def check_skip_link(rel: str, text: str) -> list[Issue]:
    if 'class="skip-link"' not in text and "class='skip-link'" not in text:
        return [Issue(rel, "missing_skip_link", 0, "メインコンテンツへのスキップリンクが見つかりません", hard=True)]
    return []


def extract_internal_links(text: str) -> list[tuple[str, int]]:
    links = []
    for m in re.finditer(r'\b(?:href|src)\s*=\s*["\']([^"\']+)["\']', text, re.I):
        links.append((m.group(1), m.start()))
    return links


def check_links(rel: str, text: str) -> list[Issue]:
    issues: list[Issue] = []
    for href, pos in extract_internal_links(text):
        if href.startswith("#") or href.startswith("mailto:"):
            continue
        parsed = urlsplit(href)
        if parsed.scheme in ("http",):
            issues.append(
                Issue(rel, "insecure_external_link", line_of(text, pos),
                      f"http://の外部リンクが含まれています: {href}", hard=True)
            )
            continue
        if parsed.scheme in ("https",):
            issues.append(
                Issue(rel, "external_link", line_of(text, pos),
                      f"外部リンクが含まれています（要確認）: {href}", hard=False)
            )
            continue
        # 内部リンク（相対パス）
        target_path = href.split("#")[0].split("?")[0]
        if target_path == "":
            continue
        target = (ROOT / target_path).resolve()
        try:
            target.relative_to(ROOT.resolve())
        except ValueError:
            issues.append(
                Issue(rel, "link_outside_root", line_of(text, pos),
                      f"サイト外へのリンクの可能性があります: {href}", hard=True)
            )
            continue
        if not target.is_file():
            issues.append(
                Issue(rel, "broken_internal_link", line_of(text, pos),
                      f"内部リンク先が存在しません: {href}", hard=True)
            )
    return issues


def check_required_link_targets(rel: str, text: str) -> list[Issue]:
    issues: list[Issue] = []
    if rel == "index.html":
        if 'href="privacy.html"' not in text:
            issues.append(Issue(rel, "missing_privacy_link", 0, "プライバシーポリシーへのリンクがありません", hard=True))
        if 'href="data-deletion.html"' not in text:
            issues.append(Issue(rel, "missing_deletion_link", 0, "データ削除案内へのリンクがありません", hard=True))
    return issues


def check_content_labels(rel: str, text: str) -> list[Issue]:
    issues: list[Issue] = []
    if rel not in ("index.html", "privacy.html", "data-deletion.html"):
        return issues
    for key, (pattern, label) in CONTENT_LABEL_CHECKS.items():
        if key == "retention" and rel != "privacy.html":
            continue
        if key in ("contact",) and rel not in ("index.html", "privacy.html", "data-deletion.html"):
            continue
        if key in ("effective_date", "last_updated") and rel != "privacy.html" and rel != "index.html":
            continue
        if not pattern.search(text):
            issues.append(Issue(rel, f"missing_{key}_label", 0, f"{label}が見つかりません", hard=True))
    return issues


def check_placeholders(rel: str, text: str, mode: str) -> list[Issue]:
    issues: list[Issue] = []
    for placeholder in PLACEHOLDERS:
        for m in re.finditer(re.escape(placeholder), text):
            hard = mode == "release"
            issues.append(
                Issue(rel, "placeholder_remaining", line_of(text, m.start()),
                      f"未確定のプレースホルダーが残っています: {placeholder}", hard=hard)
            )
    for m in BRACKET_PLACEHOLDER_RE.finditer(text):
        hard = mode == "release"
        issues.append(
            Issue(rel, "draft_bracket_placeholder", line_of(text, m.start()),
                  f"草案由来と思われるブラケット表記が残っています: {m.group(0)}", hard=hard)
        )
    return issues


def check_secrets(rel: str, text: str) -> list[Issue]:
    issues: list[Issue] = []
    for name, pattern in SECRET_PATTERNS:
        for m in pattern.finditer(text):
            issues.append(
                Issue(rel, f"possible_secret:{name}", line_of(text, m.start()),
                      "秘密情報らしき文字列を検出しました（詳細は非表示）。該当箇所を確認し削除してください。",
                      hard=True)
            )
    for name, pattern in RAW_DATA_PATTERNS:
        for m in pattern.finditer(text):
            issues.append(
                Issue(rel, f"possible_raw_data:{name}", line_of(text, m.start()),
                      "実投稿データらしい記述を検出しました。サンプル・プレースホルダーに置き換えてください。",
                      hard=True)
            )
    if PRIVATE_REPO_LEAK_RE.search(text):
        m = PRIVATE_REPO_LEAK_RE.search(text)
        issues.append(
            Issue(rel, "private_repo_name_leak", line_of(text, m.start()),
                  "Private本体リポジトリ名らしき文字列が含まれています。公開サイトから削除してください。",
                  hard=True)
        )
    return issues


def check_external_resources(rel: str, text: str) -> list[Issue]:
    issues: list[Issue] = []
    for category, pattern in EXTERNAL_RESOURCE_CHECKS:
        m = pattern.search(text)
        if m:
            issues.append(
                Issue(rel, category, line_of(text, m.start()),
                      f"許可されていない外部リソース/構成要素の可能性: {category}", hard=True)
            )
    return issues


def check_external_stylesheets_and_scripts_root() -> list[Issue]:
    # styles.css自体が外部リソースを読み込んでいないか確認する
    issues: list[Issue] = []
    css_path = ROOT / "styles.css"
    if css_path.is_file():
        text = read(css_path)
        for m in re.finditer(r'url\(\s*["\']?(https?:)?//', text, re.I):
            issues.append(
                Issue("styles.css", "external_css_resource", line_of(text, m.start()),
                      "styles.cssが外部リソースを参照しています", hard=True)
            )
    return issues


def gather_html_issues(mode: str) -> list[Issue]:
    issues: list[Issue] = []
    for rel in HTML_FILES:
        path = ROOT / rel
        if not path.is_file():
            continue
        text = read(path)
        issues += check_html_structure(rel, text)
        issues += check_skip_link(rel, text)
        issues += check_links(rel, text)
        issues += check_required_link_targets(rel, text)
        issues += check_content_labels(rel, text)
        issues += check_placeholders(rel, text, mode)
        issues += check_secrets(rel, text)
        issues += check_external_resources(rel, text)
    issues += check_external_stylesheets_and_scripts_root()
    return issues


def suggest_fix(issue: Issue) -> str:
    fixes = {
        "missing_file": "指定パスに必須ファイルを作成してください。",
        "missing_lang": "<html lang=\"ja\"> のようにlang属性を追加してください。",
        "missing_charset": "<meta charset=\"UTF-8\"> を<head>内に追加してください。",
        "missing_viewport": "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\"> を追加してください。",
        "missing_title": "<title>ページ名</title> を<head>内に追加してください。",
        "missing_description": "<meta name=\"description\" content=\"...\"> を追加してください。",
        "missing_csp": "Content-Security-Policyのmetaタグを<head>内に追加してください。",
        "weak_csp": "CSPに不足しているディレクティブを追加してください。",
        "missing_ja_section": "id=\"ja\" lang=\"ja\" を持つセクションを追加してください。",
        "missing_en_section": "id=\"en\" lang=\"en\" を持つセクションを追加してください。",
        "missing_skip_link": "class=\"skip-link\"のスキップリンクを<body>直後に追加してください。",
        "broken_internal_link": "リンク先ファイルを作成するか、リンクを修正してください。",
        "link_outside_root": "サイトルート外へのリンクを削除・修正してください。",
        "insecure_external_link": "https://へ変更するか、外部リンク自体を削除してください。",
        "missing_privacy_link": "href=\"privacy.html\"のリンクを追加してください。",
        "missing_deletion_link": "href=\"data-deletion.html\"のリンクを追加してください。",
        "placeholder_remaining": "実際の公開情報に置き換えてください。",
        "draft_bracket_placeholder": "草案由来の表記を、確定した公開情報またはプレースホルダーに置き換えてください。",
        "private_repo_name_leak": "Private本体リポジトリを示す文字列を削除してください。",
        "external_link": "外部リンクが意図的か確認してください。不要なら削除してください。",
    }
    if issue.category.startswith("possible_secret") or issue.category.startswith("possible_raw_data"):
        return "該当箇所を確認し、秘密情報・実データを本サイトから完全に削除してください。"
    if issue.category in EXTERNAL_RESOURCE_CATEGORY_FIXES:
        return EXTERNAL_RESOURCE_CATEGORY_FIXES[issue.category]
    for key, label in CONTENT_LABEL_CHECKS.items():
        if issue.category == f"missing_{key}_label":
            return f"{label}をページ内に追加してください。"
    return fixes.get(issue.category, "内容を確認し、公開要件に沿って修正してください。")


EXTERNAL_RESOURCE_CATEGORY_FIXES = {
    "external_script": "外部scriptタグを削除してください。JavaScriptは使用しない方針です。",
    "inline_script": "インラインscriptを削除してください。JavaScriptは使用しない方針です。",
    "external_stylesheet": "外部stylesheetを削除し、styles.cssのみを使用してください。",
    "external_font": "外部フォント参照を削除し、システムフォントのみを使用してください。",
    "cdn_reference": "CDN参照を削除してください。",
    "analytics_reference": "アクセス解析コードを削除してください。",
    "ad_tag": "広告タグを削除してください。",
    "iframe_tag": "iframeタグを削除してください。",
    "form_tag": "formタグを削除してください（お問い合わせフォームは使用しない方針です）。",
    "tracking_pixel": "トラッキングピクセルらしき1x1画像を削除してください。",
    "external_css_resource": "styles.cssから外部URL参照を削除してください。",
}


def run(mode: str) -> int:
    issues: list[Issue] = []
    issues += check_required_files()
    issues += gather_html_issues(mode)

    hard_issues = [i for i in issues if i.hard]
    soft_issues = [i for i in issues if not i.hard]

    if soft_issues:
        print(f"[警告 warning] {len(soft_issues)} 件")
        for i in soft_issues:
            print(f"  - {i.file}:{i.line} [{i.category}] {i.message}")
            print(f"      修正案: {suggest_fix(i)}")

    if hard_issues:
        print(f"[失敗 fail] {len(hard_issues)} 件")
        for i in hard_issues:
            print(f"  - {i.file}:{i.line} [{i.category}] {i.message}")
            print(f"      修正案: {suggest_fix(i)}")

    print()
    print(f"モード: --{mode}")
    print(f"合計: 警告 {len(soft_issues)} 件 / 失敗 {len(hard_issues)} 件")

    if hard_issues:
        print("結果: FAIL")
        return 1

    print("結果: PASS")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="公開前チェックスクリプト")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--draft", action="store_true", help="ドラフト確認モード（プレースホルダーは警告扱い）")
    group.add_argument("--release", action="store_true", help="公開前確認モード（プレースホルダーは失敗扱い）")
    args = parser.parse_args()

    mode = "draft" if args.draft else "release"
    return run(mode)


if __name__ == "__main__":
    sys.exit(main())
