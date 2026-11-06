* Encoding: UTF-8.

*analysis acquisition phase*

DATASET ACTIVATE DataSet1.
GLM Acq_CSplus1_1 Acq_CSplus1_2 Acq_CSplus1_3 Acq_CSplus1_4 Acq_CSplus1_5 Acq_CSplus2_1 
    Acq_CSplus2_2 Acq_CSplus2_3 Acq_CSplus2_4 Acq_CSplus2_5 Acq_CSmin_1 Acq_CSmin_2 Acq_CSmin_3 
    Acq_CSmin_4 Acq_CSmin_5 BY Conditie
  /WSFACTOR=CS 3 Polynomial trial 5 Polynomial 
  /METHOD=SSTYPE(3)
  /EMMEANS=TABLES(OVERALL) 
  /EMMEANS=TABLES(Conditie) 
  /EMMEANS=TABLES(CS) 
  /EMMEANS=TABLES(trial) 
  /EMMEANS=TABLES(Conditie*CS) 
  /EMMEANS=TABLES(Conditie*trial) 
  /EMMEANS=TABLES(CS*trial) 
  /EMMEANS=TABLES(Conditie*CS*trial) 
  /PRINT=DESCRIPTIVE ETASQ 
  /CRITERIA=ALPHA(.05)
  /WSDESIGN=CS trial CS*trial
  /DESIGN=Conditie.

*analysis extinction phase*

GLM Ext_CSplus1_1 Ext_CSplus1_2 Ext_CSplus1_3 Ext_CSplus1_4 Ext_CSplus1_5 Ext_CSplus1_6 
    Ext_CSplus2_1 Ext_CSplus2_2 Ext_CSplus2_3 Ext_CSplus2_4 Ext_CSplus2_5 Ext_CSplus2_6 Ext_CSmin_1 
    Ext_CSmin_2 Ext_CSmin_3 Ext_CSmin_4 Ext_CSmin_5 Ext_CSmin_6 BY Conditie
  /WSFACTOR=CS 3 Polynomial trial 6 Polynomial 
  /METHOD=SSTYPE(3)
  /EMMEANS=TABLES(OVERALL) 
  /EMMEANS=TABLES(Conditie) 
  /EMMEANS=TABLES(CS) 
  /EMMEANS=TABLES(trial) 
  /EMMEANS=TABLES(Conditie*CS) 
  /EMMEANS=TABLES(Conditie*trial) 
  /EMMEANS=TABLES(CS*trial) 
  /EMMEANS=TABLES(Conditie*CS*trial) 
  /PRINT=DESCRIPTIVE ETASQ 
  /CRITERIA=ALPHA(.05)
  /WSDESIGN=CS trial CS*trial
  /DESIGN=Conditie.

*analysis reinstatement*

GLM Ext_CSmin_6 Ri_CSmin_1 Ext_CSplus2_6 Ri_CSplus2_1 BY Conditie
  /WSFACTOR=CS 2 Polynomial phase 2 Polynomial 
  /METHOD=SSTYPE(3)
  /EMMEANS=TABLES(OVERALL) 
  /EMMEANS=TABLES(Conditie) 
  /EMMEANS=TABLES(CS) 
  /EMMEANS=TABLES(Conditie*CS) 
  /PRINT=DESCRIPTIVE ETASQ 
  /CRITERIA=ALPHA(.05)
  /WSDESIGN=CS phase CS*phase
  /DESIGN=Conditie.

*analysis excluding participants who did not think that the two CSs were equivalent*

USE ALL.
COMPUTE filter_$=(Question2 <= 2).
VARIABLE LABELS filter_$ 'Question2 <= 2 (FILTER)'.
VALUE LABELS filter_$ 0 'Not Selected' 1 'Selected'.
FORMATS filter_$ (f1.0).
FILTER BY filter_$.
EXECUTE.


GLM Ext_CSmin_6 Ri_CSmin_1 Ext_CSplus2_6 Ri_CSplus2_1 BY Conditie
  /WSFACTOR=CS 2 Polynomial phase 2 Polynomial 
  /METHOD=SSTYPE(3)
  /EMMEANS=TABLES(OVERALL) 
  /EMMEANS=TABLES(Conditie) 
  /EMMEANS=TABLES(CS) 
  /EMMEANS=TABLES(Conditie*CS) 
  /PRINT=DESCRIPTIVE ETASQ 
  /CRITERIA=ALPHA(.05)
  /WSDESIGN=CS phase CS*phase
  /DESIGN=Conditie.


