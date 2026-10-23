// Five random walks on [-1/2,1/2]^n. Standard C++17 only.
// This mirrors python/walks.py and python/diagnostics.py mathematically.
#include <algorithm>
#include <chrono>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <numeric>
#include <random>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>
#include <thread>
using namespace std;
using Vec = vector<double>;
constexpr double HALF = 0.5;
const vector<string> WALKS = {"ball","dikin","coordinate_hit_run","random_hit_run","john"};

struct Rng {
    mt19937_64 gen;
    uniform_real_distribution<double> unif{0., 1.};
    normal_distribution<double> gaussian{0., 1.};
    explicit Rng(uint64_t seed) : gen(seed) {}
    double uniform() { return unif(gen); }
    double gauss() { return gaussian(gen); }
    int index(int n) { return uniform_int_distribution<int>(0,n-1)(gen); }
};

bool inside(const Vec &x) {
    for (double v : x) if (!(v > -HALF && v < HALF)) return false;
    return true;
}
// Scratch vectors allocated ONCE per worker, not once for each transition.
struct Workspace {
    Vec u,y,h;
    explicit Workspace(int n) : u(n),y(n),h(n) {}
};
void gaussian_vector(Vec &u, Rng &rng) {
    for(double &v:u) v=rng.gauss();
}
void unit_ball_into(Vec &u, Rng &rng) {
    double squared;
    do {
        squared=0.;
        for(double &v:u) {v=rng.gauss(); squared+=v*v;}
    } while (squared==0.);
    double scale=pow(rng.uniform(),1.0/u.size())/sqrt(squared);
    for(double &v:u)v*=scale;
}
inline double diagonal_hessian(double v) {
    double a=HALF-v,b=HALF+v;
    return 1./(a*a)+1./(b*b);
}
bool step_fast(Vec &x,int walk,Rng &rng,Workspace &ws) {
    int n=static_cast<int>(x.size());
    Vec &u=ws.u,&y=ws.y,&h=ws.h;
    if(walk==2) { // Coordinate Hit-and-Run: resample one coordinate.
        x[rng.index(n)]=rng.uniform()-HALF;
        return true;
    }
    if(walk==3) { // Random Hit-and-Run: unnormalized direction is sufficient.
        gaussian_vector(u,rng);
        double lo=-numeric_limits<double>::infinity();
        double hi=numeric_limits<double>::infinity();
        for(int i=0;i<n;i++) {
            if(abs(u[i])<1e-15) continue;
            double a=(-HALF-x[i])/u[i],b=(HALF-x[i])/u[i];
            lo=max(lo,min(a,b));hi=min(hi,max(a,b));
        }
        double t=lo+(hi-lo)*rng.uniform();
        for(int i=0;i<n;i++)x[i]+=t*u[i];
        return true;
    }
    unit_ball_into(u,rng);
    if(walk==0) { // Ball Walk: symmetric proposal with rejection.
        double r=.8/sqrt(static_cast<double>(n));
        for(int i=0;i<n;i++)y[i]=x[i]+r*u[i];
        if(!inside(y))return false;
        copy(y.begin(),y.end(),x.begin());return true;
    }
    if(walk==1) { // Dikin ellipsoid, reverse-support test and MH correction.
        for(int i=0;i<n;i++) {
            h[i]=diagonal_hessian(x[i]);
            y[i]=x[i]+u[i]/sqrt(h[i]);
        }
        if(!inside(y))return false;
        double reverse=0., log_ratio=0.;
        for(int i=0;i<n;i++) {
            double hy=diagonal_hessian(y[i]),dif=y[i]-x[i];
            reverse+=hy*dif*dif;
            log_ratio+=.5*log(hy/h[i]);
        }
        if(reverse>1.+1e-11)return false;
        if(log(max(rng.uniform(),1e-300))>min(0.,log_ratio))return false;
        copy(y.begin(),y.end(),x.begin());return true;
    }
    // John's Walk: symmetrized cube -> diagonal John ellipsoid; MH.
    double radius=.8;
    for(int i=0;i<n;i++) {
        h[i]=HALF-abs(x[i]); // local John ellipsoid semiaxis
        y[i]=x[i]+radius*h[i]*u[i];
    }
    if(!inside(y))return false;
    double reverse=0.,log_ratio=0.;
    for(int i=0;i<n;i++) {
        double dy=HALF-abs(y[i]),dif=y[i]-x[i];
        reverse+=(dif/dy)*(dif/dy);
        log_ratio+=log(h[i]/dy);
    }
    if(reverse>radius*radius+1e-11)return false;
    if(log(max(rng.uniform(),1e-300))>min(0.,log_ratio))return false;
    copy(y.begin(),y.end(),x.begin());return true;
}

