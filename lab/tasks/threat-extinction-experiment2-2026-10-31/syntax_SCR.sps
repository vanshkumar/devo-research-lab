* Encoding: UTF-8.

*Rescale to microS*

DATASET ACTIVATE DataSet1.
COMPUTE CSplus1_1=GSR1CSplus1_1 / 1000.
EXECUTE.
COMPUTE CSplus1_2=GSR1CSplus1_2 / 1000.
EXECUTE.
COMPUTE CSplus1_3=GSR1CSplus1_3 / 1000.
EXECUTE.
COMPUTE CSplus1_4=GSR1CSplus1_4 / 1000.
EXECUTE.
COMPUTE CSplus1_5=GSR1CSplus1_5 / 1000.
EXECUTE.
COMPUTE CSplus1_6=GSR1CSplus1_6 / 1000.
EXECUTE.
COMPUTE CSplus1_7=GSR1CSplus1_7 / 1000.
EXECUTE.
COMPUTE CSplus1_8=GSR1CSplus1_8 / 1000.
EXECUTE.
COMPUTE CSplus1_9=GSR1CSplus1_9 / 1000.
EXECUTE.
COMPUTE CSplus1_10=GSR1CSplus1_10 / 1000.
EXECUTE.
COMPUTE CSplus1_11=GSR1CSplus1_11 / 1000.
EXECUTE.
COMPUTE CSplus1_12=GSR1CSplus1_12 / 1000.
EXECUTE.
COMPUTE CSplus1_13=GSR1CSplus1_13 / 1000.
EXECUTE.

COMPUTE CSplus2_1=GSR1CSplus2_1 / 1000.
EXECUTE.
COMPUTE CSplus2_2=GSR1CSplus2_2 / 1000.
EXECUTE.
COMPUTE CSplus2_3=GSR1CSplus2_3 / 1000.
EXECUTE.
COMPUTE CSplus2_4=GSR1CSplus2_4 / 1000.
EXECUTE.
COMPUTE CSplus2_5=GSR1CSplus2_5 / 1000.
EXECUTE.
COMPUTE CSplus2_6=GSR1CSplus2_6 / 1000.
EXECUTE.
COMPUTE CSplus2_7=GSR1CSplus2_7 / 1000.
EXECUTE.
COMPUTE CSplus2_8=GSR1CSplus2_8 / 1000.
EXECUTE.
COMPUTE CSplus2_9=GSR1CSplus2_9 / 1000.
EXECUTE.
COMPUTE CSplus2_10=GSR1CSplus2_10 / 1000.
EXECUTE.
COMPUTE CSplus2_11=GSR1CSplus2_11 / 1000.
EXECUTE.
COMPUTE CSplus2_12=GSR1CSplus2_12 / 1000.
EXECUTE.
COMPUTE CSplus2_13=GSR1CSplus2_13 / 1000.
EXECUTE.
COMPUTE CSplus2_14=GSR1CSplus2_14 / 1000.
EXECUTE.

COMPUTE CSmin_1=GSR1CSmin_1 / 1000.
EXECUTE.
COMPUTE CSmin_2=GSR1CSmin_2 / 1000.
EXECUTE.
COMPUTE CSmin_3=GSR1CSmin_3 / 1000.
EXECUTE.
COMPUTE CSmin_4=GSR1CSmin_4 / 1000.
EXECUTE.
COMPUTE CSmin_5=GSR1CSmin_5 / 1000.
EXECUTE.
COMPUTE CSmin_6=GSR1CSmin_6 / 1000.
EXECUTE.
COMPUTE CSmin_7=GSR1CSmin_7 / 1000.
EXECUTE.
COMPUTE CSmin_8=GSR1CSmin_8 / 1000.
EXECUTE.
COMPUTE CSmin_9=GSR1CSmin_9 / 1000.
EXECUTE.
COMPUTE CSmin_10=GSR1CSmin_10 / 1000.
EXECUTE.
COMPUTE CSmin_11=GSR1CSmin_11 / 1000.
EXECUTE.
COMPUTE CSmin_12=GSR1CSmin_12 / 1000.
EXECUTE.
COMPUTE CSmin_13=GSR1CSmin_13 / 1000.
EXECUTE.
COMPUTE CSmin_14=GSR1CSmin_14 / 1000.
EXECUTE.

