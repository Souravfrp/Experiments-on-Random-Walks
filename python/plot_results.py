"""Plot saved experiment results; drawing only, no sampling occurs here."""
import argparse
import csv
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

WALKS=('ball','dikin','coordinate_hit_run','random_hit_run','john')
LABELS={'ball':'Ball Walk','dikin':'Dikin Walk','coordinate_hit_run':'Coordinate Hit-and-Run','random_hit_run':'Random Hit-and-Run','john':"John's Walk"}


def rows(path):
    with Path(path).open(newline='') as f: return list(csv.DictReader(f))


def endpoints(rows_, n,walk):
    good=[r for r in rows_ if r['walk']==walk and int(r['n'])==n and int(r['repeat'])==0]
    if not good:return []
    t=max(int(r['step']) for r in good)
    return [[float(v) for v in r['coords'].split(';')] for r in good if int(r['step'])==t]


def geometry(root,lang,n,out):
    points=rows(root/lang/'snapshots.csv')
    if not points:return
    if n==1:
        fig,axes=plt.subplots(1,5,figsize=(16,3.2),constrained_layout=True)
        for ax,w in zip(axes,WALKS):
            pts=endpoints(points,n,w)
            if pts:ax.hist([v[0] for v in pts],bins=18,density=True)
            ax.axhline(1,linestyle='--',alpha=.55)
            ax.set_xlim(-.5,.5);ax.set_title(LABELS[w],fontsize=10)
        fig.suptitle(f'{lang.upper()} | n=1 | endpoint density (dashed uniform target)')
    elif n==2:
        fig,axes=plt.subplots(2,5,figsize=(17,7.4),constrained_layout=True)
        for j,w in enumerate(WALKS):
            pts=endpoints(points,n,w)
            if pts:
                a=[v[0] for v in pts];b=[v[1] for v in pts]
                axes[0][j].scatter(a,b,s=4,alpha=.55)
                axes[1][j].hist2d(a,b,bins=12,range=[[-.5,.5],[-.5,.5]])
            for i in range(2):
                axes[i][j].set_xlim(-.5,.5);axes[i][j].set_ylim(-.5,.5)
                axes[i][j].set_aspect('equal');axes[i][j].set_xlabel('x1')
                axes[i][j].set_ylabel('x2')
            axes[0][j].set_title(LABELS[w],fontsize=10)
        fig.suptitle(f'{lang.upper()} | n=2 | endpoint spread and empirical density')
    elif n==3:
        fig=plt.figure(figsize=(17,3.8),constrained_layout=True)
        for j,w in enumerate(WALKS):
            ax=fig.add_subplot(1,5,j+1,projection='3d')
            pts=endpoints(points,n,w)
            if pts:ax.scatter([v[0] for v in pts],[v[1] for v in pts],[v[2] for v in pts],s=4,alpha=.5)
            ax.set_xlim(-.5,.5);ax.set_ylim(-.5,.5);ax.set_zlim(-.5,.5)
            ax.set_title(LABELS[w],fontsize=10);ax.set_xlabel('x1');ax.set_ylabel('x2');ax.set_zlabel('x3')
        fig.suptitle(f'{lang.upper()} | n=3 | 3D endpoint sample clouds')
    else:
        fig,axes=plt.subplots(5,3,figsize=(11,14),constrained_layout=True)
        pairs=((0,1),(1,2),(2,0))
        for j,w in enumerate(WALKS):
            pts=endpoints(points,n,w)
            for k,(a,b) in enumerate(pairs):
                ax=axes[j][k]
                if pts:ax.hist2d([v[a] for v in pts],[v[b] for v in pts],bins=12,range=[[-.5,.5],[-.5,.5]])
                ax.set_xlim(-.5,.5);ax.set_ylim(-.5,.5);ax.set_aspect('equal')
                ax.set_xlabel(f'x{a+1}');ax.set_ylabel(f'x{b+1}')
                if k==0:ax.set_title(LABELS[w],fontsize=10,loc='left')
        fig.suptitle(f'{lang.upper()} | n={n} | density projections (x1,x2), (x2,x3), (x3,x1)')
    path=out/f'{lang}_n{n}_geometry.png';fig.savefig(path,dpi=140,bbox_inches='tight');plt.close(fig)


def convergence(root,n,out):
    fig,axes=plt.subplots(2,2,figsize=(13,8),constrained_layout=True)
    for j,lang in enumerate(('python','cpp')):
        records=rows(root/lang/'checkpoints.csv')
        for w in WALKS:
            sub=[r for r in records if r['walk']==w and int(r['n'])==n and int(r['repeat'])==0 and int(r['step'])>0]
            if not sub:continue
            t=[int(r['step']) for r in sub]
            axes[0][j].plot(t,[float(r['ks_max']) for r in sub],marker='.',label=LABELS[w])
            axes[1][j].plot(t,[float(r['moment_relative_error']) for r in sub],marker='.',label=LABELS[w])
        axes[0][j].axhline(.15,linestyle='--',alpha=.5)
        axes[1][j].axhline(.25,linestyle='--',alpha=.5)
        axes[0][j].set_title(lang.upper())
        for i in range(2):
            axes[i][j].set_xscale('log',base=2);axes[i][j].set_xlabel('Markov steps per chain');axes[i][j].grid(alpha=.25)
    axes[0][0].set_ylabel('Coordinate/pair KS discrepancy')
    axes[1][0].set_ylabel('Relative second-moment error')
    axes[0][1].legend(fontsize=7)
    fig.suptitle(f'n={n} | Empirical convergence diagnostics (not certified TV mixing)')
    fig.savefig(out/f'n{n}_python_cpp_convergence.png',dpi=160);plt.close(fig)