double uniform_cdf(double x) { return max(0.,min(1.,x+HALF)); }
double triangle_cdf(double z) {
    if (z<=-1) return 0;
    if (z>=1) return 1;
    if (z<0) return .5*(z+1)*(z+1);
    return 1-.5*(1-z)*(1-z);
}
double ks_distance(Vec a, bool triangle=false) {
    sort(a.begin(),a.end());
    double discrepancy=0, m=static_cast<double>(a.size());
    for (size_t j=0;j<a.size();j++) {
        double f=triangle ? triangle_cdf(a[j]) : uniform_cdf(a[j]);
        discrepancy=max({discrepancy, abs(f-j/m), abs((j+1)/m-f)});
    }
    return discrepancy;
}
double binned_tv(const Vec &a) {
    constexpr int B=12;
    int count[B] = {0};
    for (double x : a) {
        int j=max(0,min(B-1, static_cast<int>((x+HALF)*B)));
        count[j]++;
    }
    double discrepancy=0;
    for (int c : count) discrepancy += abs(c/static_cast<double>(a.size())-1./B);
    return discrepancy/2.;
}
struct Stats { double ks, error, btv, pair; };
Stats measure(const vector<Vec> &points) {
    int n=static_cast<int>(points[0].size()), m=static_cast<int>(points.size());
    double max_ks=0, moment=0, btv=0, pair_ks=0;
    for (int i=0;i<n;i++) {
        Vec a; a.reserve(m);
        for (const Vec &x : points) a.push_back(x[i]);
        max_ks=max(max_ks,ks_distance(a));
        btv += binned_tv(a)/n;
    }
    if (n>1) {
        vector<pair<int,int>> pairs = n==2 ? vector<pair<int,int>>{{0,1}}
            : vector<pair<int,int>>{{0,1},{1,2},{2,0}};
        for (auto [i,j] : pairs) {
            Vec sum; sum.reserve(m);
            for (const Vec &x : points) sum.push_back(x[i]+x[j]);
            pair_ks=max(pair_ks,ks_distance(sum,true));
        }
    }
    max_ks=max(max_ks,pair_ks);
    for (const Vec &x : points) {
        for (double v : x) moment += v*v;
    }
    moment/=m*n;
    return {max_ks,abs(moment-1./12)/(1./12),btv,pair_ks};
}
double coordinate_tv(int n, int t) {
    Vec p(n+1,0.);p[0]=1.;
    for (int s=0;s<t;s++) {
        Vec q(n+1,0.);
        for(int k=0;k<=n;k++) {
            q[k]+=p[k]*k/n;
            if(k<n) q[k+1]+=p[k]*(n-k)/n;
        }
        p=std::move(q);
    }
    return max(0.,1.-p[n]);
}
vector<int> parse_dims(const string &value) {
    vector<int> out;
    size_t sep=value.find(':');
    if (sep!=string::npos) {
        int first=stoi(value.substr(0,sep)), last=stoi(value.substr(sep+1));
        if (first>last) throw invalid_argument("dimension range must ascend");
        for (int i=first;i<=last;i++) out.push_back(i);
    } else {
        stringstream ss(value);string item;
        while(getline(ss,item,','))out.push_back(stoi(item));
    }
    for (int n:out)if(n<1)throw invalid_argument("dimensions must be positive");
    return out;
}
vector<int> checkpoints(int steps) {
    vector<int> out{0};
    for(int x=1;x<steps && x>0;x*=2)out.push_back(x);
    if(out.back()!=steps)out.push_back(steps);
    return out;
}
struct Args {string dims="1:10",out="results/pilot/cpp",walk="all";
 int steps=256,chains=200,repeats=2,threads=1,snapshot_chains=300;uint64_t seed=2026;};
Args parse_args(int argc,char **argv) {
    Args a;
    for(int i=1;i<argc;i++) {
        string key=argv[i];
        if(i+1>=argc)throw invalid_argument("Missing value for "+key);
        string value=argv[++i];
        if(key=="--dimensions")a.dims=value;
        else if(key=="--steps")a.steps=stoi(value);
        else if(key=="--chains")a.chains=stoi(value);
        else if(key=="--repeats")a.repeats=stoi(value);
        else if(key=="--seed")a.seed=stoull(value);
        else if(key=="--out")a.out=value;
        else if(key=="--threads")a.threads=stoi(value);
        else if(key=="--snapshot-chains")a.snapshot_chains=stoi(value);
        else if(key=="--walk")a.walk=value;
        else throw invalid_argument("Unknown option "+key);
    }
    if(a.steps<1||a.chains<1||a.repeats<1||a.threads<1||a.snapshot_chains<0)throw invalid_argument("steps, chains, repeats, threads>=1; snapshot-chains>=0");
    if(a.walk!="all"&&find(WALKS.begin(),WALKS.end(),a.walk)==WALKS.end())
        throw invalid_argument("Unknown walk");
    return a;
}