COMPUTE US_1=GSR1US_1 / 1000.
EXECUTE.
COMPUTE US_2=GSR1US_2 / 1000.
EXECUTE.
COMPUTE US_3=GSR1US_3 / 1000.
EXECUTE.
COMPUTE US_4=GSR1US_4 / 1000.
EXECUTE.
COMPUTE US_5=GSR1US_5 / 1000.
EXECUTE.
COMPUTE US_6=GSR1US_6 / 1000.
EXECUTE.
COMPUTE US_7=GSR1US_7 / 1000.
EXECUTE.
COMPUTE US_8=GSR1US_8 / 1000.
EXECUTE.
COMPUTE US_9=GSR1US_9 / 1000.
EXECUTE.
COMPUTE US_10=GSR1US_10 / 1000.
EXECUTE.
COMPUTE US_11=GSR1US_11 / 1000.
EXECUTE.
COMPUTE US_12=GSR1US_12 / 1000.
EXECUTE.
COMPUTE US_13=GSR1US_13 / 1000.
EXECUTE.



*Response criterium = 0,02*

RECODE CSplus1_1, CSplus1_2, CSplus1_3, CSplus1_4, CSplus1_5, CSplus1_6, CSplus1_7, CSplus1_8, CSplus1_9, CSplus1_10, CSplus1_11, CSplus1_12, CSplus1_13, 
CSplus2_1, CSplus2_2, CSplus2_3, CSplus2_4, CSplus2_5, CSplus2_6, CSplus2_7, CSplus2_8, CSplus2_9, CSplus2_10, CSplus2_11, CSplus2_12, CSplus2_13, CSplus2_14, 
CSmin_1, CSmin_2, CSmin_3, CSmin_4, CSmin_5, CSmin_6, CSmin_7, CSmin_8, CSmin_9, CSmin_10, CSmin_11, CSmin_12, CSmin_13, CSmin_14,
US_1, US_2, US_3, US_4, US_5, US_6, US_7, US_8, US_9, US_10, US_11, US_12, US_13
(Lowest thru 0.02=0).
EXECUTE.

*COMPUTE MAX*

COMPUTE SCR_max=MAX(CSplus1_1, CSplus1_2, CSplus1_3, CSplus1_4, CSplus1_5, CSplus1_6, CSplus1_7, CSplus1_8, CSplus1_9, CSplus1_10, CSplus1_11, CSplus1_12, CSplus1_13, 
CSplus2_1, CSplus2_2, CSplus2_3, CSplus2_4, CSplus2_5, CSplus2_6, CSplus2_7, CSplus2_8, CSplus2_9, CSplus2_10, CSplus2_11, CSplus2_12, CSplus2_13, CSplus2_14, 
CSmin_1, CSmin_2, CSmin_3, CSmin_4, CSmin_5, CSmin_6, CSmin_7, CSmin_8, CSmin_9, CSmin_10, CSmin_11, CSmin_12, CSmin_13, CSmin_14).
EXECUTE.

*zero & missings count*

COUNT zerocount=CSplus1_1, CSplus1_2, CSplus1_3, CSplus1_4, CSplus1_5, CSplus1_6, CSplus1_7, CSplus1_8, CSplus1_9, CSplus1_10, CSplus1_11, CSplus1_12, CSplus1_13, 
CSplus2_1, CSplus2_2, CSplus2_3, CSplus2_4, CSplus2_5, CSplus2_6, CSplus2_7, CSplus2_8, CSplus2_9, CSplus2_10, CSplus2_11, CSplus2_12, CSplus2_13, CSplus2_14, 
CSmin_1, CSmin_2, CSmin_3, CSmin_4, CSmin_5, CSmin_6, CSmin_7, CSmin_8, CSmin_9, CSmin_10, CSmin_11, CSmin_12, CSmin_13, CSmin_14(0). 
EXECUTE.


