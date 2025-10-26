#!/usr/bin/env python3
import os
import sys
import json
import argparse


def extract_step(step):
    name = step.get('name') if isinstance(step, dict) else None
    status = step.get('status') if isinstance(step, dict) else None
    substeps = []
    if isinstance(step, dict):
        children = step.get('steps') or []
        if isinstance(children, list):
            for c in children:
                if isinstance(c, dict):
                    substeps.append({'name': c.get('name'), 'status': c.get('status')})
    return {'name': name, 'status': status, 'substeps': substeps}


def process_file(path, results):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = json.load(f)
    except Exception as e:
        print(f"Skipping {os.path.basename(path)}: failed to read/parse JSON: {e}")
        return

    if not isinstance(content, dict):
        return

    tc = {}
    tc['testCaseId'] = content.get('testCaseId')
    tc['uuid'] = content.get('uuid')
    tc['name'] = content.get('name')
    tc['description'] = content.get('description')
    tc['status'] = content.get('status')

    sd = content.get('statusDetails') or {}
    tc['statusDetails'] = {
        'message': sd.get('message') if isinstance(sd, dict) else None,
        'trace': sd.get('trace') if isinstance(sd, dict) else None
    }

    tc_steps = []
    for s in content.get('steps') or []:
        tc_steps.append(extract_step(s))

    tc['steps'] = tc_steps

    results.append(tc)


def main():
    parser = argparse.ArgumentParser(description='Summarize Allure result JSON files into a single summary')
    parser.add_argument('results_dir', help='Path to allure-results directory')
    parser.add_argument('--output', '-o', help='Output filename (placed in results_dir)', default='allure-results-summary.json')
    args = parser.parse_args()

    results_dir = args.results_dir
    if not os.path.isdir(results_dir):
        print(f"Allure results directory not found: {results_dir}", file=sys.stderr)
        sys.exit(1)

    summary = []

    for name in os.listdir(results_dir):
        lower = name.lower()
        if lower.endswith('-result.json') or (lower.endswith('.json') and 'result' in lower):
            path = os.path.join(results_dir, name)
            if os.path.isfile(path):
                process_file(path, summary)

    out_path = os.path.join(results_dir, args.output)
    try:
        with open(out_path, 'w', encoding='utf-8') as out:
            json.dump(summary, out, indent=2, ensure_ascii=False)
        print(f"Wrote summary with {len(summary)} test case(s) to {out_path}")
    except Exception as e:
        print(f"Failed to write summary file {out_path}: {e}", file=sys.stderr)
        sys.exit(2)


if __name__ == '__main__':
    main()

