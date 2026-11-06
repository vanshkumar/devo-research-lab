## task_generate.source
function taskData = GenerateOutcomes(taskParam, vola, sig, condition)
% This funtion generates the outcomes of the task.
%   The outcomes that are centerend around the mean of a normal
%   distribution (distMean) with standard deviation = sigma.
%   All other variables are preallocated.
% 
%   This function uses code from Matt Nassar (Brown University). Thanks Matt!

if isequal(condition, 'main') || isequal(condition, 'oddball')
    trials = taskParam.gParam.trials;
elseif isequal(condition, 'practice') || isequal(condition, 'practiceNoOddball') || isequal(condition, 'practiceOddball')
    trials = taskParam.gParam.practTrials;
elseif isequal(condition, 'shield')
    trials = taskParam.gParam.shieldTrials;
elseif isequal(condition, 'practiceCont')
    trials = taskParam.gParam.practContTrials;
elseif isequal(condition, 'control')
    trials = taskParam.gParam.contTrials;
end

% Preallocate variables.
fieldNames = taskParam.fieldNames;
ID = cell(trials, 1); % ID.
age = zeros(trials, 1); % Age.
sex = cell(trials, 1); % Sex.
rew = nan(trials, 1); % Reward.
actRew = nan(trials,1); % Actual reward.
Date = cell(trials, 1); % Date.
cond = cell(trials, 1); % Condition.
outcome=nan(trials, 1); % Outcome.
distMean=nan(trials, 1); % Distribution mean.
cp=zeros(trials, 1); % Change point.
TAC=nan(trials, 1); % Trials after change-point.
boatType = zeros(trials, 1); % Boat type.
catchTrial = zeros(trials, 1); % Catch trial.
predT = zeros(trials, 1); % Trigger: prediction.
outT = zeros(trials, 1); % Trigger: outcome.
triggers = zeros(trials, 7); % Trigger: boat.
pred = zeros(trials, 1); % Prediction of participant.
predErr = nan(trials, 1); % Prediction error.
predErrNorm = zeros(trials, 1);% Regular prediction error.
predErrPlus = zeros(trials, 1); %Prediction error plus 360 degrees.
predErrMin = zeros(trials, 1); % Prediction error minus 360 degrees.
memErr = zeros(trials, 1);% Memory error.
memErrNorm = zeros(trials, 1);% Regular memory error.
memErrPlus = zeros(trials, 1); % Memory error plus 360 degrees.
memErrMin = zeros(trials, 1); % Memory error minus 360 degrees.
UP = zeros(trials, 1); % Update of participant.
UPNorm = zeros(trials, 1);% Regular prediction error.
UPPlus = zeros(trials, 1); %Prediction error plus 360 degrees.
UPMin = zeros(trials, 1); % Prediction error minus 360 degrees.
hit = zeros(trials, 1); % Hit.
cBal = nan(trials, 1); % Counterbalancing.
s=taskParam.gParam.safe; % how many guaranteed trials before change-point.
perf = zeros(trials, 1); % Performance.
accPerf = zeros(trials, 1); % Accumulated performance.
timestampOnset = nan(trials,1);
timestampPrediction = nan(trials,1);
timestampOffset = nan(trials, 1);
initiationRT = nan(trials,1);
block = nan(trials,1);
actJitter = nan(trials,1);
%% generateOutcomes (by Matt Nassar)

%rng('shuffle')
a = clock;
rand('twister', a(6).*10000);

% Angular shield size:
UorExp=0;
mu=15; % for CP = 15
minASS = 10;
maxASS=180;
allASS = zeros(trials,1);

if isequal(condition, 'main') || isequal(condition, 'practice') || isequal(condition, 'shield')%taskParam.gParam.oddball == false || isequal(type, 'Main')
for i = 1:trials
    
    % blocknumber
    if i >= taskParam.gParam.blockIndices(1) && i <= taskParam.gParam.blockIndices(2) 
            block(i) = 1;
        elseif i >= taskParam.gParam.blockIndices(2) && i <= taskParam.gParam.blockIndices(3)
            block(i) = 2;
        elseif i >= taskParam.gParam.blockIndices(3) && i <= taskParam.gParam.blockIndices(4)
            block(i) = 3;
        elseif i >= taskParam.gParam.blockIndices(4)
            block(i) = 4;
    end 
    
    if (rand < vola && s==0) || i == taskParam.gParam.blockIndices(1) || i == taskParam.gParam.blockIndices(2) + 1 || i == taskParam.gParam.blockIndices(3) + 1 || i == taskParam.gParam.blockIndices(4) + 1 %% new mean for every block!
        mean=round(rand(1).*359); % Outcome expressed in degrees.
        cp(i)=1;
        s=taskParam.gParam.safe;
        TAC(i)=0; %TAC(i)=1;
    else
        TAC(i)=TAC(i-1)+1;
        s=max([s-1, 0]);
    end
    %outcome(i) = 90
    
    outcome(i)=round(180+rad2deg(circ_vmrnd(deg2rad(mean-180), sig, 1)));
    %outcome(i)=round(normrnd(mean, sig));
    distMean(i)=mean;
    oddBall(i) = nan;
    
    %CatchTrial
    if rand(1) <= 0.00
        catchTrial(i) = 1;
    else
        catchTrial(i) = 0;
    end
    ASS=nan;

    while ~isfinite(ASS)|| ASS<minASS || ASS>maxASS
    ASS=exprnd(mu);
    end
    allASS(i)=ASS;
end


elseif isequal(condition, 'oddball') || isequal(condition, 'practiceNoOddball') || isequal(condition, 'practiceOddball')
  
distMean=nan(trials,1);
oddBall=false(trials,1);
outcome=nan(trials,1);
if isequal(condition, 'shield')
    driftConc = taskParam.gParam.driftConc(2);
else
    driftConc = taskParam.gParam.driftConc(1);
end

s = 0;
mu=10; % for ODDBALL = 10

for i =1:trials
   
        % blocknumber
    if i >= taskParam.gParam.blockIndices(1) && i <= taskParam.gParam.blockIndices(2) 
            block(i) = 1;
        elseif i >= taskParam.gParam.blockIndices(2) && i <= taskParam.gParam.blockIndices(3)
            block(i) = 2;
        elseif i >= taskParam.gParam.blockIndices(3) && i <= taskParam.gParam.blockIndices(4)
            block(i) = 3;
        elseif i >= taskParam.gParam.blockIndices(4)
            block(i) = 4;
    end 
    
    if i == taskParam.gParam.blockIndices(1) || i == taskParam.gParam.blockIndices(2) + 1 || i == taskParam.gParam.blockIndices(3) + 1 || i == taskParam.gParam.blockIndices(4) + 1 %% new mean for every block 
        muRad_offset=unifrnd(-pi, pi);
    else
        muRad_offset= deg2rad(distMean(i-1)-180)+circ_vmrnd(0, driftConc, 1);
    end
        muRad_offset=circ_dist(muRad_offset, 0);
        distMean(i)=rad2deg(muRad_offset)+180;

    if isequal(condition, 'practiceNoOddball') || isequal(condition, 'shield')
        oddballProb = taskParam.gParam.oddballProb(2);
    elseif isequal(condition, 'practiceOddball') || isequal(condition, 'practice') || isequal(condition, 'main') || isequal(condition, 'oddball') 
        oddballProb = taskParam.gParam.oddballProb(1);
    end
    
    if rand<oddballProb && s==0
        outcome(i)=round(rand.*359);
        oddBall(i)=true;
        TAC(i)=0; %TAC(i)=1;
        s=taskParam.gParam.safe;
    else
        if i==1
            TAC(i)=nan;
        else
            TAC(i)=TAC(i-1)+1;
        end
        outcome(i)= round(rad2deg(circ_vmrnd(deg2rad(distMean(i)-180), sig, 1))+180); %taskParam.gParam.driftConc
        s=max([s-1, 0]);
    end
    cp(i) = nan;
    
    
    ASS=nan;

    while ~isfinite(ASS)|| ASS<minASS || ASS>maxASS
    ASS=exprnd(mu);
    end
    allASS(i)=ASS.*2;