*Range Correction*

COMPUTE Range_CSplus1_1 = CSplus1_1/SCR_max.
EXECUTE.
COMPUTE Range_CSplus1_2 = CSplus1_2/SCR_max.
EXECUTE.
COMPUTE Range_CSplus1_3 = CSplus1_3/SCR_max.
EXECUTE.
COMPUTE Range_CSplus1_4 = CSplus1_4/SCR_max.
EXECUTE.
COMPUTE Range_CSplus1_5 = CSplus1_5/SCR_max.
EXECUTE.
COMPUTE Range_CSplus1_6 = CSplus1_6/SCR_max.
EXECUTE.
COMPUTE Range_CSplus1_7 = CSplus1_7/SCR_max.
EXECUTE.
COMPUTE Range_CSplus1_8 = CSplus1_8/SCR_max.
EXECUTE.
COMPUTE Range_CSplus1_9 = CSplus1_9/SCR_max.
EXECUTE.
COMPUTE Range_CSplus1_10 = CSplus1_10/SCR_max.
EXECUTE.
COMPUTE Range_CSplus1_11 = CSplus1_11/SCR_max.
EXECUTE.
COMPUTE Range_CSplus1_12 = CSplus1_12/SCR_max.
EXECUTE.
COMPUTE Range_CSplus1_13 = CSplus1_13/SCR_max.
EXECUTE.

COMPUTE Range_CSplus2_1 = CSplus2_1/SCR_max.
EXECUTE.
COMPUTE Range_CSplus2_2 = CSplus2_2/SCR_max.
EXECUTE.
COMPUTE Range_CSplus2_3 = CSplus2_3/SCR_max.
EXECUTE.
COMPUTE Range_CSplus2_4 = CSplus2_4/SCR_max.
EXECUTE.
COMPUTE Range_CSplus2_5 = CSplus2_5/SCR_max.
EXECUTE.
COMPUTE Range_CSplus2_6 = CSplus2_6/SCR_max.
EXECUTE.
COMPUTE Range_CSplus2_7 = CSplus2_7/SCR_max.
EXECUTE.
COMPUTE Range_CSplus2_8 = CSplus2_8/SCR_max.
EXECUTE.
COMPUTE Range_CSplus2_9 = CSplus2_9/SCR_max.
EXECUTE.
COMPUTE Range_CSplus2_10 = CSplus2_10/SCR_max.
EXECUTE.
COMPUTE Range_CSplus2_11 = CSplus2_11/SCR_max.
EXECUTE.
COMPUTE Range_CSplus2_12 = CSplus2_12/SCR_max.
EXECUTE.
COMPUTE Range_CSplus2_13 = CSplus2_13/SCR_max.
EXECUTE.
COMPUTE Range_CSplus2_14 = CSplus2_14/SCR_max.
EXECUTE.

COMPUTE Range_CSmin_1 = CSmin_1/SCR_max.
EXECUTE.
COMPUTE Range_CSmin_2 = CSmin_2/SCR_max.
EXECUTE.
COMPUTE Range_CSmin_3 = CSmin_3/SCR_max.
EXECUTE.
COMPUTE Range_CSmin_4 = CSmin_4/SCR_max.
EXECUTE.
COMPUTE Range_CSmin_5 = CSmin_5/SCR_max.
EXECUTE.
COMPUTE Range_CSmin_6 = CSmin_6/SCR_max.
EXECUTE.
COMPUTE Range_CSmin_7 = CSmin_7/SCR_max.
EXECUTE.
COMPUTE Range_CSmin_8 = CSmin_8/SCR_max.
EXECUTE.
COMPUTE Range_CSmin_9 = CSmin_9/SCR_max.
EXECUTE.
COMPUTE Range_CSmin_10 = CSmin_10/SCR_max.
EXECUTE.
COMPUTE Range_CSmin_11 = CSmin_11/SCR_max.
EXECUTE.
COMPUTE Range_CSmin_12 = CSmin_12/SCR_max.
EXECUTE.
COMPUTE Range_CSmin_13 = CSmin_13/SCR_max.
EXECUTE.
COMPUTE Range_CSmin_14 = CSmin_14/SCR_max.
EXECUTE.



