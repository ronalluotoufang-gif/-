#!/usr/bin/env python3
"""Render a Sanyi Markdown review as a standalone offline HTML preview."""

from __future__ import annotations

import argparse
import datetime as dt
import html
import re
from pathlib import Path


BLOCK_START = re.compile(
    r"^(#{1,6})\s+|^>\s?|^[-*+]\s+|^\d+\.\s+|^```|^---+$|^\|"
)


def inline_markup(text: str) -> str:
    code_spans: list[str] = []

    def save_code(match: re.Match[str]) -> str:
        token = f"@@CODE{len(code_spans)}@@"
        code_spans.append(f"<code>{html.escape(match.group(1))}</code>")
        return token

    text = re.sub(r"`([^`\n]+)`", save_code, text)
    text = html.escape(text, quote=False)

    def link(match: re.Match[str]) -> str:
        label = match.group(1)
        url = html.escape(match.group(2), quote=True)
        attrs = ' target="_blank" rel="noopener noreferrer"' if url.startswith(("http://", "https://")) else ""
        return f'<a href="{url}"{attrs}>{label}</a>'

    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", link, text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"~~([^~]+)~~", r"<del>\1</del>", text)
    for index, code in enumerate(code_spans):
        text = text.replace(f"@@CODE{index}@@", code)
    return text


def split_table_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def is_table_separator(line: str) -> bool:
    cells = split_table_row(line)
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells)


def markdown_to_html(markdown: str) -> tuple[str, str]:
    lines = markdown.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    title = "三义漫剧评审"
    body: list[str] = []
    i = 0
    first_h1_skipped = False

    while i < len(lines):
        line = lines[i].rstrip()
        stripped = line.strip()

        if not stripped:
            i += 1
            continue

        heading = re.match(r"^(#{1,6})\s+(.+)$", stripped)
        if heading:
            level = len(heading.group(1))
            heading_text = heading.group(2).strip()
            if level == 1 and not first_h1_skipped:
                title = re.sub(r"[*_`]", "", heading_text)
                first_h1_skipped = True
            else:
                body.append(f"<h{level}>{inline_markup(heading_text)}</h{level}>")
            i += 1
            continue

        if stripped == "---":
            body.append("<hr>")
            i += 1
            continue

        if stripped.startswith("```"):
            language = stripped[3:].strip()
            code_lines: list[str] = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code_lines.append(lines[i])
                i += 1
            i += 1
            language_class = f' class="language-{html.escape(language)}"' if language else ""
            body.append(
                f"<pre><code{language_class}>{html.escape(chr(10).join(code_lines))}</code></pre>"
            )
            continue

        if stripped.startswith("|") and i + 1 < len(lines) and is_table_separator(lines[i + 1].strip()):
            headers = split_table_row(stripped)
            i += 2
            rows: list[list[str]] = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append(split_table_row(lines[i].strip()))
                i += 1
            table = ['<div class="table-wrap"><table><thead><tr>']
            table.extend(f"<th>{inline_markup(cell)}</th>" for cell in headers)
            table.append("</tr></thead><tbody>")
            for row in rows:
                padded = row + [""] * max(0, len(headers) - len(row))
                table.append("<tr>")
                table.extend(f"<td>{inline_markup(cell)}</td>" for cell in padded[: len(headers)])
                table.append("</tr>")
            table.append("</tbody></table></div>")
            body.append("".join(table))
            continue

        if stripped.startswith(">"):
            quote_lines: list[str] = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                quote_lines.append(re.sub(r"^>\s?", "", lines[i].strip()))
                i += 1
            body.append(f"<blockquote>{'<br>'.join(inline_markup(x) for x in quote_lines)}</blockquote>")
            continue

        list_match = re.match(r"^(\s*)([-*+]|\d+\.)\s+(.+)$", line)
        if list_match:
            list_type = "ol" if list_match.group(2)[0].isdigit() else "ul"
            items: list[str] = []
            base_indent = len(list_match.group(1))
            while i < len(lines):
                item_match = re.match(r"^(\s*)([-*+]|\d+\.)\s+(.+)$", lines[i].rstrip())
                if not item_match:
                    break
                current_type = "ol" if item_match.group(2)[0].isdigit() else "ul"
                if len(item_match.group(1)) != base_indent or current_type != list_type:
                    break
                items.append(f"<li>{inline_markup(item_match.group(3).strip())}</li>")
                i += 1
            body.append(f"<{list_type}>{''.join(items)}</{list_type}>")
            continue

        paragraph = [stripped]
        i += 1
        while i < len(lines):
            candidate = lines[i].rstrip()
            if not candidate.strip() or BLOCK_START.match(candidate.strip()):
                break
            paragraph.append(candidate.strip())
            i += 1
        body.append(f"<p>{inline_markup(' '.join(paragraph))}</p>")

    return title, "\n".join(body)


