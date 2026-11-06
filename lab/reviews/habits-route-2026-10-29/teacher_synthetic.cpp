
#include <cmath>
#include <cstdio>
using byte = unsigned char;
struct FakeSerial { void print(const char*) {} } Serial;
long random(long a, long b) { return a; }
float sgn(float);
byte TrialType = 1;
byte TrialTypeContrast[2] = {};
float W_star[7] = {0,10,-10,0,0,0,0};
struct DATAModel{
    float x[7] = {}; // 特征变量 bias S0{X1 ,X2} WSLS S1 A1 R1
    int y = 0; // 目标变量 Left or Right 
};
struct DATAModel MiceChoiceData;
struct DATAModel TrialTypeData;

// 定义逻辑回归模型结构
typedef struct {
    float theta[7] = {0}; // 参数向量，包括截距项
    float alpha = 0.01; // 学习率 Correct Sample
    float L1        = 0;        // L1 regularization value
    float Gamma    = 0.03;    // argMax param: learning rate of Mouse model 用来调整自适应训练算法的策略
    float Eta = 1.0; // argMax中小鼠模型对梯度的学习率
    float beta      = 0;  // Momentum param
    int    t         = 0;    // iterative number
    float m[7]     = {0};    // moment value
    float S0[5] = {-1, 0.5, 0, 0.5, 1}; // S0 params 
} LOGISTIC;
//LOGISTIC *model; //  注意；这里 只是定义了一个结构体的指针，并没有实例化这个结构体；需要实例化后再让这个指针指向这个实例结构体变量,这样可以节约空间，结构体实例可以随时free掉
LOGISTIC model; // 使用off-policy
LOGISTIC actionmodel;
float sigmoid(float z) {
    return 1.0 / (1.0 + exp(-z));
}

// 定义预测函数，返回样本属于第k类的概率
float predictFunc(struct DATAModel *data, int k) {
    float z = 0;
    for (int i = 0; i < 7; i++) { 
        z += model.theta[i] * data->x[i];
    }
    if (k == 0) { // 第0类的概率为1-sigmoid(z) // left 0
        return 1.0 - sigmoid(z);
    } 
    else if (k == 1) { // 第1类的概率为sigmoid(z) // right 1
        return sigmoid(z);
    } else {
      Serial.print("Invalid class label");
      return -1.0;
    }
}

// 定义损失函数，返回对数似然损失值
float lossFunc(struct DATAModel *data ,int n) {  //  n == 1
    float l = 0.0;
    
    l += log(predictFunc(data, 1)) * data->y; // 计算每个样本的对数似然值，并累加到损失值中
    l += (1.0 - data->y) * log(1.0 - predictFunc(data, 1));
    
    return -l / n; // 返回负对数似然损失值的平均值（最小化目标）
}

// 定义随机梯度下降法，更新参数向量，并返回更新后的损失值 ，使用的数据为小鼠的实际选择数据
float UpdateMiceParams(struct DATAModel *data, int n) { // batch size is 1
    model.t = model.t + 1;
    float yhat = predictFunc(data, 1); // 计算预测值
    for (int j = 0; j < 7; j++) { // 遍历所有参数
      model.m[j] = ((yhat - data->y) * data->x[j]) * (1.0 - model.beta) + model.beta * model.m[j];
      model.theta[j] -= model.alpha * (model.m[j]/(1.0 - pow(model.beta ,model.t)) + model.L1 * sgn(model.theta[j])) ; // 初始化偏差校正
    }
    return lossFunc(data, n); // 返回更新后的损失值
}