*Square root transformation*

COMPUTE SQRT_CSplus1_1 = SQRT(Range_CSplus1_1).
EXECUTE.
COMPUTE SQRT_CSplus1_2 = SQRT(Range_CSplus1_2).
EXECUTE.
COMPUTE SQRT_CSplus1_3 = SQRT(Range_CSplus1_3).
EXECUTE.
COMPUTE SQRT_CSplus1_4 = SQRT(Range_CSplus1_4).
EXECUTE.
COMPUTE SQRT_CSplus1_5 = SQRT(Range_CSplus1_5).
EXECUTE.
COMPUTE SQRT_CSplus1_6 = SQRT(Range_CSplus1_6).
EXECUTE.
COMPUTE SQRT_CSplus1_7 = SQRT(Range_CSplus1_7).
EXECUTE.
COMPUTE SQRT_CSplus1_8 = SQRT(Range_CSplus1_8).
EXECUTE.
COMPUTE SQRT_CSplus1_9 = SQRT(Range_CSplus1_9).
EXECUTE.
COMPUTE SQRT_CSplus1_10 = SQRT(Range_CSplus1_10).
EXECUTE.
COMPUTE SQRT_CSplus1_11 = SQRT(Range_CSplus1_11).
EXECUTE.
COMPUTE SQRT_CSplus1_12 = SQRT(Range_CSplus1_12).
EXECUTE.
COMPUTE SQRT_CSplus1_13 = SQRT(Range_CSplus1_13).
EXECUTE.

COMPUTE SQRT_CSplus2_1 = SQRT(Range_CSplus2_1).
EXECUTE.
COMPUTE SQRT_CSplus2_2 = SQRT(Range_CSplus2_2).
EXECUTE.
COMPUTE SQRT_CSplus2_3 = SQRT(Range_CSplus2_3).
EXECUTE.
COMPUTE SQRT_CSplus2_4 = SQRT(Range_CSplus2_4).
EXECUTE.
COMPUTE SQRT_CSplus2_5 = SQRT(Range_CSplus2_5).
EXECUTE.
COMPUTE SQRT_CSplus2_6 = SQRT(Range_CSplus2_6).
EXECUTE.
COMPUTE SQRT_CSplus2_7 = SQRT(Range_CSplus2_7).
EXECUTE.
COMPUTE SQRT_CSplus2_8 = SQRT(Range_CSplus2_8).
EXECUTE.
COMPUTE SQRT_CSplus2_9 = SQRT(Range_CSplus2_9).
EXECUTE.
COMPUTE SQRT_CSplus2_10 = SQRT(Range_CSplus2_10).
EXECUTE.
COMPUTE SQRT_CSplus2_11 = SQRT(Range_CSplus2_11).
EXECUTE.
COMPUTE SQRT_CSplus2_12 = SQRT(Range_CSplus2_12).
EXECUTE.
COMPUTE SQRT_CSplus2_13 = SQRT(Range_CSplus2_13).
EXECUTE.
COMPUTE SQRT_CSplus2_14 = SQRT(Range_CSplus2_14).
EXECUTE.