end




    
    
    
end

%%%%%%%%
% Angular shield size:
% UorExp=0
% mu=20;
% minASS = 10;
% maxASS=180;
% allASS = zeros(trials,1);

% for i = 1:trials
% 
% ASS=nan;
% 
% while ~isfinite(ASS)|| ASS<minASS || ASS>maxASS
% ASS=exprnd(mu);
% end
% allASS(i)=ASS;
% 
% end

%%%%%%%%%%%%%
    % Boat type.
    if trials > 1
    boatType = Shuffle([zeros((trials/2),1); ones((trials/2),1)]);
    else boatType = 1;
    end
%% Save data.
taskData = struct(fieldNames.actJitter, actJitter, fieldNames.block, block, fieldNames.initiationRTs, initiationRT, fieldNames.timestampOnset, timestampOnset, fieldNames.timestampPrediction, timestampPrediction, fieldNames.timestampOffset, timestampOffset, fieldNames.oddBall, oddBall, fieldNames.allASS, allASS, fieldNames.ID, {ID}, fieldNames.age, {age}, fieldNames.rew, {rew}, fieldNames.actRew, actRew, fieldNames.sex, {sex}, fieldNames.cond, {cond}, fieldNames.trial, i,...
    fieldNames.outcome, outcome, fieldNames.distMean, distMean, fieldNames.cp, cp, fieldNames.cBal, {cBal},...
    fieldNames.TAC, TAC, fieldNames.boatType, boatType, fieldNames.catchTrial, catchTrial, fieldNames.predT, predT,...
    fieldNames.outT, outT, fieldNames.triggers, triggers, fieldNames.pred, pred, fieldNames.predErr, predErr, fieldNames.predErrNorm, predErrNorm, fieldNames.predErrPlus, predErrPlus,...
    fieldNames.predErrMin, predErrMin, fieldNames.memErr, memErr, fieldNames.memErrNorm, memErrNorm,...
    fieldNames.memErrPlus, memErrPlus, fieldNames.memErrMin, memErrMin, fieldNames.UP, UP,...
    fieldNames.UPNorm, UPNorm, fieldNames.UPPlus, UPPlus, fieldNames.UPMin, UPMin, fieldNames.hit, hit,...
    fieldNames.perf, perf, fieldNames.accPerf, accPerf, fieldNames.Date, {Date});
end

## source_model.source
function [errBased_pCha, errBased_RU, errBased_LR, errBased_UP]=getTrialVarsFromPEs_cannon...
    (noise, PE, modHaz, newBlock, allHeliVis,...
    initRU, heliVisVar, lw, ud, driftRate, isOdd, outcomeSpace)



% Inputs:
% noise     = standard deviation of guassian noise distribution
% PE        = trial by trial prediction errors
% modHaz    = hazard rate
% newBlock  = logical indicating where new blocks start
% allHeliVis= visible helicopter/cannon?
% initRU    = RU has to be initialized to something...
% heliVisVar= how reliable is visible helicopter/cannon info?
% lw        = likelihood weight for surprise sensitivity
% ud        = uncertainty depletion
% isOdd     = logical array defining whether trials are from oddball condition
% outcomeSpace = size of outcome space 


% OK, i'd like to set it up so that this model can actually make
% predictions if you want it to. The idea would be that you just send in a
% nan instead of the prediction error array.




% adapted by MRN from getTrialVarsFromPEs that was used in
% "berlinMastList_new" for aging paper.

% the main changes from the code must deal with:

% 1) the circular nature of the cannon task.
% 2) the the drift/oddball condition.  


% list of all changes made:

% 1) removed option ot compute CPP and RU in separate passes. All will be
% computed at once for this analysis. That is the more justifiable strategy
% and it worked better anyway for the aging data.

% 2) added a variable "outcomeSpace" that defines the range of possible
% outcomes. 

% 3) included a drift term that increases total uncertainty

% 4) ** WRITE UP UNCERTAINTY UPDATE EQUATIONS HERE~!!! **



% Original description of the code:



% This code can be used to get SUBJECTIVE estimates of change-point
% probability and relative uncertainty from 1) subject prediction errors
% and 2) a set of model parameters (hazard, heliVisVar, likelihood weight,
% Uncertainty Depletion). 

% NOTE: this code can compute CPP and RU in two different ways. If you set:
% separateCPP_RU to true, then the algorithm computes all values of CPP
% using some average value of RU. Then it goes through and computes RU
% values according to all of those values for CPP. This method guarentees
% that RU can't pick up any error magnitude related variance... but its not
% exactly accurate, because subjects are not actually maintaining a fixed
% value of RU across all trials (so the CPP computation is a bit wrong). 
% The second strategy comes when you set separateCPP_RU to false... in that
% regime you get sequential updating of CPP based on RU and RU based on the
% previous CPP. In most ways this should be more accurate because it
% accounts for differences in uncertainty, but it does suffer from the fact
% that it leaves some error related variance in the data (as CPP is no
% longer exactly monotonic in absolute errors). 



if nargin<11
    ud=1;
end

if nargin<10
    lw=1;
end



% OK, it turns out we're using this bit of code over and over. In order to
% prevent stuff from diverging at different parts of code I'm going to put
% it in a function.

% inputs:
% noise = array of trial standard deviations...
% PE= prediction errors from subject.
% modHaz: what hazard do you want to give to the model?
% separateCPP_RU: fit CPP and RU together (ie no assumptions about flat RU)
% relUnc is only necessary if you are separating CPP and RU estimation:
% newBlock: logical telling you where new blocks start
% allHeliVis: logical telling you whether heli was visible (zeros for no)
% initRU: starting RU value
% heliVisVar: how much variance on the visible helicopter predictive cue
%
% keyboard

errBased_RU   = nan(size(PE));
errBased_pCha = nan(size(PE));
errBased_LR   = nan(size(PE));
errBased_UP   = nan(size(PE));
H=modHaz;



