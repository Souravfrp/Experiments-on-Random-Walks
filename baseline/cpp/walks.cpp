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
Vec direction(int n, Rng &rng) {
    Vec v(n);
    double squared = 0;
    do {
        squared = 0;
        for (double &a : v) { a = rng.gauss(); squared += a*a; }
    } while (squared == 0);
    for (double &a : v) a /= sqrt(squared);
    return v;
}
Vec unit_ball(int n, Rng &rng) {
    Vec u = direction(n,rng);
    double r = pow(rng.uniform(), 1./n);
    for (double &v : u) v *= r;
    return u;
}
Vec dikin_hessian(const Vec &x) {
    Vec h;
    for (double v : x) h.push_back(1./pow(HALF-v,2) + 1./pow(HALF+v,2));
    return h;
}
bool step(Vec &x, int walk, Rng &rng) {
    int n = static_cast<int>(x.size());
    if (walk == 0) { // Ball Walk: symmetric proposal; reject outside K.
        Vec u = unit_ball(n,rng), y = x;
        double radius = 0.8/sqrt(static_cast<double>(n));
        for (int i=0; i<n; i++) y[i] += radius*u[i];
        if (!inside(y)) return false;
        x = std::move(y); return true;
    }
    if (walk == 1) { // Dikin Walk: barrier-Hessian ellipsoid + MH correction.
        Vec h_x = dikin_hessian(x), u = unit_ball(n,rng), y=x;
        double radius=1.0;
        for (int i=0; i<n; i++) y[i] += radius*u[i]/sqrt(h_x[i]);
        if (!inside(y)) return false;
        Vec h_y=dikin_hessian(y);
        double reverse=0, log_ratio=0;
        for (int i=0;i<n;i++) {
            reverse += h_y[i]*pow(y[i]-x[i],2);
            log_ratio += 0.5*log(h_y[i]/h_x[i]);
        }
        if (reverse>radius*radius+1e-11) return false;
        if (log(max(rng.uniform(),1e-300))<=min(0.,log_ratio)) {
            x=std::move(y);return true;
        }
        return false;
    }
    if (walk == 2) { // Coordinate Hit-and-Run: resample one coordinate.
        x[rng.index(n)] = rng.uniform()-HALF;
        return true;
    }
    if (walk == 3) { // Random Hit-and-Run: sample uniform full chord.
        Vec d=direction(n,rng);
        double left=-numeric_limits<double>::infinity();
        double right=numeric_limits<double>::infinity();
        for (int i=0;i<n;i++) {
            if (abs(d[i])<1e-15) continue;
            double lo=(-HALF-x[i])/d[i], hi=(HALF-x[i])/d[i];
            left=max(left,min(lo,hi)); right=min(right,max(lo,hi));
        }
        double t=left+(right-left)*rng.uniform();
        for (int i=0;i<n;i++) x[i] += t*d[i];
        return true;
    }
    // John ellipsoid of centred symmetrized cube at x; MH ratio explicit.
    Vec d_x(n), y=x, u=unit_ball(n,rng);
    double radius=.8;
    for (int i=0;i<n;i++) {
        d_x[i] = HALF-abs(x[i]);
        y[i] += radius*d_x[i]*u[i];
    }
    if (!inside(y)) return false;
    double reverse=0, log_ratio=0;
    for (int i=0;i<n;i++) {
        double d_y=HALF-abs(y[i]);
        reverse += pow((y[i]-x[i])/d_y,2);
        log_ratio += log(d_x[i]/d_y);
    }
    if (reverse>radius*radius+1e-11) return false;
    if (log(max(rng.uniform(),1e-300))<=min(0.,log_ratio)) {
        x=std::move(y);return true;
    }
    return false;
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
 int steps=256,chains=200,repeats=2;uint64_t seed=2026;};
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
        else if(key=="--walk")a.walk=value;
        else throw invalid_argument("Unknown option "+key);
    }
    if(a.steps<1||a.chains<10||a.repeats<1)throw invalid_argument("steps>=1, chains>=10, repeats>=1");
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
            for(int cp:checkpoints(a.steps)) {
                if(cp>prev) {
                    auto start=chrono::steady_clock::now();
                    for(int s=prev;s<cp;s++)for(int j=0;j<a.chains;j++)
                        accepted += step(points[j],w,rngs[j]);
                    auto stop=chrono::steady_clock::now();
                    runtime += chrono::duration<double>(stop-start).count();
                }
                Stats metric=measure(points);
                double acceptance=cp==0?0:accepted/static_cast<double>(cp*a.chains);
                fm<<WALKS[w]<<","<<n<<","<<repeat<<","<<cp<<","<<a.chains<<","<<metric.ks<<","<<metric.pair<<","<<metric.error<<","<<metric.btv<<","<<acceptance<<",";
                if(w==2)fm<<coordinate_tv(n,cp);
                fm<<"\n";
                if(repeat==0)for(int j=0;j<a.chains;j++) {
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
            cout<<"C++: n="<<n<<"  "<<WALKS[w]<<"  repeat="<<repeat+1<<"  "<<runtime<<"s\n";
        }
    }
    cout<<"Saved C++ results in "<<a.out<<"\n";
 } catch(const exception &e) {cerr<<"Error: "<<e.what()<<"\n";return 1;}
}