COMPUTE SQRT_CSmin_1 = SQRT(Range_CSmin_1).
EXECUTE.
COMPUTE SQRT_CSmin_2 = SQRT(Range_CSmin_2).
EXECUTE.
COMPUTE SQRT_CSmin_3 = SQRT(Range_CSmin_3).
EXECUTE.
COMPUTE SQRT_CSmin_4 = SQRT(Range_CSmin_4).
EXECUTE.
COMPUTE SQRT_CSmin_5 = SQRT(Range_CSmin_5).
EXECUTE.
COMPUTE SQRT_CSmin_6 = SQRT(Range_CSmin_6).
EXECUTE.
COMPUTE SQRT_CSmin_7 = SQRT(Range_CSmin_7).
EXECUTE.
COMPUTE SQRT_CSmin_8 = SQRT(Range_CSmin_8).
EXECUTE.
COMPUTE SQRT_CSmin_9 = SQRT(Range_CSmin_9).
EXECUTE.
COMPUTE SQRT_CSmin_10 = SQRT(Range_CSmin_10).
EXECUTE.
COMPUTE SQRT_CSmin_11 = SQRT(Range_CSmin_11).
EXECUTE.
COMPUTE SQRT_CSmin_12 = SQRT(Range_CSmin_12).
EXECUTE.
COMPUTE SQRT_CSmin_13 = SQRT(Range_CSmin_13).
EXECUTE.
COMPUTE SQRT_CSmin_14 = SQRT(Range_CSmin_14).
EXECUTE.


*Means different CSs acquisition phase*

COMPUTE Mean_CS1_acq=MEAN(SQRT_CSplus1_1,SQRT_CSplus1_2,SQRT_CSplus1_3,SQRT_CSplus1_4,
    SQRT_CSplus1_5).
EXECUTE.

COMPUTE Mean_CS2_acq=MEAN(SQRT_CSplus2_1,SQRT_CSplus2_2,SQRT_CSplus2_3,SQRT_CSplus2_4,
    SQRT_CSplus2_5).
EXECUTE.

COMPUTE Mean_CSmin_acq=MEAN(SQRT_CSmin_1,SQRT_CSmin_2,SQRT_CSmin_3,SQRT_CSmin_4,
    SQRT_CSmin_5).
EXECUTE.

*Difference CS2/CSmin reinstatement analysis*

DATASET ACTIVATE DataSet2.
COMPUTE Average_CS2_reinstatement=MEAN(SQRT_CSplus2_11,SQRT_CSplus2_12).
EXECUTE.

COMPUTE Average_CSmin_reinstatement=MEAN(SQRT_CSmin_11,SQRT_CSmin_12).
EXECUTE.

COMPUTE Average_End_Extinction =MEAN(SQRT_CSplus2_11,SQRT_CSmin_11).
EXECUTE.

COMPUTE Average_Start_Reinstatement =MEAN(SQRT_CSplus2_12,SQRT_CSmin_12).
EXECUTE.


COMPUTE Difference_CS2reinst_CSminreinst=Average_CS2_reinstatement - Average_CSmin_reinstatement.
EXECUTE.

COMPUTE Difference_EndExt_StartReinst=Average_Start_Reinstatement - Average_End_Extinction.
EXECUTE.


*analysis acquisition phase*

DATASET ACTIVATE DataSet1.
GLM SQRT_CSplus1_1 SQRT_CSplus1_2 SQRT_CSplus1_3 SQRT_CSplus1_4 SQRT_CSplus1_5 SQRT_CSplus2_1 
    SQRT_CSplus2_2 SQRT_CSplus2_3 SQRT_CSplus2_4 SQRT_CSplus2_5 SQRT_CSmin_1 SQRT_CSmin_2 SQRT_CSmin_3 
    SQRT_CSmin_4 SQRT_CSmin_5 BY Conditie
  /WSFACTOR=CS 3 Polynomial trial 5 Polynomial 
  /METHOD=SSTYPE(3)
  /EMMEANS=TABLES(OVERALL) 
  /EMMEANS=TABLES(CS) 
  /EMMEANS=TABLES(trial) 
  /EMMEANS=TABLES(CS*trial) 
  /EMMEANS=TABLES(Conditie) 
  /EMMEANS=TABLES(Conditie*CS) 
  /EMMEANS=TABLES(Conditie*trial) 
  /EMMEANS=TABLES(Conditie*CS*trial) 
  /PRINT=DESCRIPTIVE ETASQ 
  /CRITERIA=ALPHA(.05)
  /WSDESIGN=CS trial CS*trial
  /DESIGN=Conditie.