for i = 1:length(noise)
    
    
    
    % First compute relative uncertainty. 
    
    % IF this is the first trial in a block, set it to a fixed value:
    if newBlock(i)
        errBased_RU(i)=initRU;
    else
    % otherwise, compute it based on the previous trials prediction error.

        nVar=noise(i-1).^2;
               
        cp   =errBased_pCha(i-1);
        tPE  =PE(i-1);
        inRU=errBased_RU(i-1);
        
        
        
        
        
     % ok, this is complicated as shit. I'm pretty sure i've got it at this point, 
     % but the propagation of uncertainty, as it is written down here, is still not
     % totally intuitive. These notes are meant to provide some intuition: 
     
     % The key is that, if there is no change point or oddball, we want to
     % use the UPDATED value of uncertainty. That is to say: what is the
     % variance on the predictive distribution given the that we can use
     % the newest piece of information (and trust it completely). 
     
     % so as run length goes to infinity, this quantity goes to zero.
     % as run length goes to zero, this quantity goes to the noise variance
     % *NOTE* this is because we are assuming that we got a new piece of good info: 
     % so worst case scenario is we're at noise 
        
     % so through this lens it makes some sense that this should be the noise variance
     % divided by 1+run length . 
     
     % Why is this equal to inRU.*nVar ? Because inRU is equal to 1./(R+1).
     
     % OK, for the oddball condition, we want the oddball variance to be
     % equal to the total variance assuming that the new outcome provided
     % NO new information. This quantity should go to infinity as run length goes 
     % to zero... and toward zero as run length goes to infinity.      
     % It is 1/(run length)... 
        
     % given the intuition above, it is a bit easier to compute this update 
     % in terms of run length:
     
        runLength=(1-inRU)./inRU;
     
        if ~isOdd(i)
        % if we are in the changepoint condition, update uncertainty as
        % we've done previously:   
        % from equation 6 in heliFMRI paper:
        numerator=(cp.*nVar)+((1-cp).*inRU.*nVar) + ...
            cp.*(1-cp).*(tPE.*(1-inRU)).^2;
        elseif isOdd(i)  
        % difference in means = tPE.*inRU 
        % note, since oddballs are 0 learning, this is sort of opposite the
        % same term int the equation above (ie 1-inRU)
        
        % otherwise, update as if "cp" means oddball:
        numerator=(cp.*nVar./runLength)+((1-cp).*nVar./(runLength+1)) + ...
            cp.*(1-cp).*(tPE.*inRU).^2;
        
        % description for paper:
        % first term  = odd * (nVar*inRU)./(1-inRU )
        % second term = (1-odd)* inRU.*nVar
        % third term  = odd.*(1-odd).*(tPE.*inRU).^2;
        
        end
        
        
        
        
        
        
        
        % if we are in the drift condition, increment total uncertainty
        % according to the drift rate:
        if driftRate(i)>0
        numerator=numerator+driftRate(i).^2;
        end
        
        numerator=numerator./ud; % divide uncertainty about mean by constant
        denominator = numerator+nVar; % denominator is just numerator plus noise variacne
        errBased_RU(i)=numerator./denominator; % RU is just the fraction

        % this is going to be skipped because we don't have catch trials:
        if allHeliVis(i)==1
            % MRN improved this on 1/9/15
            inRU = (( errBased_RU(i).*nVar.*heliVisVar)./( errBased_RU(i).*nVar + heliVisVar))./nVar;
            if isnan(inRU)
                inRU=0;
            end
            errBased_RU(i)=inRU;  
        end

        
        if ~isfinite(errBased_RU(i))
            keyboard
        end
        
    end
    
    % Compute error based CPP for subject data:
    totUnc=(noise(i).^2)./(1-errBased_RU(i));
    % note, this should just be the denominator from above. Why didn't I
    % just use that? Not sure.
    
    
    pSame=(1-H).*normpdf(PE(i), 0, totUnc.^.5).^lw;
    pNew = H .* (1./outcomeSpace).^lw;
    errBased_pCha(i) = pNew./ (pSame+pNew);
   
    
    if ~isOdd(i)
        errBased_LR(i)=errBased_RU(i)+errBased_pCha(i)- errBased_RU(i).*errBased_pCha(i);
    else
        errBased_LR(i)=errBased_RU(i)- errBased_RU(i).*errBased_pCha(i);
    end
    
end


% compute model update
errBased_UP=errBased_LR.*PE;


