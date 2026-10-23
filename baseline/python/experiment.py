"""Run independent chains; save endpoints and numerical diagnostics to CSV.

Example:
 python python/experiment.py --dimensions 1:10 --steps 256 --chains 200 --repeats 2
"""
import argparse
import csv
import os
import random
import time
from walks import WALKS, STEPS
from diagnostics import measure, coordinate_exact_tv


def dimensions(text):
    if ':' in text:
        a, b = [int(s) for s in text.split(':')]
        dims = list(range(a, b+1))
    else:
        dims = [int(s) for s in text.split(',')]
    if not dims or any(n < 1 for n in dims):
        raise ValueError('All dimensions must be positive integers')
    return dims


def checkpoints(steps):
    c = [0]
    k = 1
    while k < steps:
        if k in (1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096): c.append(k)
        k *= 2
    if steps not in c: c.append(steps)
    return c


def run(n, walk, steps, chains, repeat, seed, metrics, snapshots, summary):
    # Each chain owns a random generator. This is reproducible across Python runs.
    # C++ has its own standard random generator; the numerical draws are not identical.
    w_index = WALKS.index(walk)
    base_seed = seed + 1000003*n + 100003*w_index + 1009*repeat
    rngs = [random.Random(base_seed + 37*(i+1)) for i in range(chains)]
    xs = [[0.]*n for _ in range(chains)]
    fn = STEPS[walk]
    accepted = 0
    runtime = 0.
    prev = 0
    cps = checkpoints(steps)
    for cp in cps:
        if cp > prev:
            # Only measure the transition loop, excluding plots, CSV, and diagnostics.
            start = time.perf_counter()
            for _ in range(cp-prev):
                for j in range(chains):
                    accepted += int(fn(xs[j], rngs[j]))
            runtime += time.perf_counter()-start
        ks, error, btv, pair_ks = measure(xs)
        total = max(1, cp*chains)
        exact = coordinate_exact_tv(n, cp) if walk == 'coordinate_hit_run' else ''
        metrics.writerow([walk,n,repeat,cp,chains,f'{ks:.8f}',f'{pair_ks:.8f}',f'{error:.8f}',f'{btv:.8f}',f'{accepted/total:.6f}',exact])
        # Snapshot the first repetition only; use coordinates separated by semicolons.
        if repeat == 0:
            for i, x in enumerate(xs):
                snapshots.writerow([walk,n,repeat,cp,i,';'.join(f'{v:.10f}' for v in x)])
        prev=cp
    summary.writerow([walk,n,repeat,steps,chains,f'{runtime:.8f}',f'{1e6*runtime/(steps*chains):.8f}',f'{accepted/(steps*chains):.6f}'])
    print(f'Python: n={n:2d}  {walk:19s}  repeat={repeat+1}  {runtime:.4f}s')


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--dimensions', default='1:10')
    p.add_argument('--steps',type=int,default=256)
    p.add_argument('--chains',type=int,default=200)
    p.add_argument('--repeats',type=int,default=2)
    p.add_argument('--seed',type=int,default=2026)
    p.add_argument('--out',default='results/pilot/python')
    p.add_argument('--walk',choices=['all']+list(WALKS),default='all')
    a=p.parse_args()
    if a.steps<1 or a.chains<10 or a.repeats<1: p.error('steps >= 1; chains >= 10; repeats >= 1')
    os.makedirs(a.out,exist_ok=True)
    with open(f'{a.out}/checkpoints.csv','w',newline='') as fm, open(f'{a.out}/snapshots.csv','w',newline='') as fs, open(f'{a.out}/runtime.csv','w',newline='') as fr:
        m,s,r = csv.writer(fm),csv.writer(fs),csv.writer(fr)
        m.writerow(['walk','n','repeat','step','chains','ks_max','ks_pair_max','moment_relative_error','binned_tv_marginal','acceptance_rate','coordinate_exact_tv'])
        s.writerow(['walk','n','repeat','step','chain','coords'])
        r.writerow(['walk','n','repeat','steps','chains','runtime_s','us_per_step','acceptance_rate'])
        for n in dimensions(a.dimensions):
            for walk in (WALKS if a.walk=='all' else [a.walk]):
                for rep in range(a.repeats):
                    run(n,walk,a.steps,a.chains,rep,a.seed,m,s,r)

if __name__=='__main__': main()