*analysis extinction phase*

GLM SQRT_CSplus1_6 SQRT_CSplus1_7 SQRT_CSplus1_8 SQRT_CSplus1_9 SQRT_CSplus1_10 SQRT_CSplus1_11 
    SQRT_CSplus2_6 SQRT_CSplus2_7 SQRT_CSplus2_8 SQRT_CSplus2_9 SQRT_CSplus2_10 SQRT_CSplus2_11 
    SQRT_CSmin_6 SQRT_CSmin_7 SQRT_CSmin_8 SQRT_CSmin_9 SQRT_CSmin_10 SQRT_CSmin_11 BY Conditie
  /WSFACTOR=CS 3 Polynomial trial 6 Polynomial 
  /METHOD=SSTYPE(3)
  /EMMEANS=TABLES(OVERALL) 
  /EMMEANS=TABLES(CS) 
  /EMMEANS=TABLES(trial) 
  /EMMEANS=TABLES(CS*trial) 
  /EMMEANS=TABLES(Conditie) 
  /EMMEANS=TABLES(Conditie*CS) 
  /EMMEANS=TABLES(Conditie*trial) 
  /EMMEANS=TABLES(Conditie*CS*trial) 
  /PRINT=DESCRIPTIVE ETASQ 
  /CRITERIA=ALPHA(.05)
  /WSDESIGN=CS trial CS*trial
  /DESIGN=Conditie.

*analysis reinstatement phase*

GLM SQRT_CSplus2_11 SQRT_CSplus2_12 SQRT_CSmin_11 SQRT_CSmin_12 BY Conditie
  /WSFACTOR=CS 2 Polynomial Phase 2 Polynomial 
  /METHOD=SSTYPE(3)
  /EMMEANS=TABLES(OVERALL) 
  /EMMEANS=TABLES(CS) 
  /EMMEANS=TABLES(Conditie) 
  /EMMEANS=TABLES(Conditie*CS) 
  /EMMEANS=TABLES(Phase) 
  /EMMEANS=TABLES(Conditie*Phase) 
  /EMMEANS=TABLES(CS*Phase) 
  /EMMEANS=TABLES(Conditie*CS*Phase) 
  /PRINT=DESCRIPTIVE ETASQ 
  /CRITERIA=ALPHA(.05)
  /WSDESIGN=CS Phase CS*Phase
  /DESIGN=Conditie.

*analysis reinstatement phase excluding participants who did not think the CSs were equivalent*

USE ALL.
COMPUTE filter_$=(Question2 <= 2).
VARIABLE LABELS filter_$ 'Question2 <= 2 (FILTER)'.
VALUE LABELS filter_$ 0 'Not Selected' 1 'Selected'.
FORMATS filter_$ (f1.0).
FILTER BY filter_$.
EXECUTE.

GLM SQRT_CSplus2_11 SQRT_CSplus2_12 SQRT_CSmin_11 SQRT_CSmin_12 BY Conditie
  /WSFACTOR=CS 2 Polynomial Phase 2 Polynomial 
  /METHOD=SSTYPE(3)
  /EMMEANS=TABLES(OVERALL) 
  /EMMEANS=TABLES(CS) 
  /EMMEANS=TABLES(Conditie) 
  /EMMEANS=TABLES(Conditie*CS) 
  /EMMEANS=TABLES(Phase) 
  /EMMEANS=TABLES(Conditie*Phase) 
  /EMMEANS=TABLES(CS*Phase) 
  /EMMEANS=TABLES(Conditie*CS*Phase) 
  /PRINT=DESCRIPTIVE ETASQ 
  /CRITERIA=ALPHA(.05)
  /WSDESIGN=CS Phase CS*Phase
  /DESIGN=Conditie.