## task_main.source
5: 
6: %%%
7: % Check Feedback!
8: %%%
9: 
13: % Trigger 3: Outcome: 500 - 1000 mSec
14: % Trigger 4: Fixation Cross 2: 1000 - 2000 mSec 
15: % Trigger 5: Shield: 2000 - 2500 mSec 
16: % Trigger 6: Fixation Cross 3: 2500 - 3500 mSec
17: % Trigger 7: Trial Summary (no timing trigger)
87:    
88:     if taskData.rew(i) == 1 && taskData.boatType(i) == 1
89:         taskData.actRew(i) = 1;
90:     elseif taskData.rew(i) == 1 && taskData.boatType(i) == 0
91:         taskData.actRew(i) = 2;
92:     elseif taskData.rew(i) == 2 && taskData.boatType(i) == 1
93:         taskData.actRew(i) = 2;    
94:     elseif taskData.rew(i) == 2 && taskData.boatType(i) == 0
95:         taskData.actRew(i) = 1;
96:     end   
97:     
119:         
120:         if i ~= taskParam.gParam.blockIndices(1) && i ~= taskParam.gParam.blockIndices(2) + 1 && i ~= taskParam.gParam.blockIndices(3) + 1 && i ~= taskParam.gParam.blockIndices(4) + 1  
121:            TickMark(taskParam, taskData.outcome(i-1), 'outc')
122:            TickMark(taskParam, taskData.pred(i-1), 'pred')
123:         end
130:         
131: %         c = GetSecs - ref;
132:         taskData.timestampOnset(i,:) = GetSecs - ref;
133:        
134:         %% get initiation RT
195:     [VBLTimestamp(i) StimulusOnsetTime(i) FlipTimestamp(i) Missed(i) Beampos(i)] = Screen('Flip', taskParam.gParam.window, t + 0.1, 1);
196:     taskData.triggers(i,2) = SendTrigger(taskParam, taskData, condition, vola, i, 2); % this is the prediction / fixation 1 trigger
197:     taskData.timestampPrediction(i,:) = GetSecs - ref;
198:     
199:     %io64(ioObject,taskParam.triggers.port,2) % this is the prediction and the onset of the first baseline
201:     
202:     % Calculate prediction error.
203:     taskData.predErr(i) = Diff(taskData.outcome(i), taskData.pred(i));
204:     %if i > 1 && taskParam.gParam.PE_Bar == true
205:       
206:     
207:     %end
208:     % Show outcome.
209:     %background = false
210:     %Cannonball(taskParam, taskData.distMean(i), taskData.outcome(i), background)
211:     %Cannonball(taskParam, distMean, outcome, background)
212:     
213:     DrawCircle(taskParam)
214:     %Shield(taskParam, taskData.pred(i))
215: 
216:     PredictionSpot(taskParam)  
217:     DrawPE_Bar(taskParam, taskData, i) 
218:     DrawOutcome(taskParam, taskData.outcome(i)) %%TRIGGER
219: %PredictionSpot(taskParam) 
220:     % DrawNeedle(taskParam, taskData.outcome(i)) % Test whether bar is
221:     % centered around the outcome
222:     
223:     Screen('DrawingFinished', taskParam.gParam.window, 1);
233:         if i > 1
234:             % Calculate memory error.
235:             taskData.memErr(i) = Diff(taskData.pred(i), taskData.outcome(i-1));
236:         else
237:             taskData.memErr(i) = 999;
239:     end
240:     
241:     % Calculate hits
242:     if isequal(condition,'main') || isequal(condition,'practice') || isequal(condition, 'practiceOddball') || isequal(condition, 'oddball')
243:         if taskData.predErr(i) <= taskData.allASS(i)/2
244:             taskData.hit(i) = 1;
245:             %taskData.perf(i) = taskParam.gParam.rewMag; 
246:         end
247:     elseif isequal(condition,'control') || isequal(condition,'practiceCont')
248:         if taskData.memErr(i) <= 5
249:             taskData.hit(i) = 1;
250:         end
251:     end
254: %     DrawCircle(taskParam)
255:      
256:     if taskData.actRew(i) == 1 && taskData.hit(i) == 1
257:         taskData.perf(i) = taskParam.gParam.rewMag;
258:     end
271:     end
272:     
273:     % Trigger: outcome.
274:    
275:     Screen('Flip', taskParam.gParam.window, t + 0.6);
276:     taskData.triggers(i,3) = SendTrigger(taskParam, taskData, condition, vola, i, 3); % this is the PE
277: 
278:     %io64(ioObject,taskParam.triggers.port,3) % this is the presentation of the outcome
279:     %taskData.outT(i) = SendTrigger(taskParam, taskData, condition, vola, i, Tevent);
280:     
291:     DrawCircle(taskParam)
292:     %PredictionSpot(taskParam)  
293:     Shield(taskParam, taskData.allASS(i), taskData.pred(i), taskData.boatType(i))
294:     DrawOutcome(taskParam, taskData.outcome(i)) %%TRIGGER
295:     %DrawPE_Bar(taskParam, taskData, i) 
296:     %PredictionSpot(taskParam) 
297:     % DrawNeedle(taskParam, taskData.outcome(i)) % Test whether bar is
298:     % centered around the outcome
299:     
300:    
301:     Screen('DrawingFinished', taskParam.gParam.window, 1);
302:     Screen('Flip', taskParam.gParam.window, t + 2.1);
303:     taskData.triggers(i,5) = SendTrigger(taskParam, taskData, condition, vola, i, 5); % this is the shield trigger
304: 
305:     %io64(ioObject,taskParam.triggers.port,5) % this is the prediction and the onset of the first baseline
320: %     if taskData.boatType(i) == 1
321: %         RewardTxt = Reward(taskParam, 'gold');
322: %         if Subject.rew == '1' && taskData.hit(i) == 1
323: %             taskData.perf(i) = taskParam.gParam.rewMag;  
324: %         end
325: %     else
326: %         RewardTxt = Reward(taskParam, 'silver');
327: %         if Subject.rew == '2' && taskData.hit(i) == 1
328: %             taskData.perf(i) = taskParam.gParam.rewMag;  
329: %         end
351:     
352:     
353:     taskData.timestampOffset(i,:) = GetSecs - ref;
354: 
355:     WaitSecs(.5);
374: % end
375: 
376: % Give performance feedback.
377: % while 1
378: %     if isequal(condition, 'practice')
379: %         txtFeedback = sprintf('In diesem Block h�ttest du %.2f von %.2f Euro gewonnen', taskData.accPerf(end), maxMon);
380: %     else
381: %         txtFeedback = sprintf('In diesem Block hast du %.2f von %.2f Euro gewonnen', taskData.accPerf(end), maxMon);
382: %     end
383: %      hits = sum(taskData.hit == 1)
384: %                 goldBall = sum(taskData.boatType == 1)
385: %                 goldHit = taskData.accPerf(end)/taskParam.gParam.rewMag %sum(practData.boatType == 1)
386: %                 silverBall = sum(taskData.boatType == 0)
387: %                 silverHit = hits - goldHit;
388: %                 maxMon = (length(find(taskData.boatType == 1)) * taskParam.gParam.rewMag);
389: %                 
390:                     hits = sum(taskData.hit == 1);
391:                     goldBall = sum(taskData.boatType == 1);
392:                     goldHit = taskData.accPerf(end)/taskParam.gParam.rewMag;
393:                     silverBall = sum(taskData.boatType == 0);
394:                     silverHit = hits - goldHit;
395:                     maxMon = (length(find(taskData.boatType == 1))...
396:                         * taskParam.gParam.rewMag);
407:                     header = 'Performance';
408:                     if isequal(condition, 'practiceOddball')
409: %                     txt = sprintf(['%s shield catches: %.0f of '...
410: %                     '%.0f\n\n%s shield catches: %.0f of '...
411: %                     '%.0f\n\nIn this block you would have earned %.2f of '...
412: %                     'possible $ %.2f.'], colRewCap, goldHit,...
413: %                     goldBall, colNoRewCap, silverHit, silverBall,...
414: %                     practData.accPerf(end), maxMon);
415:                     [txt, header] = Feedback(taskData, taskParam, Subject, condition);
416: 
417:                     else
418: %                     txt = sprintf(['%s shield catches: %.0f of '...
419: %                     '%.0f\n\n%s shield catches: %.0f of '...
420: %                     '%.0f\n\nIn this block you earned %.2f of '...
421: %                     'possible $ %.2f.'], colRewCap, goldHit,...
422: %                     goldBall, colNoRewCap, silverHit, silverBall,...
423: %                     practData.accPerf(end), maxMon);
424:                     [txt, header] = Feedback(taskData, taskParam, Subject, condition);
425: 
426:                     end
433:                 
434:                % header = 'Leistung';
435:                 feedback = true
436:                 [fw, bw] = BigScreen(taskParam, taskParam.strings.txtPressEnter, header, txt, feedback);
437:             
438:     
442: %     DrawFormattedText(taskParam.gParam.window, txtBreak, 'center', taskParam.gParam.screensize(4)*0.3);
443: %     Screen('TextSize', taskParam.gParam.window, 30);
444: %     DrawFormattedText(taskParam.gParam.window, txtFeedback, 'center', 'center');
445: %     DrawFormattedText(taskParam.gParam.window,txtPressEnter,'center',taskParam.gParam.screensize(4)*0.9);
446: %     Screen('DrawingFinished', taskParam.gParam.window);
463: %% Save data.
464: fieldNames = taskParam.fieldNames;
465: Data = struct(fieldNames.actJitter, taskData.actJitter, fieldNames.block, taskData.block, fieldNames.initiationRTs, taskData.initiationRTs, fieldNames.timestampOnset, taskData.timestampOnset, fieldNames.timestampPrediction, taskData.timestampPrediction, fieldNames.timestampOffset, taskData.timestampOffset, fieldNames.allASS, taskData.allASS, fieldNames.driftConc, driftConc, fieldNames.oddballProb, oddballProb, fieldNames.oddBall, taskData.oddBall, fieldNames.ID, {taskData.ID}, fieldNames.age, taskData.age, fieldNames.rew, {taskData.rew}, fieldNames.actRew, taskData.actRew, fieldNames.sex, {taskData.sex},...
466:     fieldNames.cond, {taskData.cond}, fieldNames.cBal, {taskData.cBal}, fieldNames.trial, taskData.trial,...
467:     fieldNames.vola, vola, taskParam.fieldNames.sigma, sigma, fieldNames.outcome, taskData.outcome, fieldNames.distMean, taskData.distMean, fieldNames.cp, taskData.cp,...
468:     fieldNames.TAC, taskData.TAC, fieldNames.boatType, taskData.boatType, fieldNames.catchTrial, taskData.catchTrial, ...
469:     fieldNames.predT, taskData.predT, fieldNames.outT, taskData.outT, fieldNames.triggers, taskData.triggers, fieldNames.pred, taskData.pred, fieldNames.predErr, taskData.predErr, fieldNames.predErrNorm, taskData.predErrNorm,...
471:     fieldNames.memErr, taskData.memErr, fieldNames.memErrNorm, taskData.memErrNorm, fieldNames.memErrPlus, taskData.memErrPlus,...
472:     fieldNames.memErrMin, taskData.memErrMin, fieldNames.UP, taskData.UP,fieldNames.UPNorm, taskData.UPNorm,...
473:     fieldNames.UPPlus, taskData.UPPlus, fieldNames.UPMin, taskData.UPMin, fieldNames.hit, taskData.hit,...
474:     fieldNames.perf, taskData.perf, fieldNames.accPerf, taskData.accPerf, fieldNames.Date, {taskData.Date});
475: end