def make_document(title: str, body: str, source_name: str, score: str, rating: str) -> str:
    generated = dt.datetime.now().astimezone().strftime("%Y-%m-%d %H:%M")
    score_card = ""
    if score or rating:
        score_card = f"""
        <section class="score-card" aria-label="评审总览">
          <div><span>总分</span><strong>{html.escape(score or "—")}</strong></div>
          <div><span>评级</span><strong>{html.escape(rating or "—")}</strong></div>
          <div class="source"><span>内容母版</span><strong>{html.escape(source_name)}</strong></div>
        </section>"""

    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="color-scheme" content="light">
  <title>{html.escape(title)}</title>
  <style>
    :root {{
      --ink: #18221f;
      --muted: #65716d;
      --paper: #fffdf8;
      --canvas: #f2efe7;
      --line: #ded9cd;
      --brand: #a33a2b;
      --brand-dark: #72251d;
      --green: #1f5b4b;
      --green-soft: #e7f0ec;
      --gold: #b7832f;
      --shadow: 0 20px 60px rgba(49, 43, 32, .12);
    }}
    * {{ box-sizing: border-box; }}
    html {{ scroll-behavior: smooth; }}
    body {{
      margin: 0;
      color: var(--ink);
      background:
        radial-gradient(circle at 10% 0%, rgba(183, 131, 47, .12), transparent 28rem),
        var(--canvas);
      font-family: "PingFang SC", "Microsoft YaHei", "Noto Sans CJK SC", system-ui, sans-serif;
      line-height: 1.78;
    }}
    a {{ color: var(--brand-dark); text-decoration-thickness: 1px; text-underline-offset: 3px; }}
    .topbar {{
      position: sticky; top: 0; z-index: 20;
      display: flex; justify-content: space-between; align-items: center;
      padding: 10px clamp(18px, 4vw, 54px);
      background: rgba(24, 34, 31, .94); color: #fff;
      backdrop-filter: blur(14px);
    }}
    .brand {{ font-weight: 700; letter-spacing: .08em; }}
    .actions {{ display: flex; gap: 8px; }}
    button {{
      border: 1px solid rgba(255,255,255,.28); border-radius: 999px;
      background: transparent; color: #fff; padding: 7px 13px; cursor: pointer;
    }}
    .hero {{
      padding: clamp(34px, 7vw, 88px) clamp(18px, 6vw, 90px) 54px;
      color: #fff;
      background:
        linear-gradient(120deg, rgba(114,37,29,.96), rgba(24,34,31,.94)),
        #18221f;
    }}
    .eyebrow {{ margin: 0 0 12px; color: #f1c889; font-size: 13px; letter-spacing: .16em; }}
    h1 {{ max-width: 1100px; margin: 0; font-size: clamp(30px, 5vw, 64px); line-height: 1.18; }}
    .stamp {{ margin-top: 18px; color: rgba(255,255,255,.68); font-size: 13px; }}
    .shell {{
      display: grid; grid-template-columns: minmax(190px, 250px) minmax(0, 920px);
      gap: clamp(22px, 4vw, 54px); max-width: 1260px; margin: 0 auto;
      padding: 40px 22px 90px;
    }}
    aside {{ position: sticky; top: 72px; align-self: start; max-height: calc(100vh - 92px); overflow: auto; }}
    aside h2 {{ margin: 0 0 12px; font-size: 12px; letter-spacing: .16em; color: var(--muted); }}
    #toc a {{
      display: block; padding: 6px 10px; border-left: 2px solid var(--line);
      color: var(--muted); text-decoration: none; font-size: 13px; line-height: 1.45;
    }}
    #toc a.sub {{ padding-left: 22px; font-size: 12px; }}
    #toc a:hover {{ color: var(--brand); border-color: var(--brand); }}
    main {{
      min-width: 0; background: var(--paper); border: 1px solid var(--line);
      border-radius: 22px; box-shadow: var(--shadow); padding: clamp(24px, 5vw, 66px);
    }}
    .score-card {{
      display: grid; grid-template-columns: 1fr 1fr 2fr; gap: 1px;
      margin: 0 0 42px; overflow: hidden; border: 1px solid var(--line);
      border-radius: 16px; background: var(--line);
    }}
    .score-card div {{ background: #fff; padding: 19px 22px; }}
    .score-card span {{ display: block; color: var(--muted); font-size: 12px; letter-spacing: .1em; }}
    .score-card strong {{ display: block; margin-top: 3px; color: var(--brand); font-size: 28px; line-height: 1.2; }}
    .score-card .source strong {{ color: var(--ink); font-size: 14px; word-break: break-all; }}
    h2 {{
      margin: 62px 0 20px; padding-top: 12px; border-top: 3px solid var(--ink);
      font-size: clamp(24px, 3vw, 34px); line-height: 1.35;
    }}
    h2:first-of-type {{ margin-top: 18px; }}
    h3 {{ margin: 38px 0 14px; color: var(--brand-dark); font-size: 21px; line-height: 1.45; }}
    h4 {{ margin: 26px 0 10px; font-size: 17px; }}
    p {{ margin: 12px 0; }}
    ul, ol {{ padding-left: 1.45rem; }}
    li {{ margin: 7px 0; }}
    strong {{ color: #101714; }}
    code {{
      padding: .12em .42em; border-radius: 5px; background: #eee9df;
      color: var(--brand-dark); font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
      font-size: .91em;
    }}
    pre {{ overflow: auto; padding: 18px; border-radius: 12px; background: #17201d; color: #edf4f1; }}
    pre code {{ padding: 0; background: transparent; color: inherit; }}
    blockquote {{
      margin: 22px 0; padding: 18px 22px; border-left: 5px solid var(--gold);
      border-radius: 0 12px 12px 0; background: #faf3e5; color: #443b2f;
    }}
    .table-wrap {{ overflow-x: auto; margin: 22px 0 30px; border: 1px solid var(--line); border-radius: 12px; }}
    table {{ width: 100%; border-collapse: collapse; min-width: 620px; font-size: 14px; line-height: 1.55; }}
    th {{ background: var(--green); color: #fff; text-align: left; }}
    th, td {{ padding: 11px 13px; border-bottom: 1px solid var(--line); vertical-align: top; }}
    tr:nth-child(even) td {{ background: #faf8f2; }}
    tr:last-child td {{ border-bottom: 0; }}
    hr {{ border: 0; border-top: 1px solid var(--line); margin: 38px 0; }}
    @media (max-width: 840px) {{
      .shell {{ display: block; padding: 18px 10px 60px; }}
      aside {{ position: static; max-height: none; margin: 0 8px 20px; }}
      #toc {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); }}
      main {{ border-radius: 14px; padding: 22px 18px 44px; }}
      .score-card {{ grid-template-columns: 1fr 1fr; }}
      .score-card .source {{ grid-column: 1 / -1; }}
      .topbar {{ padding-inline: 14px; }}
    }}
    @media (max-width: 520px) {{
      #toc {{
        grid-template-columns: 1fr;
        max-height: 34vh;
        overflow-y: auto;
        border-bottom: 1px solid var(--line);
      }}
      #toc a.sub {{ padding-left: 20px; }}
      .hero {{ padding-top: 34px; padding-bottom: 34px; }}
    }}
    @media print {{
      body {{ background: #fff; }}
      .topbar, aside {{ display: none; }}
      .hero {{ padding: 28px 0; color: #000; background: #fff; border-bottom: 2px solid #000; }}
      .hero .eyebrow, .hero .stamp {{ color: #444; }}
      .shell {{ display: block; max-width: none; padding: 0; }}
      main {{ border: 0; box-shadow: none; padding: 20px 0; }}
      a {{ color: inherit; }}
      h2, h3 {{ break-after: avoid; }}
      table, blockquote {{ break-inside: avoid; }}
    }}
  </style>
</head>
<body>
  <nav class="topbar">
    <div class="brand">三义爆款漫剧专项</div>
    <div class="actions">
      <button type="button" onclick="window.print()">打印 / PDF</button>
      <button type="button" onclick="window.scrollTo({{top:0,behavior:'smooth'}})">回到顶部</button>
    </div>
  </nav>
  <header class="hero">
    <p class="eyebrow">SCRIPT REVIEW · HTML PREVIEW</p>
    <h1>{html.escape(title)}</h1>
    <p class="stamp">生成时间 {generated} · 离线单文件预览</p>
  </header>
  <div class="shell">
    <aside>
      <h2>内容目录</h2>
      <nav id="toc"></nav>
    </aside>
    <main>
      {score_card}
      {body}
    </main>
  </div>
  <script>
    (() => {{
      const toc = document.getElementById('toc');
      const headings = document.querySelectorAll('main h2, main h3');
      headings.forEach((heading, index) => {{
        heading.id = `section-${{index + 1}}`;
        const link = document.createElement('a');
        link.href = `#${{heading.id}}`;
        link.textContent = heading.textContent;
        if (heading.tagName === 'H3') link.className = 'sub';
        toc.appendChild(link);
      }});
    }})();
  </script>
</body>
</html>
"""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Markdown review")
    parser.add_argument("output", type=Path, nargs="?", help="HTML output; defaults to the same stem")
    args = parser.parse_args()

    source = args.input.resolve()
    output = (args.output or source.with_suffix(".html")).resolve()
    markdown = source.read_text(encoding="utf-8")
    title, body = markdown_to_html(markdown)
    score_match = re.search(r"总分[：:]\s*\**(\d+/100)\**", markdown)
    rating_match = re.search(r"综合评级[：:]\s*\**([SABCD])\**", markdown)
    document = make_document(
        title=title,
        body=body,
        source_name=source.name,
        score=score_match.group(1) if score_match else "",
        rating=rating_match.group(1) if rating_match else "",
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(document, encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