int main(int argc,char **argv) {
 try {
    Args a=parse_args(argc,argv);
    filesystem::create_directories(a.out);
    ofstream fm(a.out+"/checkpoints.csv"),fs(a.out+"/snapshots.csv"),fr(a.out+"/runtime.csv");
    fm<<"walk,n,repeat,step,chains,ks_max,ks_pair_max,moment_relative_error,binned_tv_marginal,acceptance_rate,coordinate_exact_tv\n";
    fs<<"walk,n,repeat,step,chain,coords\n";
    fr<<"walk,n,repeat,steps,chains,runtime_s,us_per_step,acceptance_rate\n";
    fm<<setprecision(9)<<fixed;fr<<setprecision(9)<<fixed;fs<<setprecision(9)<<fixed;
    for(int n:parse_dims(a.dims))for(int w=0;w<5;w++) {
        if(a.walk!="all"&&a.walk!=WALKS[w])continue;
        for(int repeat=0;repeat<a.repeats;repeat++) {
            uint64_t base_seed=a.seed+1000003ULL*n+100003ULL*w+1009ULL*repeat;
            vector<Rng> rngs; rngs.reserve(a.chains);
            for(int i=0;i<a.chains;i++)rngs.emplace_back(base_seed+37ULL*(i+1));
            vector<Vec> points(a.chains,Vec(n,0.));
            long long accepted=0;double runtime=0;int prev=0;
            int used_threads=min(a.threads,a.chains);
            for(int cp:checkpoints(a.steps)) {
                if(cp>prev) {
                    auto start=chrono::steady_clock::now();
                    vector<long long> counts(used_threads,0);
                    auto worker = [&](int id) {
                        Workspace ws(n);
                        int first=(id*a.chains)/used_threads;
                        int last=((id+1)*a.chains)/used_threads;
                        long long local=0;
                        // Each chain has its OWN generator, independent of worker count.
                        for(int j=first;j<last;j++)
                            for(int s=prev;s<cp;s++)
                                local+=step_fast(points[j],w,rngs[j],ws);
                        counts[id]=local;
                    };
                    if(used_threads==1) worker(0);
                    else {
                        vector<thread> workers;workers.reserve(used_threads);
                        for(int id=0;id<used_threads;id++)workers.emplace_back(worker,id);
                        for(auto &t:workers)t.join();
                    }
                    for(long long c:counts)accepted+=c;
                    auto stop=chrono::steady_clock::now();
                    runtime+=chrono::duration<double>(stop-start).count();
                }
                Stats metric=measure(points);
                double acceptance=cp==0?0:accepted/static_cast<double>(cp*a.chains);
                fm<<WALKS[w]<<","<<n<<","<<repeat<<","<<cp<<","<<a.chains<<","<<metric.ks<<","<<metric.pair<<","<<metric.error<<","<<metric.btv<<","<<acceptance<<",";
                if(w==2)fm<<coordinate_tv(n,cp);
                fm<<"\n";
                if(repeat==0)for(int j=0;j<min(a.chains,a.snapshot_chains);j++) {
                    fs<<WALKS[w]<<","<<n<<","<<repeat<<","<<cp<<","<<j<<",";
                    for(int k=0;k<n;k++) {
                        if(k)fs<<";";
                        fs<<points[j][k];
                    }
                    fs<<"\n";
                }
                prev=cp;
            }
            fr<<WALKS[w]<<","<<n<<","<<repeat<<","<<a.steps<<","<<a.chains<<","<<runtime<<","<<1e6*runtime/(a.steps*a.chains)<<","<<accepted/static_cast<double>(a.steps*a.chains)<<"\n";
            cout<<"C++ optimized ("<<used_threads<<" thread(s)): n="<<n<<"  "<<WALKS[w]<<"  repeat="<<repeat+1<<"  "<<runtime<<"s\n";
        }
    }
    cout<<"Saved C++ results in "<<a.out<<"\n";
 } catch(const exception &e) {cerr<<"Error: "<<e.what()<<"\n";return 1;}
}
