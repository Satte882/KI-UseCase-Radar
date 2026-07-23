from __future__ import annotations

import html
import re
from urllib.parse import urlparse

from django.utils.safestring import SafeString, mark_safe

FENCE_RE = re.compile(r"^```(?P<language>[\w+-]*)\s*$")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+)$")
LIST_RE = re.compile(r"^(?P<indent>\s*)(?P<marker>[*+-]|\d+\.)\s+(?P<text>.+)$")
TABLE_SEPARATOR_RE = re.compile(r"^\s*\|?\s*:?-{3,}:?\s*(?:\|\s*:?-{3,}:?\s*)+\|?\s*$")
LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
CODE_RE = re.compile(r"`([^`]+)`")
BOLD_RE = re.compile(r"\*\*([^*]+)\*\*")
ITALIC_RE = re.compile(r"(?<!\*)\*([^*]+)\*(?!\*)")


def _safe_link(match: re.Match[str]) -> str:
    label = html.escape(match.group(1), quote=False)
    url = match.group(2).strip()
    parsed = urlparse(url)
    if parsed.scheme and parsed.scheme not in {"http", "https", "mailto"}:
        return label
    escaped_url = html.escape(url, quote=True)
    return f'<a href="{escaped_url}" rel="noopener noreferrer">{label}</a>'


def _inline(value: str) -> str:
    placeholders: list[str] = []

    def protect_code(match: re.Match[str]) -> str:
        placeholders.append(f"<code>{html.escape(match.group(1))}</code>")
        return f"\x00{len(placeholders) - 1}\x00"

    rendered = CODE_RE.sub(protect_code, value)
    rendered = html.escape(rendered, quote=False)
    rendered = LINK_RE.sub(_safe_link, rendered)
    rendered = BOLD_RE.sub(r"<strong>\1</strong>", rendered)
    rendered = ITALIC_RE.sub(r"<em>\1</em>", rendered)
    for index, replacement in enumerate(placeholders):
        rendered = rendered.replace(html.escape(f"\x00{index}\x00"), replacement)
    return rendered


def _table_cells(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def _starts_block(lines: list[str], index: int) -> bool:
    line = lines[index]
    if not line.strip():
        return True
    if FENCE_RE.match(line) or HEADING_RE.match(line) or LIST_RE.match(line):
        return True
    if line.lstrip().startswith(">") or line.strip() in {"---", "***", "___"}:
        return True
    return index + 1 < len(lines) and "|" in line and TABLE_SEPARATOR_RE.match(lines[index + 1])


def render_markdown(source: str) -> SafeString:
    """Render the trusted, repository-owned methodology Markdown without a runtime dependency."""

    lines = source.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    output: list[str] = []
    index = 0

    while index < len(lines):
        line = lines[index]
        stripped = line.strip()
        if not stripped:
            index += 1
            continue

        fence = FENCE_RE.match(line)
        if fence:
            language = fence.group("language")
            code_lines: list[str] = []
            index += 1
            while index < len(lines) and not FENCE_RE.match(lines[index]):
                code_lines.append(lines[index])
                index += 1
            index += 1 if index < len(lines) else 0
            language_class = f' class="language-{html.escape(language)}"' if language else ""
            output.append(
                f"<pre><code{language_class}>{html.escape(chr(10).join(code_lines))}</code></pre>"
            )
            continue

        heading = HEADING_RE.match(line)
        if heading:
            level = len(heading.group(1))
            output.append(f"<h{level}>{_inline(heading.group(2).strip())}</h{level}>")
            index += 1
            continue

        if stripped in {"---", "***", "___"}:
            output.append("<hr>")
            index += 1
            continue

        if index + 1 < len(lines) and "|" in line and TABLE_SEPARATOR_RE.match(lines[index + 1]):
            headers = _table_cells(line)
            index += 2
            rows: list[list[str]] = []
            while index < len(lines) and lines[index].strip() and "|" in lines[index]:
                rows.append(_table_cells(lines[index]))
                index += 1
            head = "".join(f"<th scope=\"col\">{_inline(cell)}</th>" for cell in headers)
            body = "".join(
                "<tr>" + "".join(f"<td>{_inline(cell)}</td>" for cell in row) + "</tr>"
                for row in rows
            )
            output.append(
                '<div class="methodology-table-wrap"><table class="table methodology-table">'
                f"<thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>"
            )
            continue

        if line.lstrip().startswith(">"):
            quote_lines: list[str] = []
            while index < len(lines) and lines[index].lstrip().startswith(">"):
                quote_lines.append(lines[index].lstrip()[1:].strip())
                index += 1
            output.append(f"<blockquote>{_inline(' '.join(quote_lines))}</blockquote>")
            continue

        list_match = LIST_RE.match(line)
        if list_match:
            ordered = list_match.group("marker")[0].isdigit()
            tag = "ol" if ordered else "ul"
            items: list[str] = []
            while index < len(lines):
                item_match = LIST_RE.match(lines[index])
                if not item_match or item_match.group("marker")[0].isdigit() != ordered:
                    break
                indent = min(len(item_match.group("indent").replace("\t", "    ")) // 2, 4)
                items.append(
                    f'<li class="methodology-indent-{indent}">{_inline(item_match.group("text"))}</li>'
                )
                index += 1
            output.append(f"<{tag}>" + "".join(items) + f"</{tag}>")
            continue

        paragraph_lines = [stripped]
        index += 1
        while index < len(lines) and lines[index].strip() and not _starts_block(lines, index):
            paragraph_lines.append(lines[index].strip())
            index += 1
        output.append(f"<p>{_inline(' '.join(paragraph_lines))}</p>")

    return mark_safe("\n".join(output))  # noqa: S308 - source is trusted and escaped above