def scaling(root,dims,out):
    if len(dims)<2:return
    from collections import defaultdict
    data=rows(root/'tables'/'combined_results.csv')
    for metric in ('proxy_steps','cost_seconds'):
        fig,axes=plt.subplots(1,2,figsize=(13,4.7),constrained_layout=True)
        for ax,lang in zip(axes,('python','cpp')):
            for w in WALKS:
                xx=[];yy=[]
                for r in data:
                    if r['walk']!=w:continue
                    n=int(r['n'])
                    if n not in dims:continue
                    cp=r[lang+'_proxy_steps']
                    cost=r[lang+'_us_per_step']
                    if not cp or (metric=='cost_seconds' and not cost):continue
                    y=float(cp) if metric=='proxy_steps' else float(cp)*float(r.get('chains','') or 0)*float(cost)/1e6
                    if metric=='cost_seconds' and y==0:continue
                    xx.append(n); yy.append(y)
                if xx:ax.plot(xx,yy,marker='o',label=LABELS[w])
            ax.set_yscale('log');ax.set_xlabel('Dimension n');ax.set_title(lang.upper());ax.grid(alpha=.25)
        axes[0].set_ylabel('Empirical convergence checkpoint' if metric=='proxy_steps' else 'Estimated wall seconds to checkpoint')
        axes[1].legend(fontsize=7)
        fig.suptitle('Dimension scaling | no claim of theoretical mixing-time bounds')
        fig.savefig(out/f'dimensions_{metric}.png',dpi=160);plt.close(fig)


def cost_comparison(root,dims,chains,out):
    r=rows(root/'tables'/'combined_results.csv')
    for record in r:record['chains']=chains
    fig,ax=plt.subplots(figsize=(11,5),constrained_layout=True)
    single=(len(dims)==1)
    if single:
        n=dims[0];found={r['walk']:r for r in r if int(r['n'])==n}
        x=list(range(5));width=.36
        p=[float(found[w]['python_us_per_step']) for w in WALKS]
        c=[float(found[w]['cpp_us_per_step']) for w in WALKS]
        ax.bar([i-width/2 for i in x],p,width,label='Python NumPy')
        ax.bar([i+width/2 for i in x],c,width,label='C++ optimized')
        ax.set_xticks(x,[LABELS[w] for w in WALKS],rotation=20,ha='right')
        ax.set_yscale('log');ax.set_ylabel('Wall microseconds / chain transition')
        ax.set_title(f'n={n} | Measured amortized wall time per transition')
    else:
        for lang in ('python','cpp'):
            for w in WALKS:
                rr=sorted([row for row in r if row['walk']==w],key=lambda row:int(row['n']))
                ax.plot([int(row['n']) for row in rr],[float(row[lang+'_us_per_step']) for row in rr],marker='.',label=f'{lang} {LABELS[w]}')
        ax.set_yscale('log');ax.set_xlabel('Dimension n');ax.set_ylabel('Wall microseconds / chain transition')
        ax.set_title('Measured amortized transition runtime across dimensions')
    ax.legend(fontsize=8);ax.grid(alpha=.25)
    fig.savefig(out/'python_cpp_runtime.png',dpi=160);plt.close(fig)
    return r


def create(root,dims,chains):
    root=Path(root);out=root/'figures';out.mkdir(parents=True,exist_ok=True)
    for n in dims:
        for lang in ('python','cpp'):geometry(root,lang,n,out)
        convergence(root,n,out)
    cost_comparison(root,dims,chains,out)
    if len(dims)>1:
        # Incorporate chain count in temporary data via computation below.
        r=rows(root/'tables'/'combined_results.csv')
        for quantity in ('proxy_steps','cost_seconds'):
            fig,axs=plt.subplots(1,2,figsize=(13,4.8),constrained_layout=True)
            for ax,lang in zip(axs,('python','cpp')):
                for w in WALKS:
                    rr=sorted([v for v in r if v['walk']==w],key=lambda v:int(v['n']))
                    xx=[];yy=[]
                    for row in rr:
                        if not row[lang+'_proxy_steps']:continue
                        t=int(row[lang+'_proxy_steps'])
                        val=t if quantity=='proxy_steps' else t*chains*float(row[lang+'_us_per_step'])/1e6
                        xx.append(int(row['n']));yy.append(val)
                    if xx:ax.plot(xx,yy,marker='o',label=LABELS[w])
                ax.set_yscale('log');ax.set_xlabel('Dimension n');ax.grid(alpha=.3);ax.set_title(lang.upper())
            axs[0].set_ylabel('Empirical checkpoint' if quantity=='proxy_steps' else 'Estimated transition seconds to checkpoint')
            axs[1].legend(fontsize=7)
            fig.suptitle('Dimension scaling: empirical, not proven total variation mixing time')
            fig.savefig(out/f'dimensions_{quantity}.png',dpi=160);plt.close(fig)
    print('Saved plots in',out)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--dimensions',required=True);p.add_argument('--chains',type=int,required=True)
    a=p.parse_args()
    from experiment_fast import parse_dimensions
    create(a.root,parse_dimensions(a.dimensions),a.chains)