## task_config.source
20: %       - Reward has to be calculated
21: %       - oddBall versus control
22: %       - check sigma vola driftConc - what is still used?
23: % 
24: % daten generieren ohne aufgabe zu machen
38: shieldTrials = 6; % Trials during the introduction (per condition). F�r Pilot: 10
39: practTrials = 20; % Number of practice trials per condition. F�r Pilot: 20
40: trials = 240;% Number of trials per (sigma-)condition. F�r Pilot: 120 // EEG: 240
41: blockIndices = [1 60 120 180]; % When should new block begin?
42: vola = [.25 .7 0]; % Volatility of the environment.
43: oddballProb = [.25 0]; % Oddball probability. .15
44: sigma = [10 12 99999999];  % [10 12 99999999] SD's of distribution.
45: driftConc = [30 99999999]; % Concentration of the drift. 10
46: safe = 3; % How many guaranteed trials without change-points.
47: rewMag = 0.2; % Reward magnitude.
48: jitter = 0.2; % Set jitter. 
52: % currently not in use:
53: runVola = false; % Do you want to run different volatility conditions?
54: runSigma = false; % Do you want to run different sigma conditions?
55: catchTrials = false;
56: PE_Bar = false; % Use a prediction error bar?
192: fOddball = 'oddball';
193: fOddballProb = 'oddballProb'; oddballProbs = fOddballProb;
194: fDriftConc = 'driftConc'; driftConcentrations = fDriftConc;
195: fSigmas = 'sigma'; sigmas = fSigmas; % Sigma.
196: fOddBall = 'oddBall'; oddBall = fOddBall;
197: fDate = 'Date'; Date = fDate; % Date.
202: fDistMean = 'distMean'; distMean = fDistMean; % Distribution mean.
203: fCp = 'cp'; cp = fCp; % Change point.
204: fTAC = 'TAC'; TAC = fTAC; % Trials after change-point.
205: fBoatType = 'boatType'; boatType = fBoatType; % Boat type.
206: fCatchTrial = 'catchTrial'; catchTrial = fCatchTrial; % Catch trial.
228: 
229: fFieldNames = 'fieldNames';
230: fieldNames = struct('actJitter', 'actJitter', 'block', 'block','initiationRTs', 'initiationRTs','timestampOnset', 'timestampOnset', 'timestampPrediction', 'timestampPrediction', 'timestampOffset', 'timestampOffset', fOddBall, oddBall, fOddball, oddball, fOddballProb, oddballProbs, fDriftConc, driftConcentrations, fAllASS, allASS, fID, ID, fSigmas, sigmas, fAge, age, fSex, sex, fRew, rew, fActRew, actRew, fDate, Date, fCond, cond, fTrial, trial, fOutcome, outcome, fDistMean, distMean, fCp, cp,...
231:     fVolas, volas, fTAC, TAC, fBoatType, boatType, fCatchTrial, catchTrial, fPredT, predT, fOutT, outT, fTriggers, triggers, fPred, pred, fPredErr, predErr, fPredErrNorm, predErrNorm,...
232:     fPredErrPlus, predErrPlus, fPredErrMin, predErrMin, fMemErr, memErr, fMemErrNorm, memErrNorm, fMemErrPlus, memErrPlus,...
233:     fMemErrMin, memErrMin, fUP, UP, fUPNorm, UPNorm, fUPPlus, UPPlus, fUPMin, UPMin, fHit, hit, fCBal, cBal, fPerf, perf, fAccPerf, accPerf, fRawPredErr, rawPredErr);
239: fPE_Bar = 'PE_Bar';
240: fSendTrigger = 'sendTrigger';
241: fDriftConc = 'driftConc';
242: fOddballProb = 'oddballProb';
243: fComputer = 'computer';
247: fPractTrials = 'practTrials';
248: fContTrials = 'contTrials';
249: fSafe = 'safe';
250: fRewMag = 'rewMag';
251: fSentenceLength = 'sentenceLength';
258: end
259: ref = GetSecs;
260: gParam = struct('jitter', jitter, 'blockIndices', blockIndices, 'ref', ref, fSentenceLength, sentenceLength, fOddball, oddball, fDriftConc, driftConc, fOddballProb, oddballProb, fSigmas, sigma, fVolas, vola, fRunVola, runVola, fRunSigma, runSigma, fPE_Bar, PE_Bar, fSendTrigger, sendTrigger, fComputer, computer, fTrials, trials, fPractContTrials, practContTrials, fShieldTrials, shieldTrials, fPractTrials, practTrials, fContTrials, contTrials,...
261:     fSafe, safe, fRewMag, rewMag, fScreensize, screensize, fZero, zero, fWindow, window, fWindowRect, windowRect);
262: 
263: %% Circle parameters.
416: fBoatTrigger = 'boatTrigger'; boatTrigger = 6; % Boat type.
417: fBaseline3Trigger = 'baseline3Trigger'; baseline3Trigger = 9; % Baseline.
418: fBlockLVTrigger = 'blockLVTrigger'; blockLVTrigger = 10; % Block with low sigma.
419: fBlockHVTrigger = 'blockHVTrigger'; blockHVTrigger = 11; % Block with high sigma.
420: fBlockControlTrigger = 'blockControlTrigger'; blockControlTrigger = 12; % Control block.
421: 
447: if test == true
448:     
449:     [taskDataLV, DataLV] = Main(taskParam, vola(1), 'main', Subject); % Run task (low sigma).
450:     
451:     % Allow input again.
462:             Instructions(taskParam, 'Oddball', Subject);
463:             condition = 'practiceOddball';
464:             [taskDataOddballPractice, DataOddballPracticeLV] = Main(taskParam, vola(3), sigma(1), condition, Subject);
465:         elseif Subject.cBal == 2
466:             Instructions(taskParam, 'Main', Subject);
467:             condition = 'practice';
468:             [taskDataOddballPractice, DataOddballPracticeLV] = Main(taskParam, vola(3), sigma(1), condition, Subject);
469:         end
470:         if taskParam.gParam.oddball == false
516:     type = 'Oddball';
517:     if Subject.cBal == 1
518:         [taskDataOddball, DataOddball] = Main(taskParam, vola(1), sigma(1), condition, Subject); % Run task (high sigma).
519:     elseif Subject.cBal == 2;
520:         condition = 'main';
521:         type = 'Main';
522:         [taskDataCP, DataCP] = Main(taskParam, vola(1), sigma(1), condition, Subject); % Run task (high sigma).
523:     end
524:     
532:         end
533:         condition = 'practice';
534:         [taskDataPracticeMain, DataPracticeMain] = Main(taskParam, vola(3), sigma(1), condition, Subject);
535:         header = 'Real Task!';
536:         txt = ['This is the beginning of the real task. During '...
555: if Subject.cBal == 1
556:     condition = 'main';
557:     [taskDataCP, DataCP] = Main(taskParam, vola(1), sigma(1), condition, Subject); % Run task (high sigma).
558: elseif Subject.cBal == 2
559:     condition = 'oddball';
560:     [taskDataOddball, DataOddball] = Main(taskParam, vola(1), sigma(1), condition, Subject); % Run task (high sigma).
561: end
562: WaitSecs(0.1);
572:     %     if Subject.cBal == '1'
573:     %         if runSigma == true
574:     %             VolaIndication(taskParam, txtLVHS, txtPressEnter) % Low sigma.
575:     %             [taskDataControlLVHS, DataControlLVHS] = Main(taskParam, vola(1), sigma(2), condition, Subject); % Run task (low sigma).
576:     %             %VolaIndication(taskParam, txtHVLS, txtPressEnter) % High sigma.
577:     %             %[taskDataHVLS, DataHVLS] = BattleShipsMain(taskParam, vola(2), sigma(1), condition, Subject); % Run task (high sigma).
578:     %             %VolaIndication(taskParam, txtLVHS, txtPressEnter) % Low sigma.
579:     %             %[taskDataLVHS, DataLVHS] = BattleShipsMain(taskParam, vola(1), sigma(2), condition, Subject); % Run task (low sigma).
580:     %             VolaIndication(taskParam, txtHVLS, txtPressEnter) % High sigma.
581:     %             [taskDataControlHVLS, DataControlHVLS] = Main(taskParam, vola(2), sigma(1), condition, Subject); % Run task (high sigma).
582:     %             %VolaIndication(taskParam, txtLowVola, txtPressEnter) % Low sigma.
583:     %             %[taskDataControlLV, DataControlLV] = BattleShipsMain(taskParam, vola(1), condition, Subject); % Run task (low sigma).
584:     %             %VolaIndication(taskParam, txtHighVola, txtPressEnter) % High sigma.
585:     %             %[taskDataControlHV, DataControlHV] = BattleShipsMain(taskParam, vola(2), condition, Subject); %Run task (high sigma).
586:     %         else
587:     %             VolaIndication(taskParam, txtLowVola, txtPressEnter) % Low sigma.
588:     %             [taskDataControlLV, DataControlLV] = Main(taskParam, vola(1), sigma(1), condition, Subject); % Run task (low sigma).
589:     %             VolaIndication(taskParam, txtHighVola, txtPressEnter) % High sigma.
590:     %             [taskDataControlHV, DataControlHV] = Main(taskParam, vola(2), sigma(1), condition, Subject); %Run task (high sigma).
591:     %         end
592:     %     else
593:     %         VolaIndication(taskParam, txtHighVola, txtPressEnter) % High sigma.
594:     %         [taskDataControlHV, DataControlHV] = Main(taskParam, vola(2), condition, Subject); %Run task (high sigma).
595:     %         VolaIndication(taskParam, txtLowVola, txtPressEnter) % Low sigma.
596:     %         [taskDataControlLV, DataControlLV] = Main(taskParam, vola(1), condition, Subject); % Run task (low sigma).
597:     %     end
598:     %

## source_analysis.source
237:     % Set parameters for generative model:
238:     % get average number of change-points and oddballs
239:     simHaz=mean([nanmean(allBehavData.cp), nanmean(allBehavData.oddBall)]);
240:     simDrift=unique(allBehavData.driftConc); % get drift
241:     simNoise=unique(allBehavData.sigma);     % get noise
278:     
279:     
280:     [modSurp, modRU, errBased_LR, errBased_UP]=getTrialVarsFromPEs_cannon...
281:         (gaussStd, PE, simHaz,  newBlock', false(size(PE)),...
282:         .99, 0, 1, 1, gaussDriftStd, ~blockCond, 2*pi);
283:  
309:     
310:     
311:     % does regression model make big mistakes on post-oddball trials?
312:     % MRN added this july 1, 2019 -- it seems that model is failing for
313:     % post-oddball trials (higher error variance) -- and when we remove
314:     % these trials we get larger fit values to the behavioral regression
315:     % coefficients of interest. 
316:     
317:     postOdd=find(allBehavData.oddBall==1) +1;
318:     postOdd(postOdd>length(allBehavData.oddBall))=[];
319:     postOddLogical=false(size(allBehavData.oddBall));
320:     postOddLogical(postOdd)=true;
321:     postOddLogical(newBlock)=false;
322:     sel=~postOddLogical&isfinite(UP) & all(isfinite(rawX), 2);
323: 
324:     
402:     allBehavData.subsPredRad=subsPredRad;
403:     allBehavData.newBlock=newBlock;
404:     allBehavData.postOdd=postOddLogical;
405:     allBehavData=straightStruct(allBehavData);
406:     
470:         useChannel=strmatch(erpChan, {EEG.chanlocs.labels});
471:         totBase=nanmean(nanmean(downSampData(useChannel, downSampTimes>baselineTime(1)&downSampTimes<baselineTime(2),:), 3), 2);
472:         sel=relBehav.oddBall~=1&relBehav.cp~=1&mod(relBehav.trial-1, 60)>1;
473:         normalERP=nanmean(downSampData(useChannel, :, sel), 3)-totBase;
474:         sel=relBehav.oddBall~=1&relBehav.cp==1&mod(relBehav.trial-1, 60)>1;
475:         cpERP=nanmean(downSampData(useChannel, :, sel), 3)-totBase;
476:         sel=relBehav.oddBall==1&relBehav.cp~=1&mod(relBehav.trial-1, 60)>1;
477:         oddERP=nanmean(downSampData(useChannel, :, sel), 3)-totBase;
478: 
643:                         relBehav.PE.* meanCentX(physData), relBehav.PE.* meanCentX(physData).*meanCentX(relBehav.cpCond)];
644:                     
645:                     sel=isfinite(relBehav.UP) & all(isfinite(rawX),2)&~relBehav.postOdd;
646:                     data.Y=relBehav.UP(sel);
647:                     data.X=(rawX(sel,:));
695:                             % in bin, oddball:
696:                             rawX=[ones(size(relBehav.PE)), relBehav.PE];
697:                             sel=relBehav.cpCond==0 & inBin & isfinite(relBehav.UP) & all(isfinite(rawX),2)&~relBehav.postOdd;
698:                             data.Y=relBehav.UP(sel);
699:                             data.X=(rawX(sel,:));
703:                             % in bin, CP:
704:                             rawX=[ones(size(relBehav.PE)), relBehav.PE];
705:                             sel=relBehav.cpCond==1 & inBin & isfinite(relBehav.UP) & all(isfinite(rawX),2)&~relBehav.postOdd;
706:                             data.Y=relBehav.UP(sel);
707:                             data.X=(rawX(sel,:));
724:                         relBehav.PE.* meanCentX(physData).*(relBehav.cpCond==1), relBehav.PE.* meanCentX(physData).*(relBehav.cpCond==0)];
725:                     
726:                     sel=isfinite(relBehav.UP) & all(isfinite(rawX),2) &~relBehav.postOdd;
727:                     data.Y=relBehav.UP(sel);
728:                     data.X=(rawX(sel,:));
875:                            ]; % LR_hat is predicted LR from pure behavioral model.
876:                        
877:                        sel=isfinite(allBehavData.UP) & all(isfinite(rawX), 2) &~allBehavData.postOdd;
878:                      
879:                        data.Y=allBehavData.UP(sel);
916:  
917:                       
918:                         sel=isfinite(relBehav.UP) & all(isfinite(rawX),2) &~relBehav.postOdd;
919:                         data.Y=relBehav.UP(sel);
920:                         data.X=(rawX(sel,:));
1926:     for i = 1:length(exPE)
1927:         
1928:         [modSurp, modRU, errBased_LR_oddball(i), errBased_UP]=getTrialVarsFromPEs_cannon...
1929:             (gaussStd(1), exPE(i), simHaz,  true, false,...
1930:             simUncOdd, 0, 1, 1, gaussDriftStd(1), true, 2*pi);
1931:         
1932:         
1933:         [modSurp, modRU, errBased_LR_CP(i), errBased_UP]=getTrialVarsFromPEs_cannon...
1934:             (gaussStd(1), exPE(i), simHaz,  true, false,...
1935:             simUncCP, 0, 1, 1, gaussDriftStd(1), false, 2*pi);
1936:         

