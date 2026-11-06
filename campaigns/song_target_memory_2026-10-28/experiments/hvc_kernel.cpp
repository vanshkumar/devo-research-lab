// Direct numerical port of Mackevicius/Happ/Fee Supplementary Code HVCIter.m.
// Keep arithmetic explicit; no BLAS and no fast-math. w[i,j] is j -> i.
#include <vector>
#include <algorithm>
extern "C" void hvc_run(int n,int steps,double* w,const unsigned char* noise,
    const unsigned char* onset,double* params,unsigned char* activity) {
    const double beta=params[0],alpha=params[1],eta=params[2],eps=params[3];
    const double tau=params[4],gamma=params[5],wmax=params[6],Wmax=params[7];
    const int k=(int)params[8];
    std::vector<double> old(n,0),y(n,0),a(n),x(n),col(n),row(n),delta(n*n);
    for(int t=0;t<steps;t++) {
        double oldsum=0;for(int i=0;i<n;i++)oldsum+=old[i];
        double asum=0;
        for(int i=0;i<n;i++) {
            y[i]+=(old[i]-y[i])/tau;
            double excitation=0;
            for(int j=0;j<n;j++)excitation+=w[i*n+j]*old[j];
            double b=i<k?(onset[t]?10.:-10.):(double)noise[t*n+i];
            a[i]=std::max(0.,excitation-beta*oldsum-alpha*y[i]+b);
            asum+=a[i];
        }
        for(int i=0;i<n;i++) {
            x[i]=(a[i]-gamma*asum)>0?1.:0.;
            activity[t*n+i]=(unsigned char)x[i];
        }
        if(eta>0) {
            std::fill(col.begin(),col.end(),0.);
            std::fill(row.begin(),row.end(),0.);
            for(int i=0;i<n;i++)for(int j=0;j<n;j++) {
                const int ij=i*n+j;
                delta[ij]=eta*(x[i]*old[j]-old[i]*x[j]);
                col[j]+=w[ij]+delta[ij];row[i]+=w[ij]+delta[ij];
            }
            for(int j=0;j<n;j++)col[j]=eta*std::max(0.,col[j]-Wmax);
            for(int i=0;i<n;i++)row[i]=eta*std::max(0.,row[i]-Wmax);
            for(int i=0;i<n;i++)for(int j=0;j<n;j++) {
                const int ij=i*n+j;
                w[ij]=i==j?0.:std::clamp(w[ij]+delta[ij]-eps*(col[j]+row[i]),0.,wmax);
            }
        }
        old=x;
    }
}
