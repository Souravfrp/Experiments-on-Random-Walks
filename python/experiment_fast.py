"""Batched NumPy experiment with the same CSV schema as the original version."""
import argparse
import csv
from pathlib import Path
import time
import numpy as np
from fast_walks import WALKS,step
from diagnostics import measure, coordinate_exact_tv


def parse_dimensions(s):
    dims=[]
    for component in s.split(','):
        if ':' in component:
            a,b=map(int,component.split(':'))
            if b<a: raise ValueError('Dimension range must ascend')
            dims.extend(range(a,b+1))
        else: dims.append(int(component))
    if not dims or min(dims)<1: raise ValueError('Positive integer dimension required')
    return list(dict.fromkeys(dims))


def checkpoints(t):
    result=[0]
    k=1
    while k<t:
        result.append(k)
        k*=2
    if t!=result[-1]: result.append(t)
    return result


def run(n,walk,steps,chains,repeat,seed,metrics,snapshots,runtime,snapshot_chains):
    rng=np.random.default_rng(seed+1000003*n+100003*WALKS.index(walk)+1009*repeat)
    x=np.zeros((chains,n),dtype=np.float64)
    accepted=0
    spent=0.0
    prev=0
    for cp in checkpoints(steps):
        if cp>prev:
            start=time.perf_counter()
            for _ in range(cp-prev):
                accepted+=step(x,walk,rng)
            spent+=time.perf_counter()-start
        # Diagnostics intentionally excluded from transition clock.
        ks, moment, btv,pair=measure(x.tolist())
        exact=coordinate_exact_tv(n,cp) if walk=='coordinate_hit_run' else ''
        metrics.writerow([walk,n,repeat,cp,chains,f'{ks:.8f}',f'{pair:.8f}',f'{moment:.8f}',f'{btv:.8f}',f'{accepted/max(1,cp*chains):.6f}',exact])
        if repeat==0:
            for i in range(min(snapshot_chains,chains)):
                snapshots.writerow([walk,n,repeat,cp,i,';'.join(f'{v:.9f}' for v in x[i])])
        prev=cp
    runtime.writerow([walk,n,repeat,steps,chains,f'{spent:.9f}',f'{1e6*spent/(steps*chains):.9f}',f'{accepted/(steps*chains):.6f}'])
    print(f'Python NumPy: n={n:3d}  {walk:19s} repeat={repeat+1} {spent:.4f}s',flush=True)


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--dimensions',default='20')
    p.add_argument('--steps',type=int,default=2560)
    p.add_argument('--chains',type=int,default=3000)
    p.add_argument('--seed',type=int,default=2026)
    p.add_argument('--repeats',type=int,default=1)
    p.add_argument('--snapshot-chains',type=int,default=300)
    p.add_argument('--out',default='runs/standalone/python')
    p.add_argument('--walk',choices=['all']+list(WALKS),default='all')
    a=p.parse_args()
    if min(a.steps,a.chains,a.repeats)<1 or a.snapshot_chains<0: p.error('steps, chains, repeats positive; snapshot-chains nonnegative')
    out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
    with (out/'checkpoints.csv').open('w',newline='') as fm,(out/'snapshots.csv').open('w',newline='') as fs,(out/'runtime.csv').open('w',newline='') as fr:
        m,s,r=map(csv.writer,(fm,fs,fr))
        m.writerow(['walk','n','repeat','step','chains','ks_max','ks_pair_max','moment_relative_error','binned_tv_marginal','acceptance_rate','coordinate_exact_tv'])
        s.writerow(['walk','n','repeat','step','chain','coords'])
        r.writerow(['walk','n','repeat','steps','chains','runtime_s','us_per_step','acceptance_rate'])
        for n in parse_dimensions(a.dimensions):
            for w in WALKS if a.walk=='all' else (a.walk,):
                for rep in range(a.repeats): run(n,w,a.steps,a.chains,rep,a.seed,m,s,r,a.snapshot_chains)
    print('Saved Python results in',out)

if __name__=='__main__':main()