void SelectTrialType(struct DATAModel *data ,byte Kernel ,byte limitedSelect) { 
    // limitedSelect 参数将 算法的trial选择能力限制在trialtype 参数的选择上，同时使用random的方法来生成 trialcontrast 参数
    float ArgMinValue[5][5]; 
    float min[3]; // min[0] -> min value ; min[1] -> row index ; min[2] -> col index
    // 计算 不同trialtype 下的梯度
    float delta_W[5][5][7];
    float delta_W_Star[7];
    float yhat;

    for(int i=0;i<7;i++){
      delta_W_Star[i] = actionmodel.theta[i] - W_star[i]; // 注意，在计算deltaW和deltaW_Star的时候，主要通过内积来判断相关性和方向一致性；但要注意这两个向量的方向是正确的；
    }
    // iterative calc all the dataset
    // i < j -> left ; i > j -> right
    for(int i=0;i<5;i++){ // Sitmuli 1 -- Sample
      for(int j=0;j<5;j++){ // Stimuli 2 -- Test
        // S0 
        if(i != j){
          data->x[1] = actionmodel.S0[i]; 
          data->x[2] = actionmodel.S0[j];
          // label
          if(i > j){
            data->y    = 1.0; // right 
          }else{
            data->y    = 0.0; // left
          }
          // predicted mouse choice
          yhat = predictFunc(data, 1); // 计算预测值, 预测小鼠的选择
          for(int w=0;w<7;w++){
            delta_W[i][j][w] = (yhat - data->y) * data->x[w];
            delta_W[i][j][w] = delta_W[i][j][w] * float(actionmodel.Eta);
          }
          // calc the argMin value
          float T1 = 0; // difficulty item
          float T2 = 0; // usefulness item
          for(int w = 0;w<7;w++){
            T1 += pow(delta_W[i][j][w] ,2);
            T2 += delta_W[i][j][w] * delta_W_Star[w];
          }
          ArgMinValue[i][j] = pow(actionmodel.Gamma ,2) * T1 * float(Kernel) - 2.0 * actionmodel.Gamma * T2;
        }
      }  
    }

    // argMin  : Min T1 and Max T2 ; 选择更简单的并且更能够align 设定参数的 trialtype
    // TrialType ; TrialTypeContrast
    int limitedContrast = 0;
    float limitedArgMinValue[2];
    if(limitedSelect){
      limitedContrast = int(random(1 ,5)); // 1-4:对应四个最难得contrast stimulus
      limitedArgMinValue[0] = ArgMinValue[limitedContrast][limitedContrast - 1]; // trial type right 2
      limitedArgMinValue[1] = ArgMinValue[limitedContrast - 1][limitedContrast]; // trial type left 1
      if(limitedArgMinValue[0] < limitedArgMinValue[1]){
        TrialType = 2;
        TrialTypeContrast[0] = limitedContrast;
        TrialTypeContrast[1] = limitedContrast - 1;
      }else{
        TrialType = 1;
        TrialTypeContrast[0] = limitedContrast - 1;
        TrialTypeContrast[1] = limitedContrast;
      }
    }else{
      min[0] = ArgMinValue[0][1];
      min[1] = 0;
      min[2] = 1;
      for(int i = 0; i < 5; i++)
        for(int j = 0; j < 5; j++)
          if(i != j)
            if(min[0] > ArgMinValue[i][j]){
              min[0] = ArgMinValue[i][j]; // min
              min[1] = i;  // Stimulus 1
              min[2] = j;  // Stimulus 2
          }
      // output
      if(min[1] < min[2]){
        TrialType = 1; // left
      }else{
        TrialType = 2; // right
      }
      TrialTypeContrast[0] = min[1];
      TrialTypeContrast[1] = min[2];
    }
}


float sgn(float w){
  if(w > 0)
  {
    return 1;
  }
  else if(w < 0)
  {
    return -1;
  }
  else
  {
    return 0;
  }
}

void deepcopymodel(void){
  for(int i=0;i<7;i++){
    actionmodel.theta[i] = model.theta[i];
    actionmodel.m[i] = model.m[i];
  }
  actionmodel.alpha = model.alpha;
  actionmodel.L1 = model.L1;
  actionmodel.Gamma = model.Gamma;
  actionmodel.Eta = model.Eta;
  actionmodel.beta = model.beta;
  actionmodel.t = model.t;
  for(int i=0;i<5;i++){
    actionmodel.S0[i] = model.S0[i];
  }
}