## Pinned article selected paragraphs
We used EEG to measure electrophysiological signatures of feedback processing while participants performed a modified predictive inference task (Nassar et al., 2010) designed to dissociate surprise from learning. Predictions were made in the context of a video game that required participants to place a shield at a location on a circle in order to block cannonballs that would be fired from a cannon located at the center of the circle (Figure 1A). Surprise and learning were manipulated independently using two different task conditions. In the oddball condition, the aim of the cannon drifted slowly from one trial to the next (Figure 1B, dotted line) and cannonball locations were distributed around the point of cannon aim (Figure 1B, green points nearby dotted line) or, occasionally and unpredictably, uniformly distributed around the circle (oddballs; see green point on trial 11 of Figure 1B for example). In the changepoint condition, the cannon aim remained constant for an unpredictable duration, and was then re-aimed at a new location on the circle at random (changepoints; Figure 1C, dotted line). Cannonball locations were always distributed around the point of cannon aim in this condition (Figure 1C, green points).

(A) Participants were trained to place the center of a shield (green tick; prediction phase [left]) at the aim location of a cannon (training task [top]) in order to block a cannonball shot from it (outcome phase [top middle]) with a shield that varied in size from trial to trial and was revealed at the end of the trial (shield phase [top right]). After training, participants were asked to complete the same task, but without a visual depiction of the cannon, which required them to infer the aim of the cannon based on the sequence of previously observed cannonballs (test task [bottom]). (B) In oddball blocks, cannon aim (dotted black line) followed a random walk and cannonball locations were typically drawn from a Von Mises distribution centered on the true cannon aim (green points), but were occasionally drawn from a uniform distribution across the entire circle (oddball trials). Participants placed their shield on each trial (brown line) providing information about their inference about the cannon aim. (C) In changepoint blocks, cannon aim was stationary for most trials but was occasionally resampled uniformly from possible angles (changepoint) and cannonball locations were always drawn from a Von Mises distribution centered on the true cannon aim (green points). (D and E) Optimal inference could be approximated in both generative environments by tracking and adjusting learning according to relative uncertainty and the probability of an unlikely event (oddball or changepoint).

In both conditions, participants were instructed to place a shield on each trial in order to maximize the chances of blocking the upcoming cannonball (Figure 1B and C, orange line). However, behavior differed qualitatively in these two conditions, which can be observed clearly in the example participant data in Figure 1. In particular, shield placements were not updated in response to extreme outcomes in the oddball condition (oddballs; Figure 1B) but were updated dramatically in response to extreme outcomes in the changepoint condition (changepoints; Figure 1C).

