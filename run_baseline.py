"""Run the explicit Python and C++ implementations without changing their algorithms."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
import uuid

ROOT = Path(__file__).resolve().parent


def call(command):
    print('\n$ ' + ' '.join(map(str, command)), flush=True)
    subprocess.run(command, cwd=ROOT, check=True)


def main():
    p = argparse.ArgumentParser(description='Run the explicit random walks in Python and C++, preserving an experiment archive.')
    p.add_argument('--dimensions', default='2,3,5')
    p.add_argument('--steps', type=int, default=128)
    p.add_argument('--chains', type=int, default=300)
    p.add_argument('--seed', type=int, default=2026)
    p.add_argument('--repeats', type=int, default=1)
    p.add_argument('--ks-limit', type=float, default=.15)
    p.add_argument('--moment-limit', type=float, default=.25)
    p.add_argument('--no-plots', action='store_true')
    args = p.parse_args()
    if args.steps < 1 or args.chains < 10 or args.repeats < 1:
        p.error('steps and repeats must be positive, and chains must be at least 10')
    identifier = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '_' + uuid.uuid4().hex[:7]
    folder = ROOT / 'runs_baseline' / identifier
    folder.mkdir(parents=True, exist_ok=False)
    (folder / 'parameters.json').write_text(json.dumps({
        'experiment_id': identifier, 'language': ['Python', 'C++17'],
        'implementation': 'explicit (baseline)', 'dimensions': args.dimensions,
        'steps': args.steps, 'chains': args.chains, 'repeats': args.repeats,
        'seed': args.seed, 'cpp_threads': 1, 'compiler_flags': '-O2',
        'ks_limit': args.ks_limit, 'moment_limit': args.moment_limit,
        'results_are_empirical_diagnostics_not_proven_mixing_times': True
    }, indent=2) + '\n')
    common = ['--dimensions', args.dimensions, '--steps', str(args.steps),
              '--chains', str(args.chains), '--repeats', str(args.repeats),
              '--seed', str(args.seed)]
    try:
        call([sys.executable, str(ROOT/'baseline/python/experiment.py'),
              *common, '--out', str(folder/'python')])
        call(['c++', '-std=c++17', '-O2', str(ROOT/'baseline/cpp/walks.cpp'),
              '-o', str(ROOT/'baseline/cpp/random_walks_baseline')])
        call([str(ROOT/'baseline/cpp/random_walks_baseline'),
              *common, '--out', str(folder/'cpp')])
        call([sys.executable, str(ROOT/'python/tables.py'),
              '--root', str(folder), '--out', str(folder/'tables'),
              '--ks-limit', str(args.ks_limit), '--moment-limit', str(args.moment_limit)])
        if not args.no_plots:
            call([sys.executable, str(ROOT/'python/plot_results.py'),
                  '--root', str(folder), '--dimensions', args.dimensions,
                  '--chains', str(args.chains)])
        (folder / 'STATUS.txt').write_text('COMPLETE\n')
        print('\nBASELINE FINISHED:', folder, flush=True)
    except BaseException:
        (folder / 'STATUS.txt').write_text('INCOMPLETE; partial results may exist.\n')
        print('\nBASELINE INCOMPLETE:', folder, flush=True)
        raise


if __name__ == '__main__':
    main()