void init(bool file) {
  model=LOGISTIC(); actionmodel=LOGISTIC();
  if(file) model.S0[1]=-.5f;
}
DATAModel datum(int i, int j, int y, int h=0) {
  DATAModel d; d.x[0]=1; d.x[1]=model.S0[i]; d.x[2]=model.S0[j];
  d.x[3]=h; d.x[4]=h; d.x[5]=(h==0)?0:1; d.x[6]=h; d.y=y; return d;
}
int select_after(DATAModel d, int i, int j) {
  UpdateMiceParams(&d,1);
  if(model.t%2==0) deepcopymodel();
  DATAModel next; int s=i>j?1:-1; int a=(2*d.y-1); int r=a*s;
  next.x[0]=1; next.x[3]=s; next.x[4]=a; next.x[5]=r; next.x[6]=a*r;
  SelectTrialType(&next,1,0);
  return 10*TrialTypeContrast[0]+TrialTypeContrast[1];
}
int main() {
  bool f=false;
  for(int i=0;i<5 && !f;i++) for(int j=0;j<5 && !f;j++) if(i!=j)
    for(int y=0;y<2 && !f;y++) for(int h=-1;h<=1 && !f;h++) {
      init(true); auto a=datum(i,j,y,h); int p=select_after(a,i,j);
      init(false); auto b=datum(i,j,y,h); int q=select_after(b,i,j);
      if(p!=q) {printf("{\"initial_file_witness\":{\"trial_indices\":[%d,%d],\"choice_right\":%d,\"synthetic_history\":%d,\"config_next\":[%d,%d],\"fallback_next\":[%d,%d]},",i,j,y,h,p/10,p%10,q/10,q%10); f=true;}
    }
  if(!f) printf("{\"initial_file_witness\":null,");
  bool found=false;
  // Each input sequence is artificial. This is a teacher/source witness,
  // not a fitted biological learning model or forecast.
  for(int n=2;n<=200 && !found;n+=2) {
    init(true);
    for(int t=0;t<n;t++) {
      int i=t%5, j=(t*3+1)%5; if(i==j) j=(j+1)%5;
      auto d=datum(i,j,(t%3==0)?0:1,(t%3)-1);
      UpdateMiceParams(&d,1); if(model.t%2==0) deepcopymodel();
    }
    LOGISTIC before=model, cached=actionmodel;
    for(int i=0;i<5 && !found;i++) for(int j=0;j<5 && !found;j++) if(i!=j)
      for(int y=0;y<2 && !found;y++) {
        model=before; actionmodel=cached; auto d=datum(i,j,y);
        int p=select_after(d,i,j);
        model=before; actionmodel=LOGISTIC();
        // The persisted teacher theta/m use four decimal places on reload.
        for(int k=0;k<7;k++) {
          model.theta[k]=std::round(model.theta[k]*10000)/10000;
          model.m[k]=std::round(model.m[k]*10000)/10000;
        }
        auto e=datum(i,j,y); int q=select_after(e,i,j);
        if(p!=q) {printf("\"cache_restart_witness\":{\"prior_synthetic_updates\":%d,\"next_update_t\":%d,\"trial_indices\":[%d,%d],\"choice_right\":%d,\"uninterrupted_next\":[%d,%d],\"reboot_reload_next\":[%d,%d]}",n,n+1,i,j,y,p/10,p%10,q/10,q%10);found=true;}
      }
  }
  if(!found) printf("\"cache_restart_witness\":null");
  printf(",");
  bool statefound=false;
  const float weights[]={2,3,4,5,6,8,10,.5f,1};
  for(float w:weights) for(int bias=-2;bias<=2 && !statefound;bias++)
    for(int i=0;i<5 && !statefound;i++) for(int j=0;j<5 && !statefound;j++) if(i!=j)
      for(int y=0;y<2 && !statefound;y++) {
        init(true); model.theta[0]=bias; model.theta[1]=w; model.theta[2]=-w; model.t=100;
        deepcopymodel(); LOGISTIC before=model, cached=actionmodel;
        auto d=datum(i,j,y); int p=select_after(d,i,j);
        model=before; actionmodel=LOGISTIC(); auto e=datum(i,j,y); int q=select_after(e,i,j);
        if(p!=q) {printf("\"admissible_state_cache_witness\":{\"initial_theta\":[%g,%g,%g,0,0,0,0],\"prior_t\":100,\"trial_indices\":[%d,%d],\"choice_right\":%d,\"cached_next\":[%d,%d],\"reset_next\":[%d,%d]}",float(bias),w,-w,i,j,y,p/10,p%10,q/10,q%10);statefound=true;}
      }
  if(!statefound) printf("\"admissible_state_cache_witness\":null");
  printf("}\n");
}
