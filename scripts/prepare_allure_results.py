#!/usr/bin/env python3
import os
import sys
import json
import re
import argparse


def compute_aggregated_status(child_steps):
    if not child_steps:
        return None
    priority = ['failed', 'broken', 'skipped', 'passed', 'unknown']
    child_statuses = []
    for s in child_steps:
        st = ''
        try:
            st = str(s.get('status', '') or '').lower()
        except Exception:
            st = ''
        child_statuses.append(st)
    for p in priority:
        if any(cs == p for cs in child_statuses):
            return p
    for cs in child_statuses:
        if cs:
            return cs
    return None


def _safe_int(value):
    try:
        if value is None:
            return None
        # handle strings and floats
        if isinstance(value, str):
            value = value.strip()
            if value == '':
                return None
        return int(float(value))
    except Exception:
        return None


def process_file(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = json.load(f)
    except Exception as e:
        print(f"Skipping {os.path.basename(path)}: failed to read/parse JSON: {e}")
        return

    if not isinstance(content, dict) or 'steps' not in content:
        # nothing to change
        return

    orig_steps = content.get('steps', []) or []
    new_steps = []
    current_parent = None

    for step in orig_steps:
        name = ''
        try:
            name = str(step.get('name', '') or '').strip()
        except Exception:
            name = ''

        if name.lower().startswith('* business step'):
            parent = dict(step) if isinstance(step, dict) else {}
            prefix = '* business step'
            remainder = name[len(prefix):].strip()
            # remove surrounding single or double quotes (use strip for simplicity and safety)
            remainder = remainder.strip('\'"')
            parent['name'] = remainder
            parent['steps'] = []
            new_steps.append(parent)
            current_parent = parent
        else:
            if current_parent is not None:
                current_parent['steps'].append(step)
            else:
                new_steps.append(step)

    content['steps'] = new_steps

    # compute aggregated statuses for parent steps and compute start/stop timestamps
    for candidate in new_steps:
        if isinstance(candidate, dict) and isinstance(candidate.get('steps'), list) and len(candidate.get('steps')) > 0:
            agg = compute_aggregated_status(candidate.get('steps'))
            if agg:
                candidate['status'] = agg

            # compute parent start as earliest child start and parent stop as latest executed child stop
            child_starts = []
            child_stops = []
            for s in candidate.get('steps'):
                # collect any numeric start timestamps
                st = _safe_int(s.get('start'))
                if st is not None:
                    child_starts.append(st)

                # consider stop timestamps only for executed children (skip if status is 'skipped')
                status = ''
                try:
                    status = str(s.get('status', '') or '').lower()
                except Exception:
                    status = ''
                sp = _safe_int(s.get('stop'))
                if sp is not None and status != 'skipped':
                    child_stops.append(sp)

            if child_starts:
                candidate['start'] = min(child_starts)
            # if no executed child stops found, fall back to any stop available
            if child_stops:
                candidate['stop'] = max(child_stops)
            else:
                # fallback: use any stop values if present
                any_stops = []
                for s in candidate.get('steps'):
                    sp = _safe_int(s.get('stop'))
                    if sp is not None:
                        any_stops.append(sp)
                if any_stops:
                    candidate['stop'] = max(any_stops)

    # write back
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(content, f, separators=(',', ':'), ensure_ascii=False)
        print(f"Processed {os.path.basename(path)}")
    except Exception as e:
        print(f"Failed to write {os.path.basename(path)}: {e}")


def main():
    parser = argparse.ArgumentParser(description='Prepare Allure results: group business steps and compute parent status')
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