To quantitatively analyze the differences between the two task conditions, we extended a previously developed normative learning model (Nassar et al., 2010; Nassar et al., 2016). The model approximates optimal inference using an error-driven learning rule by adjusting learning from trial to trial according to two latent variables. The first latent variable tracks the probability with which the most recent outcome was generated from an unexpected generative process (oddball probability in Figure 1D; changepoint probability in Figure 1E), whereas the second latent variable tracks the model’s uncertainty about the true cannon aim (Figure 1D and E; uncertainty). Critically, the model stipulates that surprising events in the oddball condition, which are tracked through the model’s estimate of oddball probability, should reduce learning, as oddballs are unrelated to future cannonball locations (d'Acremont and Bossaerts, 2016). In contrast, the model stipulates that surprising events in the changepoint condition, which are tracked through the model’s estimate of changepoint probability, should amplify learning, as changepoints render prior cannonballs (and thus prior beliefs) irrelevant to the problem of predicting future ones (Adams and MacKay, 2007; Wilson et al., 2010). Qualitatively, behavior from the example participant seems to follow these prescriptions, with adjustments in shield position fairly minimal on trials that include a spike in oddball probability (Figure 1B,D), but fairly large on trials that include a spike in changepoint probability (Figure 1C,E).

The normative model also makes quantitative prescriptions for how learning should be adjusted according to surprise differentially in the changepoint and oddball conditions. The surprise of a given outcome can be measured crudely through the degree to which a cannonball location differed from that which was predicted (e.g., the shield position). Larger absolute prediction errors indicate a higher degree of surprise, and higher oddball or changepoint probabilities depending on the task condition. Learning in this task can be measured through the degree to which a participant adjusts the shield position in response to a given prediction error (Nassar et al., 2010), and a fixed rate of learning would correspond to a straight line mapping each prediction error onto a corresponding shield update, where the slope of the line can be thought of as the learning rate (Figure 2C, gray lines). The normative learning model does not prescribe a fixed learning rate across all levels of surprise; instead it prescribes higher learning rates for more surprising outcomes in the changepoint condition (Figure 2C, orange) and lower learning rates for more surprising outcomes in the oddball condition (Figure 2C, blue).

(A) In the changepoint condition, surprising events (changepoints) signaled a transition in the aim of the cannon whereas (B) in the oddball condition, surprising events (oddballs) were unrelated to the process through which the aim of the cannon transitioned. (C) Learning rate in the cannon task can be described by the slope of the relationship between prediction error (signed distance between cannonball and shield; abscissa) and update (signed change in shield position after observing new cannonball location; ordinate). Fixed learning rate updating corresponds to a line in this space whose slope is uniform across prediction errors and reflects the learning rate (gray lines). In contrast, normative learning dictates that the slope should decrease for extreme prediction errors in the oddball condition (blue) but increase for extreme prediction errors in the changepoint condition (orange). (D) Prediction error (abscissa) and update (ordinate) for each trial (points) in each condition (designated by color) completed by a single example participant. Size of points is inversely related to density of data for improved visualization. (E) Trial updates for each subject were fit with a regression model that included prediction errors (to measure fixed learning rate) as well as several interaction terms to assess how learning depended on various factors. (F) Coefficients from regression model fit to individual subjects (points) revealed an overall tendency to update toward recent cannonball locations (red, t = 14.4, dof = 38, p=10−17), and a tendency to do so more in the changepoint condition (green, t = 3.1, dof = 38, p=0.003), when uncertain (yellow, t = 7.5, dof = 38, p=4×10−9), and on trials where the cannonball was not blocked by the shield (pink, t = −3.4, dof = 38, p=0.001). The model revealed that there was no consistent effect of surprise on learning across both conditions (blue, t = 0.8, dof = 38, p=0.43), but that there was a strong interaction between surprise and condition (orange, t = 9.9, dof = 38, p=4×10−12) whereby surprise tended to increase learning in the changepoint condition but decrease learning in the oddball condition.

Figure 2—figure supplement 1.Behavioral interaction was driven by positive effects of surprise on learning in the changepoint condition and negative effects of surprise on learning in the oddball condition.Model described in Figure 2E was altered such that PE*Surprise and PE*Surprise*Condition terms were replaced with two terms that separately modeled the effect of surprise on updating behavior in the changepoint condition (left, yellow) and in the oddball condition (right, blue). Points reflect maximum likelihood coefficient values estimated for individual subjects. Mean effect across participants was positive in the changepoint condition (mean/SEM beta = 0.38/0.05, t = 7.7, dof = 38, p=2×10e-9) and negative in the oddball condition (mean/SEM beta = −0.33/0.05, t = −6.6, dof = 38, p=8×10e-8).

Model described in Figure 2E was altered such that PE*Surprise and PE*Surprise*Condition terms were replaced with two terms that separately modeled the effect of surprise on updating behavior in the changepoint condition (left, yellow) and in the oddball condition (right, blue). Points reflect maximum likelihood coefficient values estimated for individual subjects. Mean effect across participants was positive in the changepoint condition (mean/SEM beta = 0.38/0.05, t = 7.7, dof = 38, p=2×10e-9) and negative in the oddball condition (mean/SEM beta = −0.33/0.05, t = −6.6, dof = 38, p=8×10e-8).

Participants adjusted learning behavior in accordance with normative predictions, albeit with considerable heterogeneity across trials and participants. Shield updating behavior and corresponding prediction errors for an example participant reveal the basic trend predicted by the normative model, although exact updates were variable from one trial to the next (Figure 2D). To summarize the degree to which updating behavior of individual subjects was contingent on key task variables, we constructed a linear regression model that described trial-by-trial updates in terms of prediction errors as well as key task variables thought to modulate the degree to which prediction errors are translated into updates (Figure 2E) including condition (changepoint versus oddball block), surprise (as measured by changepoint or oddball probability estimates from normative model), and their multiplicative interaction (capturing the degree to which learning is increased for surprising outcomes in the changepoint context, but decreased for surprising outcomes in the oddball context). As expected, prediction error coefficients were positive, capturing a tendency for participants to update shield position toward the most recent cannonball position (Figure 2F, red; mean/SEM beta = 0.58/0.04, t = 14.4, dof = 38, p=6×10−17). Furthermore, participants systematically adjusted the degree to which they did so according to condition (Figure 2F, green; mean/SEM beta = 0.08/0.02, t = 3.1, dof = 38, p=0.003), but not significantly according to surprise (Figure 1F, blue; mean/SEM beta = 0.03/0.03, t = 0.8, dof = 38, p=0.43). Critically, surprise robustly impacted learning in opposite directions for the two conditions, as indicated by the interaction between surprise and condition (Figure 2F, orange; mean/SEM beta = 0.71/0.07, t = 9.9, dof = 38, p=4×10−12). Specifically, positive coefficients indicate that sensitivity to prediction errors was increased for surprising outcomes in the changepoint condition and decreased for surprising outcomes in the oddball condition (Figure 2—figure supplement 1), as predicted by the normative model.

Competing theories posit different functional roles for the signal underlying the P300. In particular, some theories suggest that the P300 reflects a general surprise signal, whereas others attribute a more specific role in accumulating information, for example about the current state of the world. To test how the P300 may relate to learning behavior in our task we extracted trial-to-trial measures of these components by taking the dot product of the cluster t-map and each single trial ERP (Figure 4A; Collins and Frank, 2018). The dot product indexes the degree to which a single trial ERP displays the profile of a given spatiotemporal cluster, thereby allowing us to test the degree to which the measured signal on any given trial might relate to behavior. We then examined how trial-to-trial behavioral updates in shield position related to these single trial EEG signal strengths using a regression model similar to that employed in the behavioral analysis (Figure 4B). The regression model included two key terms to characterize the influence of 1) the multiplicative interaction of prediction error with the EEG signal strength, and 2) the interaction between prediction error, EEG signal strength and condition. The first EEG-based term provided a measure of the relationship between learning and the P300 that was independent of condition, and thus allowed us to test the prediction that the P300 reflects a direct learning signal (Figure 4C, left). The second EEG-based term provided a measure of the relationship between learning and the P300 that depended on condition (conditional learning), and thus allowed us to test the prediction that any learning impact of the P300 is bidirectionally sensitive to the source of surprise (Figure 4C, right).

