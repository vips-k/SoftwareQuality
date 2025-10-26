#!/usr/bin/env python3
import os
import sys
import json
import argparse

"""
Standalone helper: generate a Mermaid HTML flow for parent (business) steps in Allure result JSONs
and attach the HTML beside the JSON and add a text/html attachment entry to the JSON.
This does not modify any existing script logic.
"""


def _esc_html(s):
    if s is None:
        return ''
    s = str(s)
    return (s.replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;')
            .replace("'", '&#39;'))


def find_parents(steps):
    parents = []
    current = None
    for step in steps or []:
        name = ''
        try:
            name = str(step.get('name', '') or '')
        except Exception:
            name = ''
        if name.lower().startswith('* business step'):
            prefix = '* business step'
            remainder = name[len(prefix):].strip()
            remainder = remainder.strip('\'"')
            parent = {'name': remainder, 'status': step.get('status', 'unknown')}
            parents.append(parent)
            current = parent
        else:
            # child step - if it has a status that should influence parent but we rely on existing status
            continue
    return parents


def build_mermaid_html(parents):
    if not parents:
        return None
    nodes = []
    for i, p in enumerate(parents):
        name = _esc_html(p.get('name', '') or '')
        status = _esc_html(p.get('status', '') or 'unknown')
        label = f"{name} - {status}"
        node_id = f"step{i}"
        nodes.append((node_id, label, status.lower()))

    parts = []
    parts.append('<!doctype html>')
    parts.append('<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">')
    parts.append('<script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>')
    parts.append('<style>body{font-family: Arial, Helvetica, sans-serif; padding: 12px;} .mermaid{max-width:100%;}</style>')
    parts.append('<script>mermaid.initialize({startOnLoad:true});</script>')
    parts.append('</head><body>')
    parts.append('<h3>Business Steps Flow</h3>')
    parts.append('<div class="mermaid">')
    parts.append('graph LR')
    for nid, lbl, st in nodes:
        parts.append(f'{nid}["{lbl}"]')
    # connections
    conn = ' --> '.join(n[0] for n in nodes)
    parts.append(conn)
    # styles
    parts.append('classDef passed fill:#e6ffed,stroke:#34a853;')
    parts.append('classDef failed fill:#ffecec,stroke:#d93025;')
    parts.append('classDef broken fill:#fff4e5,stroke:#fbbc04;')
    parts.append('classDef skipped fill:#f0f0f0,stroke:#9aa0a6;')
    parts.append('classDef unknown fill:#ffffff,stroke:#000000;')
    for nid, lbl, st in nodes:
        sk = st if st in ('passed', 'failed', 'broken', 'skipped') else 'unknown'
        parts.append(f'class {nid} {sk}')
    parts.append('</div></body></html>')
    return '\n'.join(parts)


def process_file(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = json.load(f)
    except Exception as e:
        print(f"Skipping {os.path.basename(path)}: cannot read/parse JSON: {e}")
        return

    steps = content.get('steps') if isinstance(content, dict) else None
    if not steps:
        return

    parents = find_parents(steps)
    if not parents:
        return

    html = build_mermaid_html(parents)
    if not html:
        return

    base_name = os.path.splitext(os.path.basename(path))[0]
    html_name = f"{base_name}-business-steps.html"
    html_path = os.path.join(os.path.dirname(path), html_name)
    try:
        with open(html_path, 'w', encoding='utf-8') as hf:
            hf.write(html)
    except Exception as e:
        print(f"Failed to write HTML for {os.path.basename(path)}: {e}")
        return

    # update attachments
    try:
        attachments = content.get('attachments') if isinstance(content, dict) else None
        if attachments is None:
            attachments = []
        # remove existing entry for same source
        attachments = [a for a in attachments if not (isinstance(a, dict) and a.get('source') == html_name)]
        attachments.append({'name': 'Business Steps Flow', 'source': html_name, 'type': 'text/html'})
        content['attachments'] = attachments
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(content, f, separators=(',', ':'), ensure_ascii=False)
        print(f"Attached HTML to {os.path.basename(path)} -> {html_name}")
    except Exception as e:
        print(f"Failed to update JSON attachments for {os.path.basename(path)}: {e}")


def main():
    parser = argparse.ArgumentParser(description='Add Mermaid HTML attachment for business steps in Allure results')
    parser.add_argument('results_dir', help='Path to allure-results directory')
    args = parser.parse_args()

    results_dir = args.results_dir
    if not os.path.isdir(results_dir):
        print(f"Allure results directory not found: {results_dir}", file=sys.stderr)
        sys.exit(0)

    for name in os.listdir(results_dir):
        if name.lower().endswith('-result.json') or (name.lower().endswith('.json') and 'result' in name.lower()):
            path = os.path.join(results_dir, name)
            if os.path.isfile(path):
                process_file(path)


if __name__ == '__main__':
    main()

