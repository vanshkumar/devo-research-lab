---
dataset_info:
- config_name: exp1
  features:
  - name: task
    dtype: int64
  - name: trial
    dtype: int64
  - name: horizon
    dtype: int64
  - name: uncertainty
    dtype: int64
  - name: slot1_value
    dtype: int64
  - name: slot2_value
    dtype: int64
  - name: choice
    dtype: int64
  - name: RT
    dtype: float64
  - name: reward
    dtype: int64
  - name: forced
    dtype: int64
  - name: participant
    dtype: int64
  splits:
  - name: train
    num_bytes: 6547200
    num_examples: 74400
  download_size: 1067702
  dataset_size: 6547200
- config_name: exp2
  features:
  - name: task
    dtype: int64
  - name: trial
    dtype: int64
  - name: horizon
    dtype: int64
  - name: uncertainty
    dtype: int64
  - name: slot1_value
    dtype: int64
  - name: slot2_value
    dtype: int64
  - name: choice
    dtype: int64
  - name: RT
    dtype: float64
  - name: reward
    dtype: int64
  - name: forced
    dtype: int64
  - name: participant
    dtype: int64
  splits:
  - name: train
    num_bytes: 739200
    num_examples: 8400
  download_size: 125470
  dataset_size: 739200
- config_name: exp3
  features:
  - name: task
    dtype: int64
  - name: trial
    dtype: int64
  - name: horizon
    dtype: int64
  - name: uncertainty
    dtype: int64
  - name: slot1_value
    dtype: int64
  - name: slot2_value
    dtype: int64
  - name: choice
    dtype: int64
  - name: RT
    dtype: float64
  - name: reward
    dtype: int64
  - name: forced
    dtype: int64
  - name: participant
    dtype: int64
  splits:
  - name: train
    num_bytes: 7882160
    num_examples: 89570
  download_size: 1281292
  dataset_size: 7882160
- config_name: exp4
  features:
  - name: task
    dtype: int64
  - name: trial
    dtype: int64
  - name: horizon
    dtype: int64
  - name: uncertainty
    dtype: int64
  - name: slot1_value
    dtype: int64
  - name: slot2_value
    dtype: int64
  - name: choice
    dtype: int64
  - name: RT
    dtype: float64
  - name: reward
    dtype: int64
  - name: forced
    dtype: int64
  - name: participant
    dtype: int64
  splits:
  - name: train
    num_bytes: 9609600
    num_examples: 109200
  download_size: 1571891
  dataset_size: 9609600
- config_name: exp5
  features:
  - name: task
    dtype: int64
  - name: trial
    dtype: int64
  - name: horizon
    dtype: int64
  - name: uncertainty
    dtype: int64
  - name: slot1_value
    dtype: int64
  - name: slot2_value
    dtype: int64
  - name: choice
    dtype: int64
  - name: RT
    dtype: float64
  - name: reward
    dtype: int64
  - name: forced
    dtype: int64
  - name: participant
    dtype: int64
  splits:
  - name: train
    num_bytes: 4752000
    num_examples: 54000
  download_size: 776126
  dataset_size: 4752000
configs:
- config_name: exp1
  data_files:
  - split: train
    path: exp1/train-*
- config_name: exp2
  data_files:
  - split: train
    path: exp2/train-*
- config_name: exp3
  data_files:
  - split: train
    path: exp3/train-*
- config_name: exp4
  data_files:
  - split: train
    path: exp4/train-*
- config_name: exp5
  data_files:
  - split: train
    path: exp5/train-*
---