*follow up reinstatement in control condition*

USE ALL.
COMPUTE filter_$=(Question2 <= 2 & Conditie = 'Control').
VARIABLE LABELS filter_$ "Question2 <= 2 & Conditie = 'Control' (FILTER)".
VALUE LABELS filter_$ 0 'Not Selected' 1 'Selected'.
FORMATS filter_$ (f1.0).
FILTER BY filter_$.
EXECUTE.

GLM SQRT_CSplus2_11 SQRT_CSplus2_12 SQRT_CSmin_11 SQRT_CSmin_12
  /WSFACTOR=CS 2 Polynomial Phase 2 Polynomial 
  /METHOD=SSTYPE(3)
  /EMMEANS=TABLES(OVERALL) 
  /EMMEANS=TABLES(CS) 
  /EMMEANS=TABLES(Phase) 
  /EMMEANS=TABLES(CS*Phase) 
  /PRINT=DESCRIPTIVE ETASQ 
  /CRITERIA=ALPHA(.05)
  /WSDESIGN=CS Phase CS*Phase.

*follow up reinstatement in SE condition (excluding participants who did not think the CSs were equivalent)*

USE ALL.
COMPUTE filter_$=(Question2 <= 2 & Conditie = 'SE').
VARIABLE LABELS filter_$ "Question2 <= 2 & Conditie = 'SE' (FILTER)".
VALUE LABELS filter_$ 0 'Not Selected' 1 'Selected'.
FORMATS filter_$ (f1.0).
FILTER BY filter_$.
EXECUTE.

GLM SQRT_CSplus2_11 SQRT_CSplus2_12 SQRT_CSmin_11 SQRT_CSmin_12
  /WSFACTOR=CS 2 Polynomial Phase 2 Polynomial 
  /METHOD=SSTYPE(3)
  /EMMEANS=TABLES(OVERALL) 
  /EMMEANS=TABLES(CS) 
  /EMMEANS=TABLES(Phase) 
  /EMMEANS=TABLES(CS*Phase) 
  /PRINT=DESCRIPTIVE ETASQ 
  /CRITERIA=ALPHA(.05)
  /WSDESIGN=CS Phase CS*Phase.

*analysis reinstatement phase excluding participants who did think the CSs were equivalent*

USE ALL.
COMPUTE filter_$=(Question2 = 0  | Question2 = 2  | Question2 = 3).
VARIABLE LABELS filter_$ 'Question2 = 0  | Question2 = 2  | Question2 = 3 (FILTER)'.
VALUE LABELS filter_$ 0 'Not Selected' 1 'Selected'.
FORMATS filter_$ (f1.0).
FILTER BY filter_$.
EXECUTE.

GLM SQRT_CSplus2_11 SQRT_CSplus2_12 SQRT_CSmin_11 SQRT_CSmin_12 BY Conditie
  /WSFACTOR=CS 2 Polynomial Phase 2 Polynomial 
  /METHOD=SSTYPE(3)
  /EMMEANS=TABLES(OVERALL) 
  /EMMEANS=TABLES(CS) 
  /EMMEANS=TABLES(Phase) 
  /EMMEANS=TABLES(CS*Phase) 
  /EMMEANS=TABLES(Conditie) 
  /EMMEANS=TABLES(Conditie*CS) 
  /EMMEANS=TABLES(Conditie*Phase) 
  /EMMEANS=TABLES(Conditie*CS*Phase) 
  /PRINT=DESCRIPTIVE ETASQ 
  /CRITERIA=ALPHA(.05)
  /WSDESIGN=CS Phase CS*Phase
  /DESIGN=Conditie.