Participants were instructed to place a shield at some position along a circle subtending 5 degrees of visual angle in order to maximize the chances of catching a cannonball that would be shot on that trial (Figure 1A). During an instructional training period, the generative process that gave rise to cannonball locations was made explicit to participants. During this phase, participants were shown a cannon in the center of the screen. On each trial, a cannonball would be ‘shot’ from that cannon with some angular variability (Von Mises distributed ‘Noise’, concentration = 10 degrees). A key manipulation in our design was how the aim of the cannon evolved from one trial to the next. The cannon would either (1) remain stationary on the majority of trials and re-aim to a random angle with an average hazard rate of 0.14 (changepoint condition) or (2) change position slightly from one trial to the next according to a Von Mises distributed random walk with mean zero and concentration 30 degrees (oddball condition). In the changepoint condition, all cannonballs were displayed as originating at the cannon in the center of the circle, whereas in the oddball condition a small fraction (0.14) of trials were oddballs, in which the cannonball location was sampled uniformly across the entire circle and the cannonball appeared without a trajectory.

After completing the instructional training, in which the generative process was fully observable, participants were asked to perform the same basic task without being able to see the cannon. In this experimental phase participants were forced to use knowledge of the generative structure gained during training, along with the sequence of prior cannonball locations, in order to infer the aim of the cannon and to inform shield placement. When making a prediction, tick marks on the circle indicated the locations of the cannonball and shield placement from the previous trial. Participants completed four blocks of 60 trials for each task condition (changepoint and oddball) in order randomized across participants. The 240 experimental trials for each condition always followed the instructional training period for that condition in order to minimize ambiguity over which generative structure was giving rise to the experimental outcomes.

On each trial of the experimental task, participants would adjust the position of the shield through key presses (starting at the shield position from the previous trial) until they were satisfied with its location (Figure 1A; prediction phase). After participants locked in their prediction (through a key press) there was a 500 ms delay and then the cannonball location was revealed for 500 ms (Figure 1A; outcome phase). The cannonball then disappeared for 1000 ms before it reappeared, along with a full depiction of the participants shield (Figure 1A; shield phase). The shield was always centered on the position indicated by the participant during the prediction phase, but differed in size from one trial to the next in a random and unpredictable fashion that ensured subjects could not predict whether they would successfully ‘catch’ the cannonball during the outcome phase. Thus, information provided during the outcome phase provided all necessary information to update beliefs about the cannon aim, but did not contain sufficient information to determine whether the cannonball would be successfully blocked on the trial. In addition to trial feedback provided during the shield phase, participants were also provided information about their performance at the end of each block that included the fraction of cannonballs that were blocked. Participants were paid an incentive bonus at task completion that was based on the number of cannonballs that were blocked.

The updated relative uncertainty, along with assumed knowledge of the overall noise and hazard rate, were used to calibrate the oddball probability associated with each new prediction error:

Where H is the average hazard of an oddball (0.14) and δt+1 is the new prediction error, and the second term in the denominator reflects the probability density on a normal distribution centered on the predicted location and with variance derived from relative uncertainty. The model’s prediction about cannon aim was then updated according to a fraction of the prediction error δt+1 with the exact fraction, or learning rate, determined according to the updated uncertainty and oddball probability:

Two key behavioral measures were extracted from each trial. First, the prediction error on a trial was defined as the circular distance between the cannonball location and the shield position for that trial. Second, the update on a given trial was defined as the circular distance between the shield position on that trial and the shield position on the subsequent trial (e.g., the updated shield position). In order to better understand the computational factors governing adjustments in shield position, we fit updates with a linear model that included an intercept term to model overall biases in learning along with a prediction error term to capture general tendencies to adjust the shield towards the most recent cannonball location. The model also included additional terms to model how the influence of recent cannonball locations changed dynamically according to task context. These terms included: (1) prediction error times uncertainty interaction (to model how much more participants updated shield position under conditions of uncertainty – as assessed by the computational model), (2) prediction error times surprise (where surprise was indexed by changepoint probability or oddball probability from computational model depending on the context), (3) prediction error times surprise times condition (where condition was +1 for changepoint blocks and −1 for oddball conditions), (4) prediction error times block (a categorical variable indicating whether the shield ‘blocked’ the most recent cannonball. The model was fit to updates from each participant individually, excluding updates in response to outcomes immediately following oddballs, as such updates are difficult to attribute to learning (e.g., movements toward recent outcome) rather than memory (returning to a pre-oddball location). Nonetheless, inclusion of these trials in our behavioral models does not change the primary results reported here.

Here we assume that the hazard rate is known, given the extensive training participants receive under visible cannon conditions, however the more general case where hazard rate is unknown is similar and has been addressed elsewhere (Wilson et al., 2010). Note that the generative hazard rate differs from the empirical hazard rate (0.14) because the first trial of each block was considered to be a changepoint.

Thus, on each trial it is possible to infer the probability distribution over possible cannon locations given all previous cannonball locations using a recursive rule that updates a prior inference from the previous trial p(Ct−1|B1:t−1) according to the appropriate transition function p(CtSt,Ct-1 and the likelihood of the observed cannonball location from this trial pBt|Ct. Expanding the summation over the changepoint variable reveals that p(Ct|B1:t) is a mixture with two components:

Note that this equation differs from the changepoint solution only in that the likelihood of Bt is now conditional on St (now reflecting a binary oddball variable) whereas the Ct is now conditionally independent of St. Once again, the equation can be expanded to reveal a mixture of two components:

In the case of an oddball, the mean of the predictive distribution over cannon aim (c^t+1|st=1) is equivalent to the prior predictive mean, as the likelihood distribution (Bt |st=1) is uniformly distributed for oddball trials. The mean of the non-oddball distribution is, like in the non-changepoint case in the changepoint condition, a weighted average of the prior predictive mean and the most recent outcome. This combination can also be expressed in terms of an error-driven learning rule:

Much of the P3 literature and the explanatory accounts have tended to centre on responses to stimuli that call for an immediate choice and report. Here the authors are effectively looking at feedback-related responses and it does seem difficult to generate specific predictions from the models in this particular context but that is not necessarily a limitation of the models, more a matter of unexplored territory requiring additional simulations and empirical research. For example, if the P3 reflects the perceptual decision relating to the location of the canonball (i.e. an evidence accumulation process) then, in line with the expectation-related bound modulations proposed in sequential sampling models, one would expect larger responses for less expected canonball locations and this would effectively fit the bill of a surprise response and would be expected to relate to conditional behaviour updating. Alternatively, and the peak timing of the P3 might speak to this, the P3 may largely/partly reflect the process of selecting the next shield position in light of the current outcome and more surprising events may prompt more careful deliberation resulting in high decision bounds and larger signal amplitudes. Our impression is that the present results are interesting in their own right but do not necessarily arbitrate among existing explanatory accounts of the P3.

Much of the P3 literature and the explanatory accounts have tended to centre on responses to stimuli that call for an immediate choice and report. Here the authors are effectively looking at feedback-related responses and it does seem difficult to generate specific predictions from the models in this particular context but that is not necessarily a limitation of the models, more a matter of unexplored territory requiring additional simulations and empirical research. For example, if the P3 reflects the perceptual decision relating to the location of the canonball (i.e. an evidence accumulation process) then, in line with the expectation-related bound modulations proposed in sequential sampling models, one would expect larger responses for less expected canonball locations and this would effectively fit the bill of a surprise response and would be expected to relate to conditional behaviour updating. Alternatively, and the peak timing of the P3 might speak to this, the P3 may largely/partly reflect the process of selecting the next shield position in light of the current outcome and more surprising events may prompt more careful deliberation resulting in high decision bounds and larger signal amplitudes. Our impression is that the present results are interesting in their own right but do not necessarily arbitrate among existing explanatory accounts of the P3.
