"""Run explicit then optimized Python/C++ experiments with matching selected parameters."""
import argparse
import csv
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
import uuid

ROOT = Path(__file__).resolve().parent


def compare(baseline_folder, optimized_folder, destination):
    """Compare both programming approaches without conflating checkpoint and runtime."""
    def load(folder):
        with (folder/'tables'/'combined_results.csv').open(newline='') as handle:
            return {(r['walk'], r['n']):r for r in csv.DictReader(handle)}
    baseline,optimized=load(baseline_folder),load(optimized_folder)
    cols=['walk','n','baseline_python_proxy_steps','optimized_python_proxy_steps',
          'baseline_cpp_proxy_steps','optimized_cpp_proxy_steps',
          'baseline_python_us_per_step','optimized_python_us_per_step',
          'baseline_cpp_us_per_step','optimized_cpp_us_per_step',
          'python_speedup_per_transition','cpp_speedup_per_transition']
    destination.parent.mkdir(parents=True,exist_ok=True)
    with destination.open('w',newline='') as handle:
        writer=csv.DictWriter(handle,fieldnames=cols)
        writer.writeheader()
        for key in sorted(set(baseline)&set(optimized),key=lambda k:(int(k[1]),k[0])):
            a,b=baseline[key],optimized[key]
            row={'walk':key[0],'n':key[1]}
            for lang in ['python','cpp']:
                for label,source in [('baseline',a),('optimized',b)]:
                    row[f'{label}_{lang}_proxy_steps']=source[f'{lang}_proxy_steps']
                    row[f'{label}_{lang}_us_per_step']=source[f'{lang}_us_per_step']
                try:
                    denom=float(b[f'{lang}_us_per_step'])
                    row[f'{lang}_speedup_per_transition']=f"{float(a[f'{lang}_us_per_step'])/denom:.3f}" if denom>0 else ''
                except (TypeError,ValueError):row[f'{lang}_speedup_per_transition']=''
            writer.writerow(row)
    print('Saved baseline-versus-optimized table:', destination,flush=True)


def main():
    parser = argparse.ArgumentParser(description='Run both research stages; each stage runs Python and C++.')
    parser.add_argument('--dimensions', default='2,3,5')
    parser.add_argument('--steps', type=int, default=128)
    parser.add_argument('--chains', type=int, default=300)
    parser.add_argument('--seed', type=int, default=2026)
    parser.add_argument('--repeats', type=int, default=1)
    parser.add_argument('--threads', type=int, default=1, help='Threads only for optimized C++; baseline C++ is single-thread')
    parser.add_argument('--no-plots', action='store_true')
    args = parser.parse_args()
    if args.steps < 1 or args.chains < 10 or args.repeats < 1 or args.threads < 1:
        parser.error('positive steps, repeats and threads required; chains >= 10')
    root = ROOT / 'study_runs' / (datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '_' + uuid.uuid4().hex[:7])
    root.mkdir(parents=True, exist_ok=False)
    common = ['--dimensions', args.dimensions, '--steps', str(args.steps),
              '--chains', str(args.chains), '--seed', str(args.seed),
              '--repeats', str(args.repeats)]
    if args.no_plots: common.append('--no-plots')
    record = {'parameters': vars(args), 'status': 'INCOMPLETE', 'baseline': None, 'optimized': None}
    record_file = root / 'study_manifest.json'
    def save(): record_file.write_text(json.dumps(record, indent=2) + '\n')
    save()
    try:
        for name, script, destination, more in [
            ('baseline', 'run_baseline.py', 'runs_baseline', []),
            ('optimized', 'run_all.py', 'runs', ['--threads', str(args.threads)])
        ]:
            print('\n=== RUNNING ' + name.upper() + ' PYTHON AND C++ ===', flush=True)
            parent = ROOT / destination
            before = set(parent.iterdir())
            subprocess.run([sys.executable, str(ROOT/script), *common, *more], cwd=ROOT, check=True)
            after = set(parent.iterdir())
            created = [p for p in (after - before) if p.is_dir()]
            if len(created) != 1:
                raise RuntimeError('Could not uniquely identify the newly created ' + name + ' run')
            record[name] = str(created[0].relative_to(ROOT))
            save()
        compare(ROOT/record['baseline'],ROOT/record['optimized'],root/'baseline_vs_optimized.csv')
        record['status'] = 'COMPLETE'
        save()
        print('\nBOTH VERSIONS FINISHED:', record_file, flush=True)
        print('Baseline:', ROOT/record['baseline'], flush=True)
        print('Optimized:', ROOT/record['optimized'], flush=True)
    except BaseException:
        save()
        raise


if __name__ == '__main__':
    main()
