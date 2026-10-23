"""Build publication-review tables from actual measurements, never invented values."""
import argparse
import csv
import os
import statistics
import sys
from pathlib import Path

from fast_walks import WALKS
from diagnostics import coordinate_exact_mixing

LABEL = {'ball':'Ball Walk','dikin':'Dikin Walk',
         'coordinate_hit_run':'Coordinate Hit-and-Run',
         'random_hit_run':'Random Hit-and-Run','john':"John's Walk"}


def load(path):
    with open(path,newline='') as f: return list(csv.DictReader(f))


def write_table(out, name, data, dims):
    path=Path(out)/name
    with path.open('w') as f:
        f.write('| Walk | '+' | '.join(f'n={n}' for n in dims)+' |\n')
        f.write('|:--|'+'--:|'*len(dims)+'\n')
        for w in WALKS:
            f.write('| '+LABEL[w]+' | '+' | '.join(str(data.get((w,n),'—')) for n in dims)+' |\n')
    print(path)


def write_csv(path,rows,fields):
    with open(path,'w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)


def analyze(root,out, ks_limit, moment_limit):
    Path(out).mkdir(parents=True,exist_ok=True)
    runs={}
    dims=set()
    for language in ('python','cpp'):
        base=Path(root)/language
        c=load(base/'checkpoints.csv'); t=load(base/'runtime.csv')
        dims.update(int(r['n']) for r in t)
        by_run={}
        for r in c:
            key=(r['walk'],int(r['n']),int(r['repeat']))
            by_run.setdefault(key,[]).append(r)
        per_cell={}
        for (w,n,rep),checkpoints in by_run.items():
            checkpoints.sort(key=lambda x:int(x['step']))
            first=None
            passing=0
            for row in checkpoints:
                t_step=int(row['step'])
                if t_step==0:continue
                ok=float(row['ks_max'])<=ks_limit and float(row['moment_relative_error'])<=moment_limit
                passing=passing+1 if ok else 0
                if passing==2:
                    first=t_step
                    break
            per_cell[(w,n,rep)]=first
        runtime={}
        for row in t:
            runtime.setdefault((row['walk'],int(row['n'])),[]).append(float(row['us_per_step']))
        runs[language]={'convergence':per_cell,'runtime':runtime,'raw':c}
    dims=sorted(dims)
    rows=[]
    for w in WALKS:
        for n in dims:
            row={'walk':w,'n':n,'exact_coordinate_tv_10pct_steps':coordinate_exact_mixing(n,.1) if w=='coordinate_hit_run' else ''}
            for lang in ('python','cpp'):
                hit=[v for (ww,nn,_),v in runs[lang]['convergence'].items() if ww==w and nn==n]
                row[lang+'_proxy_steps'] = max(hit) if hit and all(v is not None for v in hit) else ''
                times=runs[lang]['runtime'].get((w,n),[])
                row[lang+'_us_per_step']=round(statistics.mean(times),3) if times else ''
            rows.append(row)
    fields=['walk','n','exact_coordinate_tv_10pct_steps','python_proxy_steps','cpp_proxy_steps','python_us_per_step','cpp_us_per_step']
    write_csv(Path(out)/'combined_results.csv',rows,fields)
    for lang in ('python','cpp'):
        for suffix,title in [('proxy_steps','empirical_convergence_checkpoints'),('us_per_step','microseconds_per_transition')]:
            data={(r['walk'],r['n']):(r[lang+'_'+suffix] if r[lang+'_'+suffix]!='' else 'not reached') for r in rows}
            write_table(out,lang+'_'+title+'.md',data,dims)
    data={(r['walk'],r['n']):r['exact_coordinate_tv_10pct_steps'] if r['walk']=='coordinate_hit_run' else '—' for r in rows}
    write_table(out,'exact_tv_coordinate_hit_and_run.md',data,dims)
    explanation=f'''# How to read the comparison matrices

Every matrix has one row per walk and one column per dimension. These numerical results are **pilot observations**, not proofs.

**Empirical convergence checkpoint:** The later checkpoint in the first pair of consecutive passing measured checkpoints at which (i) the maximum of coordinate and pair-sum Kolmogorov–Smirnov statistics is at most **{ks_limit}**, and (ii) the relative error in E[||X||²/n] is at most **{moment_limit}**. For a conservative across-repetition summary, the table reports the **latest** passing checkpoint among all repetitions; an entry is given only if *every repetition* passes. Otherwise it says **not reached**. Checkpoints were tested at 1, 2, 4, 8, ... and the final step, not at every integer. The result changes with the choice of thresholds, sample size and randomness. This is an **empirical convergence proxy, not the total-variation mixing time**.

**Exact coordinate mixing:** Only for Coordinate Hit-and-Run, the displayed number is the **exact total-variation mixing time at epsilon=0.1 from the origin** for the explicitly implemented kernel. At time t its TV distance equals the probability that at least one of the n coordinates has not yet been updated, by the coupon collector argument.

**Cost:** microseconds per transition of one chain, averaged over repetitions. Timings exclude diagnostics, plots and CSV writing. This depends on the machine, Python/compiler version and system load; C++ here was compiled with -O2. C++ and Python use distinct random generators, so individual trajectories are not expected to match exactly.

**The reported binned-TV statistic elsewhere is 1D marginal histogram discrepancy, not the full high-dimensional TV distance.** A projection can look uniform even if the joint measure has not mixed.
'''
    (Path(out)/'HOW_TO_READ_TABLES.md').write_text(explanation)
    print('Wrote matrices and combined results to',out)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--root',default='results/pilot')
    p.add_argument('--out',default='results/pilot/tables')
    p.add_argument('--ks-limit',type=float,default=.15)
    p.add_argument('--moment-limit',type=float,default=.25)
    args=p.parse_args(); analyze(args.root,args.out,args.ks_limit,args.moment_limit)
