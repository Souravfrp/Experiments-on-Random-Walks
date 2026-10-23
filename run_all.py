"""A single command runs the same cube experiment in Python and C++.

Example (n=20):
 python run_all.py --dimensions 20 --steps 2560 --chains 3000 --seed 2026

Create a fresh, timestamped run folder on every invocation. No overwriting.
"""
import argparse
import hashlib
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import uuid

ROOT = Path(__file__).resolve().parent


def invoke(command):
    print('\n$ ' + ' '.join(str(x) for x in command), flush=True)
    subprocess.run(command, cwd=ROOT, check=True)


def main():
    parser = argparse.ArgumentParser(description='Run all five cube walks, compare Python/C++, and save figures/tables.')
    parser.add_argument('--dimensions', default='20', help='20, or 1:10, or 2,3,5,20')
    parser.add_argument('--steps', type=int, default=2560)
    parser.add_argument('--chains', type=int, default=3000)
    parser.add_argument('--seed', type=int, default=2026)
    parser.add_argument('--repeats', type=int, default=1)
    parser.add_argument('--threads', type=int, default=4, help='C++ worker threads; use 1 for single-thread timing')
    parser.add_argument('--snapshot-chains', type=int, default=300, help='Limit stored coordinate snapshots')
    parser.add_argument('--ks-limit', type=float, default=0.15)
    parser.add_argument('--moment-limit', type=float, default=0.25)
    parser.add_argument('--label', default='', help='Optional run label consisting of letters, numbers, underscores or hyphens')
    parser.add_argument('--no-plots', action='store_true', help='Run without Matplotlib')
    args = parser.parse_args()
    if min(args.steps, args.chains, args.repeats, args.threads) < 1 or args.snapshot_chains < 0:
        parser.error('steps, chains, repeats and threads must be positive; snapshot-chains must be nonnegative')
    if args.label and (not all(c.isalnum() or c in '_-' for c in args.label) or len(args.label)>40):
        parser.error('label must be <= 40 letters, numbers, underscores or hyphens')

    sys.path.insert(0, str(ROOT / 'python'))
    from experiment_fast import parse_dimensions
    dimensions = parse_dimensions(args.dimensions)
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    run_id = stamp + '_' + (args.label + '_' if args.label else '') + uuid.uuid4().hex[:7]
    out = ROOT / 'runs' / run_id
    out.mkdir(parents=True, exist_ok=False)
    python_script = ROOT / 'python' / 'experiment_fast.py'
    cpp_source = ROOT / 'cpp' / 'walks_optimized.cpp'
    cpp_binary = ROOT / 'cpp' / 'random_walks_optimized'
    compile_cmd = ['c++', '-std=c++17', '-O3', '-pthread', str(cpp_source), '-o', str(cpp_binary)]
    metadata = {
        'experiment_id': run_id,
        'created_utc': datetime.now(timezone.utc).isoformat(),
        'dimensions': dimensions,
        'steps': args.steps,
        'chains': args.chains,
        'seed': args.seed,
        'repeats': args.repeats,
        'cpp_threads': args.threads,
        'snapshot_chains_per_walk_at_checkpoints': args.snapshot_chains,
        'python_implementation': 'NumPy vectorized batch chains',
        'cpp_implementation': 'C++17 reusable buffers and per-chain RNG, optional threads',
        'python_version': platform.python_version(),
        'python_executable': sys.executable,
        'numpy_version': __import__('numpy').__version__,
        'compiler_command': compile_cmd,
        'platform': platform.platform(),
        'processor': platform.processor(),
        'machine': platform.machine(),
        'cpu_count_reported': os.cpu_count(),
        'source_sha256': {
            str(f.relative_to(ROOT)): hashlib.sha256(f.read_bytes()).hexdigest()
            for f in [python_script, cpp_source, ROOT/'python'/'fast_walks.py',
                      ROOT/'python'/'diagnostics.py', ROOT/'python'/'tables.py']
        },
        'ks_limit': args.ks_limit,
        'moment_limit': args.moment_limit,
        'empirical_checkpoint_not_theoretical_mixing_time': True,
    }
    (out/'parameters.json').write_text(json.dumps(metadata, indent=2) + '\n')

    common=['--dimensions',args.dimensions,'--steps',str(args.steps),'--chains',str(args.chains),
            '--repeats',str(args.repeats),'--seed',str(args.seed),
            '--snapshot-chains',str(args.snapshot_chains)]
    try:
        invoke([sys.executable,str(python_script),*common,'--out',str(out/'python')])
        invoke(compile_cmd)
        invoke([str(cpp_binary),*common,'--threads',str(args.threads),'--out',str(out/'cpp')])
        invoke([sys.executable,str(ROOT/'python'/'tables.py'), '--root',str(out), '--out',str(out/'tables'),
                '--ks-limit',str(args.ks_limit), '--moment-limit',str(args.moment_limit)])
        if not args.no_plots:
            invoke([sys.executable,str(ROOT/'python'/'plot_results.py'), '--root',str(out),
                    '--dimensions',args.dimensions, '--chains',str(args.chains)])
        (out/'STATUS.txt').write_text('COMPLETE: both implementations, tables' + (', and figures' if not args.no_plots else '') + '\n')
        print('\nFINISHED. Archive saved to:',out,flush=True)
        print('Open tables:',out/'tables'/'combined_results.csv',flush=True)
        if not args.no_plots: print('Open figures:',out/'figures',flush=True)
    except (Exception,KeyboardInterrupt):
        (out/'STATUS.txt').write_text('INCOMPLETE: at least one stage did not finish; partial files may exist.\n')
        print('\nINCOMPLETE run retained for inspection at:',out,flush=True)
        raise


if __name__=='__main__': main()
