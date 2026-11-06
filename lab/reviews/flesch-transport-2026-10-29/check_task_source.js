/* Run with Node: const fs=require('fs'); console.log(new Function(fs.readFileSync(__filename,'utf8'))()); */

var console={log:function(){}};
var participant_id='synthetic', participant_gender='synthetic', participant_age='NA', participant_task='synthetic', participant_turker='synthetic';
var thisId='', seed=1;
function getQueryParams(){return {id:thisId};}
function colon(a,b){return Array.from({length:b-a+1},(_,i)=>a+i);}
function repmat(a,n){var z=[];for(var q=0;q<n;q++)z=z.concat(a);return z;}
function bin2num(a){return a?1:0;}
function shuffle(x){x=x.slice();for(var j=x.length-1;j>0;j--){seed=(Math.imul(1664525,seed)+1013904223)>>>0;var k=seed%(j+1);var h=x[j];x[j]=x[k];x[k]=h;}return x;}
function isnan(x){return Number.isNaN(x);}
function getTimestamp(){return 0;}
function getSecs(){return .5;}
function sum(a){return a.reduce((x,y)=>x+y,0);}

/* **************************************************************************************

Sets all the important parameters
(c) Timo Flesch, 2016 [timo.flesch@gmail.com]

Based on earlier version of script by jdobalaguer@gmail.com
************************************************************************************** */

// globals
var sdata;
var edata;
var parameters;
var board;
var coding;

function setExperiment() {


  // EDATA ----------------
  edata = {};
  // expt
  edata.expt_subject = participant_id;
  edata.expt_sex     = participant_gender;
  edata.expt_age     = participant_age;
  edata.expt_task    = participant_task;
  edata.expt_turker  = participant_turker;

  // PARAMETERS -----------
  parameters = {};

  // TIMINGS
  parameters.cue_timein       =  0;
  parameters.cue_timeout      =  500;
  parameters.stimulus_timein  =  500;
  parameters.stimulus_timeout =  2500;
  parameters.response_timeout =  2500;  // response time
  parameters.warnings_timeout =  2500;  // response warning time
  parameters.feedback_timein  =   500;  // delay after action until feedback is displayed
  parameters.feedpos_timeout  =  1500;  // feedback time (good)
  parameters.feedneg_timeout  =  1500;  // feedback time (bad)


  // TASK
  set_subjParams();  // obtains subject-specific params from URL (index.html?id=NUMS)

  parameters.keyStr           =         (parameters.keyassignment)? (['left: accept',' right: reject']) : (['right: accept',' left: reject']);
  parameters.gardenURL        =         "orchards/"
  parameters.treeURL          =         "trees/stims/";
  parameters.keyURL           =         "lib/png/";
  parameters.exemplar_ids_train =       "a,b,c,d".split(',');
  parameters.exemplar_ids_test =        "e,f,g,h".split(',');


  parameters.nb_branchiness   =         5; // how many levels?
  parameters.nb_leafiness     =         5; // how many levels?
  parameters.nb_reps          =         2; // how many repetitions within each block?
  parameters.nb_reps_test     =         1; // how many reps of each task within test ?
  parameters.nb_tasks_test    =         2; // how many tasks within test block? needs to be 2 to cover both tasks!!
  parameters.nb_unique        =         parameters.exemplar_ids_train.length; // 4 unique exemplars 
  parameters.nb_trials_train  =         parameters.nb_branchiness*parameters.nb_leafiness*parameters.nb_unique*parameters.nb_reps; //200 trials per training task 
  parameters.nb_trials_test   =         parameters.nb_branchiness*parameters.nb_leafiness*parameters.nb_unique*parameters.nb_tasks_test; // 100 trials per training task 
  parameters.nb_blocks        =         2; // has to be at least 2 (both tasks
  parameters.nb_blocks_test   =         1; // .. + test)
  parameters.nb_total_train   =         (parameters.nb_blocks)*parameters.nb_trials_train; // 400 training trials in total
  parameters.nb_total_test    =         parameters.nb_trials_test; // 200 training trials in total
  parameters.val_categories   =         [-1,-1,0,1,1];
  parameters.val_rewards      =         [-50,-25,0,25,50];


  // VISUALS
  parameters.visuals              =        {};
  // size
  parameters.visuals.size         =        {};
  parameters.visuals.size.garden  =        [400,400]; // context
  parameters.visuals.size.stim    =        [200,200]; // stimulus tree
  parameters.visuals.size.fbt     =        [150,150]; // feedback tree
  parameters.visuals.size.keyIMG  =        [75,75];   // size of key image

  // colors
  parameters.visuals.cols         =        {};
  parameters.visuals.cols.fbn_pos =        "#080";  // positive feedback
  parameters.visuals.cols.fbn_neg =        "#D00";  // negative feedback
  parameters.visuals.cols.fbn_neu =        "black"; // neutral feedback
  parameters.visuals.cols.fb_bg   =        "grey";  // feedback background

  // misc
  parameters.visuals.blurlvl      =             5;  // how much blur?


  // TEXT
  parameters.txt                          =         {};
  parameters.txt.trainBreakBlocked        =     "A couple of seconds' break. \n \n In the next block, you'll do a different task! \n \n There will be a new orchard and different features of the trees indicate their growth success. \n \n Thus, you need to learn from scratch. \n \n Press the SPACE bar when you're ready to continue";

  parameters.txt.trainInstrBlocked        =     "This is the first block of the experiment. \n \n The orchard will be the same for the entire block and a picture of it will be presented on each trial before you'll see the tree. \n \n Via trial and error, you'll learn the rule that tells you which trees grow best in this particular garden. \n \n Press the " + parameters.keyStr[0].split(':').slice(0,1)[0].toUpperCase() + " arrow key if you would like to plant the tree in your orchard, \n \n or the " + parameters.keyStr[1].split(':').slice(0,1)[0].toUpperCase() + " arrow key if you don't want to plant the tree. \n \n Press the SPACE bar when you're ready to continue";

  parameters.txt.trainBreakInterleaved    =     "A couple of seconds' break. \n \n In the next block, you'll do the same experiment! \n \n Nothing has changed. We just want to give you enough time to discover the rules. \n \n Press the SPACE bar when you're ready to continue";

  parameters.txt.trainInstrInterleaved    =     "This is the first block of the experiment. \n \n Please pay attention to the cue at the beginning of each trial that tells you in which orchard you're currently in! \n \n The cue is just an image of one of the two gardens (North or South). \n \n The cue will change every few trials!. \n \n You need to learn two rules: \n \n Which trees grow best in the North garden, and \n \n Which trees grow best in the South garden? \n \n Press the " + parameters.keyStr[0].split(':').slice(0,1)[0].toUpperCase() + " arrow key if you would like to plant the tree in your orchard, \n \n or the " + parameters.keyStr[1].split(':').slice(0,1)[0].toUpperCase() + " arrow key if you don't want to plant the tree. \n \n Press the SPACE bar when you're ready to continue";

  parameters.txt.testInstructions         =     "Now let's see how well you've learned the rules for both gardens! \n \n In the next block, you'll have to plant trees in both gardens, using the knowledge that you've acquired so far! \n \n At the beginning of each trial, you'll see an image of the orchard you're currently in. (North or South). \n \n Then, you'll see a tree and have to decide whether to plant it or not. \n \n  WE WON'T GIVE YOU FEEDBACK. THIS IS THE TEST SESSION. \n \n Press the SPACE bar when you're ready to continue";




  // SDATA ----------------
  sdata = {};
  // expt
  sdata.expt_index        = []; // trial IDX (total)
  sdata.expt_trial        = []; // trial IDX (within block)
  sdata.expt_block        = []; // block IDX
  sdata.expt_branchIDX    = []; // level of branchiness
  sdata.expt_leafIDX      = []; // level of leafiness
  sdata.expt_rewardIDX    = []; // reward: neg & pos
  sdata.expt_catIDX       = []; // category: plant vs don't plant
  sdata.expt_contextIDX   = []; // task: north vs south
  createSdata();

  // vbxi
  sdata.vbxi_category     = [];



  // resp
  sdata.resp_timestamp    = []; // time when button was pressed 
  sdata.resp_reactiontime = []; // RT wrt stimulus ONSET 
  sdata.resp_category     = []; // responded category
  sdata.resp_correct      = []; // trial-wise accuracy
  sdata.resp_reward       = []; // trial-wise received reward
  sdata.resp_return       = []; // trial-wise cummulative reward (=return)

  // BOARD ----------------
  board = {}; // will contain the canvas

  // CODING ---------------
  coding = {}; // exp logic
  // index
  coding.task   = 0;
  coding.index  = 0;
  coding.trial  = 0;
  coding.block  = 0;
  coding.return = 0;
  // other
  coding.answering = false;
  coding.timestamp = NaN;
}



function set_subjParams() {
  /*
    grabs params from url argument
    input structure:
    ?id=abcd
    a = 1/2/3 = bAB,bBA,interl
    b = 1:8   = cardinal: nn,ff,fn,nf, diagonal: nn,ff,fn,nf (f=flipped, n=normal)
    c = 0/1/3   = flip key assign or not, random otherwise
    d = 1,2,3   = blockiness: 2,20,200
  */
  input = getQueryParams();


  if (typeof(input.id)=="undefined" ) {
    parameters.task_id       = 'blocked-A-B'.split('-'); // blocked north south
    parameters.val_rewAssignment = 	  1; // no flipped assignments, cardinal boundary
    parameters.keyassignment =            0; // l-no r-yes
    parameters.blockiness    =          200; // how many trials of one task per block?
  }

  else {
    input.id = input.id.split('').map(Number);
    // 1. curriculum
    switch (input.id[0]) {
      case  1:
        parameters.task_id = 'blocked-A-B'.split('-');
        break;
      case 2:
        parameters.task_id = 'blocked-B-A'.split('-');
        break;
      case 3:
        parameters.task_id = 'interleaved-A-B'.split('-');
        break;
      default:
        parameters.task_id = 'blocked-A-B'.split('-');
        break;
    }

    // 2. reward & boundary 
    parameters.val_rewAssignment   = input.id[1]; // second and third items

    // 3. keys
    parameters.keyassignment =    (input.id[2]==3) ? (randi(2,1)) : (input.id[2]); // 0: l-no r-yes, 1: l-yes r-no 
    
    // 4. blockiness (becomes irrelevant for interleaved design)
    switch (input.id[3]) {
	case 1:
		parameters.blockiness = 2;
		break;
	case 2:
		parameters.blockiness = 20;
		break;
	case 3: 
		parameters.blockiness = 200;
		break;
	default:
		parameters.blockiness = 200;
		break;
    }
    // however, if interleaved, set back to 200
    if(input.id[0]==3){
	    parameters.blockiness = 200;
    }
  }
  console.log(parameters.task_id)
  console.log(parameters.blockiness)
  console.log(parameters.val_rewAssignment)
}


/* **************************************************************************************

Creates experimental conditions.
(c) Timo Flesch, 2016 [timo.flesch@gmail.com]


************************************************************************************** */
shuffSwitch = 0;

function createSdata(){
/*
	here happens all the magic
*/
	// index from very first to very last trial of WHOLE exp
	sdata.expt_index 	= colon(1,parameters.nb_total_train+parameters.nb_total_test);

	// index from first to last trial within each block
	sdata.expt_trial 	= repmat(colon(1,parameters.nb_trials_train),parameters.nb_blocks).concat(repmat(colon(1,parameters.nb_trials_test),parameters.nb_blocks_test));

	// generate block indices
	sdata.expt_block 	= gen_blockVect();

	// generate context indices (to distinguish between branch and leaf tasks)
	sdata.expt_contextIDX   = gen_contextVect();

	// generate session indices (training 1 vs test 2)
	sdata.expt_sessIDX      = gen_sessVect();

	// generate branchiness indices (rep([1,1,1,1,1,2,2,2......5,5,5,5]))
	sdata.expt_branchIDX 	= gen_branchVect();

	// generate leafiness indices (rep([1,2,3,4,5,1,2,3,4,5....]))
	sdata.expt_leafIDX 	= gen_leafVect();

	// generate vector with exemplar indices [I have several exemplars per level]
	sdata.expt_exemplarIDX  = gen_exemplarVect();

	// generate category label indices (depending on task order)
	sdata.expt_catIDX	= gen_catVect();

	// generate vector with reward values, depending on task and feature level
	sdata.expt_rewardIDX    = gen_rewardVect();

	// generate vector with "optimal" return up to each trial n (for performance assessment)
	sdata.expt_returnOPT    = [];  //done on the fly
	sdata.expt_rewardOPT    = [];


	// magic dust
	shuffle_trials(shuffSwitch);

	if (parameters.blockiness < 200 && shuffSwitch == 1) {
		shrink_blocks();
	}
}


function gen_blockVect(){
/*
	generates array of block indices
*/
	tmp = new Array();
	// training blocks
	for(i=1;i<=parameters.nb_blocks;i++){
		var thisBlock = repmat(i,parameters.nb_trials_train);
		tmp = tmp.concat(thisBlock);
	}
	// test block
	for(i=parameters.nb_blocks+1;i<=parameters.nb_blocks+parameters.nb_blocks_test;i++) {
		var thisBlock = repmat(i,parameters.nb_trials_test);
		tmp = tmp.concat(thisBlock);
	}
	return tmp;
}


function gen_sessVect() {
/*
	generates vector with session indices
	idx 1 = training session
	idx 2 = test session
*/
	return repmat(1,parameters.nb_total_train).concat(repmat(2,parameters.nb_total_test));
}


function gen_contextVect(){
/*
	generates vector with task indices
	idx 1 = leaf task
	idx 2 = branch task
	ix  3 = test task [need to get rid of this....]
*/

	var blockTask1 = repmat(1,parameters.nb_trials_train);
	var blockTask2 = repmat(2,parameters.nb_trials_train);
	var blockTask3 = repmat(1,parameters.nb_trials_test/parameters.nb_tasks_test).concat(repmat(2,parameters.nb_trials_test/parameters.nb_tasks_test)); // half one task, half other task
	if (parameters.task_id.slice(1).join('-') == 'A-B') {
		return blockTask1.concat(blockTask2).concat(blockTask3);
	}
	else if (parameters.task_id.slice(1).join('-') == 'B-A') {
		return blockTask2.concat(blockTask1).concat(blockTask3);
	}
}


function gen_leafVect(){
/*
	generates vector of leafiness levels
*/
	// training & test
	tmp = repmat(colon(1,parameters.nb_leafiness),sdata.expt_index.length/parameters.nb_leafiness);

	return tmp;
}


function gen_branchVect(){
/*
   generates vector of branchiness levels
*/
	var tmp       = new Array();
	// train
	var trainBlock = [];
	for(i=1;i<=parameters.nb_unique*parameters.nb_blocks;i++){
		for(j=1;j<=parameters.nb_branchiness;j++){
			var thisBranch = repmat(j,parameters.nb_leafiness);
			tmp = tmp.concat(thisBranch);
		}
	}
	trainBlock = repmat(tmp,parameters.nb_reps);

	//test
	var testBlock = [];
	var tmp       = [];
	for(i=1;i<=parameters.nb_unique*parameters.nb_blocks_test;i++){
		for(j=1;j<=parameters.nb_branchiness;j++){
			var thisBranch = repmat(j,parameters.nb_leafiness);
			tmp = tmp.concat(thisBranch);
		}
	}
	testBlock = repmat(tmp,parameters.nb_tasks_test);
	return trainBlock.concat(testBlock);
}


function gen_catVect() {
/* 
 * simplified catvect generation to avoid redundancy
 */
	catVect = [];
	// 1. obtain catard and cat matrices 
	condMatrices = loadTaskMatrix(parameters.val_rewAssignment);
	// 2. loop through trials and assign category  accordingly
	for(var ii = 0; ii< sdata.expt_contextIDX.length; ii++) {
    		if (sdata.expt_contextIDX[ii]==1) {
			catVect[ii] = condMatrices.catMat_leaf[sdata.expt_leafIDX[ii]-1][sdata.expt_branchIDX[ii]-1];
	        }
	        else {
		        catVect[ii] = condMatrices.catMat_branch[sdata.expt_leafIDX[ii]-1][sdata.expt_branchIDX[ii]-1];
	    	}
	}
	return catVect;
}


function gen_rewardVect() {
/* 
 * simplified rewvect generation to avoid redundancy
 */
	rewVect = [];
	// 1. obtain reward and rew matrices 
	condMatrices = loadTaskMatrix(parameters.val_rewAssignment);
	// 2. loop through trials and assign rewegory  accordingly
	for(var ii = 0; ii< sdata.expt_contextIDX.length; ii++) {
    		if (sdata.expt_contextIDX[ii]==1) {
			rewVect[ii] = condMatrices.rewMat_leaf[sdata.expt_leafIDX[ii]-1][sdata.expt_branchIDX[ii]-1];
	        }
	        else {
		        rewVect[ii] = condMatrices.rewMat_branch[sdata.expt_leafIDX[ii]-1][sdata.expt_branchIDX[ii]-1];
	    	}
	}
	return rewVect;
}

function gen_exemplarVect() {
/*
	generates vector of exemplar indices	,
	both for training and test phase (note: I want different exemplars)
*/
	exemplarVectTrain = [];
	for(var blockID=0;blockID<parameters.nb_blocks;blockID++) {
		for(var ii=0;ii<parameters.exemplar_ids_train.length;ii++) {
			exemplarVectTrain = exemplarVectTrain.concat(repmat(parameters.exemplar_ids_train[ii],parameters.nb_branchiness*parameters.nb_leafiness));

		}
	}

	exemplarVectTest = [];
	for(var blockID=0;blockID<parameters.nb_blocks_test;blockID++) {
		for(var ii=0;ii<parameters.exemplar_ids_test.length;ii++) {
			exemplarVectTest = exemplarVectTest.concat(repmat(parameters.exemplar_ids_test[ii],parameters.nb_branchiness*parameters.nb_leafiness));

		}
	}


	return repmat(exemplarVectTrain,parameters.nb_reps).concat(repmat(exemplarVectTest,parameters.nb_reps_test*parameters.nb_tasks_test));
}



function shrink_blocks() {
/*
	if parameters.blockiness <200, this funct reduces blocksize accordingly	
	important: run after shuffling!!!
 */

	 sdata.expt_leafIDX 	=      shrink_vect(sdata.expt_leafIDX);
	 sdata.expt_branchIDX 	=    shrink_vect(sdata.expt_branchIDX);
	 sdata.expt_catIDX	=       shrink_vect(sdata.expt_catIDX);
	 sdata.expt_exemplarIDX =  shrink_vect(sdata.expt_exemplarIDX);
	 sdata.expt_contextIDX	=   shrink_vect(sdata.expt_contextIDX);
	 sdata.expt_rewardIDX   =    shrink_vect(sdata.expt_rewardIDX);
}

function shrink_vect(thisVect) {
/*
	takes a vector of two training blocks and splits into smaller blocks
 */
	// init empty vect
	newVect = [];
	// extract first and second task:
	trialsTrain1 = thisVect.slice(0,parameters.nb_trials_train);
	trialsTrain2 = thisVect.slice(parameters.nb_trials_train,parameters.nb_total_train);
	trialsTest   = thisVect.slice(parameters.nb_total_train,thisVect.length);
	// loop from 0 over blockiness to vectlength-blockiness
	//for each iteration: add #blockiness items from first and second task successively to new rect, return this
	for(var ii=0;ii<=trialsTrain1.length-parameters.blockiness;ii=ii+parameters.blockiness) {
		newVect = newVect.concat(trialsTrain1.slice(ii,ii+parameters.blockiness),trialsTrain2.slice(ii,ii+parameters.blockiness));
	}
	newVect = newVect.concat(trialsTest);
	return newVect;
}


function shuffle_trials(){
/*
	let's create some chaos...
*/
	 var shuffIDX = [];
	 shuffIDX = mk_shuffIDX();
	 sdata.expt_leafIDX 	=      shuffle_vect(shuffIDX,sdata.expt_leafIDX);
	 sdata.expt_branchIDX 	=    shuffle_vect(shuffIDX,sdata.expt_branchIDX);
	 sdata.expt_catIDX	=       shuffle_vect(shuffIDX,sdata.expt_catIDX);
	 sdata.expt_exemplarIDX =  shuffle_vect(shuffIDX,sdata.expt_exemplarIDX);
	 sdata.expt_contextIDX	=   shuffle_vect(shuffIDX,sdata.expt_contextIDX);
	 sdata.expt_rewardIDX   =    shuffle_vect(shuffIDX,sdata.expt_rewardIDX);
	 shuffSwitch = 1;
}


function mk_shuffIDX() {
/*
	shuffle idces
*/
	var shuffIDX = [];
	var startIDX =  0;

	// training
	switch(bin2num(parameters.task_id.slice(0,1) == 'blocked')){
		case 1:
			for(var i=1;i<=parameters.nb_blocks;i++){
				var tmp = [];
				tmp = shuffle(colon(startIDX,startIDX+parameters.nb_trials_train-1));
				shuffIDX = shuffIDX.concat(tmp);
				startIDX = startIDX+parameters.nb_trials_train;
			}

			break;

		case 0:
			shuffIDX = shuffle(colon(0,parameters.nb_total_train-1));

			break;
    }

    // test
    shuffIDX = shuffIDX.concat(shuffle(colon(parameters.nb_total_train,parameters.nb_total_train+parameters.nb_total_test-1)));
    return shuffIDX;
}


function shuffle_vect(shuffIDX,vectToShuffle){
/*
	shuffle vector with set of new indices
*/
	for(var i=0;i<shuffIDX.length;i++){
		vectToShuffle.push(vectToShuffle[shuffIDX[i]]);
	}
	vectToShuffle.splice(0,shuffIDX.length);
	return vectToShuffle;
}


function loadTaskMatrix(matID) {
	taskMatrices = {};
	switch (matID){
		case 1:
			 // high high
			 taskMatrices.rewMat_leaf = [[-50,-50,-50,-50,-50],
			 			     [-25,-25,-25,-25,-25],
						     [0,0,0,0,0],
						     [25,25,25,25,25],
						     [50,50,50,50,50]];
	
			 taskMatrices.catMat_leaf = [[-1,-1,-1,-1,-1],
			 			     [-1,-1,-1,-1,-1],
						     [0,0,0,0,0],
						     [1,1,1,1,1],
						     [1,1,1,1,1]];
			
			 taskMatrices.rewMat_branch = [[-50,-25,0,25,50],
			 		  	       [-50,-25,0,25,50],
					  	       [-50,-25,0,25,50],
					  	       [-50,-25,0,25,50],
					  	       [-50,-25,0,25,50]];
			 
			 taskMatrices.catMat_branch = [[-1,-1,0,1,1],
			 		  	       [-1,-1,0,1,1],
					  	       [-1,-1,0,1,1],
					  	       [-1,-1,0,1,1],
					  	       [-1,-1,0,1,1]];
			break;
		case 2:	  
			  // low low
			  taskMatrices.rewMat_leaf = [[50,50,50,50,50],
			  		 	      [25,25,25,25,25],
					 	      [0,0,0,0,0],
					 	      [-25,-25,-25,-25,-25],
					 	      [-50,-50,-50,-50,-50]];
			
			 taskMatrices.catMat_leaf = [[1,1,1,1,1],
			 			     [1,1,1,1,1],
						     [0,0,0,0,0],
						     [-1,-1,-1,-1,-1],
						     [-1,-1,-1,-1,-1]];
			
			 taskMatrices.rewMat_branch = [[50,25,0,-25,-50],
			 		  	       [50,25,0,-25,-50],
					  	       [50,25,0,-25,-50],
					  	       [50,25,0,-25,-50],
					  	       [50,25,0,-25,-50]];
			
			 taskMatrices.catMat_branch = [[1,1,0,-1,-1],
			 		  	       [1,1,0,-1,-1],
					  	       [1,1,0,-1,-1],
					  	       [1,1,0,-1,-1],
					  	       [1,1,0,-1,-1]];
			break;
		
		case 3:
			  // low high		  
			  taskMatrices.rewMat_leaf = [[50,50,50,50,50],
			  		 	      [25,25,25,25,25],
					 	      [0,0,0,0,0],
					 	      [-25,-25,-25,-25,-25],
					 	      [-50,-50,-50,-50,-50]];
			
			 taskMatrices.catMat_leaf = [[1,1,1,1,1],
			 			     [1,1,1,1,1],
						     [0,0,0,0,0],
						     [-1,-1,-1,-1,-1],
						     [-1,-1,-1,-1,-1]];
			
			 taskMatrices.rewMat_branch = [[-50,-25,0,25,50],
			 		  	       [-50,-25,0,25,50],
					  	       [-50,-25,0,25,50],
					  	       [-50,-25,0,25,50],
					  	       [-50,-25,0,25,50]];
			
			 taskMatrices.catMat_branch = [[-1,-1,0,1,1],
			 		  	       [-1,-1,0,1,1],
					  	       [-1,-1,0,1,1],
					  	       [-1,-1,0,1,1],
					  	       [-1,-1,0,1,1]];
			break;
		
		case 4:
			  // high low 		  
			 taskMatrices.rewMat_leaf = [[-50,-50,-50,-50,-50],
			 			     [-25,-25,-25,-25,-25],
						     [0,0,0,0,0],
						     [25,25,25,25,25],
						     [50,50,50,50,50]];
			
			 taskMatrices.catMat_leaf = [[-1,-1,-1,-1,-1],
			 			     [-1,-1,-1,-1,-1],
						     [0,0,0,0,0],
						     [1,1,1,1,1],
						     [1,1,1,1,1]];
			
			 taskMatrices.rewMat_branch = [[50,25,0,-25,-50],
			 		  	       [50,25,0,-25,-50],
					  	       [50,25,0,-25,-50],
					  	       [50,25,0,-25,-50],
					  	       [50,25,0,-25,-50]];
			
			 taskMatrices.catMat_branch = [[1,1,0,-1,-1],
			 		  	       [1,1,0,-1,-1],
					  	       [1,1,0,-1,-1],
					  	       [1,1,0,-1,-1],
					  	       [1,1,0,-1,-1]];
			break;
	
		case 5:
			 // high high
			 taskMatrices.rewMat_leaf = [[-50,-50,-50,-25,0],
			 			     [-50,-50,-25,0,25],
						     [-50,-25,0,25,50],
						     [-25,0,25,50,50],
						     [0,25,50,50,50]];
	
			 taskMatrices.catMat_leaf = [[-1,-1,-1,-1,0],
			 			     [-1,-1,-1,0,1],
						     [-1,-1,0,1,1],
						     [-1,0,1,1,1],
						     [0,1,1,1,1]];
			
			 taskMatrices.rewMat_branch = [[0,25,50,50,50],
			 		  	       [-25,0,25,50,50],
					  	       [-50,-25,0,25,50],
					  	       [-50,-50,-25,0,25],
					  	       [-50,-50,-50,-25,0]];
			 
			 taskMatrices.catMat_branch = [[0,1,1,1,1],
			 		  	       [-1,0,1,1,1],
					  	       [-1,-1,0,1,1],
					  	       [-1,-1,-1,0,1],
					  	       [-1,-1,-1,-1,0]];
			break;
		case 6:	  
			  // low low
			  taskMatrices.rewMat_leaf = [[50,50,50,25,0],
			 			      [50,50,25,0,-25],
						      [50,25,0,-25,-50],
						      [25,0,-25,-50,-50],
						      [0,-25,-50,-50,-50]];
			
			 taskMatrices.catMat_leaf = [[1,1,1,1,0],
			 			     [1,1,1,0,-1],
						     [1,1,0,-1,-1],
						     [1,0,-1,-1,-1],
						     [0,-1,-1,-1,-1]];
			
			 taskMatrices.rewMat_branch = [[0,-25,-50,-50,-50],
			 		  	       [25,0,-25,-50,-50],
					  	       [50,25,0,-25,-50],
					  	       [50,50,25,0,-25],
					  	       [50,50,50,25,0]];

			 taskMatrices.catMat_branch = [[0,-1,-1,-1,-1],
			 		  	       [1,0,-1,-1,-1],
					  	       [1,1,0,-1,-1],
					  	       [1,1,1,0,-1],
					  	       [1,1,1,1,0]];
			break;
		
		case 7:
			  // low high		  
			  taskMatrices.rewMat_leaf = [[50,50,50,25,0],
			 			      [50,50,25,0,-25],
						      [50,25,0,-25,-50],
						      [25,0,-25,-50,-50],
						      [0,-25,-50,-50,-50]];
			
			 taskMatrices.catMat_leaf = [[1,1,1,1,0],
			 			     [1,1,1,0,-1],
						     [1,1,0,-1,-1],
						     [1,0,-1,-1,-1],
						     [0,-1,-1,-1,-1]];
			
			 taskMatrices.rewMat_branch = [[0,25,50,50,50],
			 		  	       [-25,0,25,50,50],
					  	       [-50,-25,0,25,50],
					  	       [-50,-50,-25,0,25],
					  	       [-50,-50,-50,-25,0]];
			 
			 taskMatrices.catMat_branch = [[0,1,1,1,1],
			 		  	       [-1,0,1,1,1],
					  	       [-1,-1,0,1,1],
					  	       [-1,-1,-1,0,1],
					  	       [-1,-1,-1,-1,0]];
			break;
		
		case 8:
			  // high low 		  
			 taskMatrices.rewMat_leaf = [[-50,-50,-50,-25,0],
			 			     [-50,-50,-25,0,25],
						     [-50,-25,0,25,50],
						     [-25,0,25,50,50],
						     [0,25,50,50,50]];
	
			 taskMatrices.catMat_leaf = [[-1,-1,-1,-1,0],
			 			     [-1,-1,-1,0,1],
						     [-1,-1,0,1,1],
						     [-1,0,1,1,1],
						     [0,1,1,1,1]];
			
			 taskMatrices.rewMat_branch = [[0,-25,-50,-50,-50],
			 		  	       [25,0,-25,-50,-50],
					  	       [50,25,0,-25,-50],
					  	       [50,50,25,0,-25],
					  	       [50,50,50,25,0]];

			 taskMatrices.catMat_branch = [[0,-1,-1,-1,-1],
			 		  	       [1,0,-1,-1,-1],
					  	       [1,1,0,-1,-1],
					  	       [1,1,1,0,-1],
					  	       [1,1,1,1,0]];
			break;
	}
	return taskMatrices;
}		  

/*
Timo Flesch, 2016 [timo.flesch@gmail.com]
*/
// <!-- Response methods -->
function handleLeft()  {
  if(parameters.keyassignment) {
    handleResponse('Left', 1);
  }
  else {
    handleResponse('Left', 0);
  }
}


function handleRight() {
 if(parameters.keyassignment) {
    handleResponse('Right', 0);
  }
  else {
    handleResponse('Right', 1);
  }
}

function handleResponse(key,category) {
  if(coding.answering){
    if(isnan(category)) {
      handleNoResponse();
    }
    coding.answering = false;
    stopCountdown();
    clearTimeout(board.countdown.stimTimeOut); // this is important, otherwise, stim might disappear during next trial..
    saveResponse(key,category);
    hideStimuli();


    // show choice:
    showAction(category);

    if(sdata.resp_correct[coding.index]){
      setTimeout(nextTrial,parameters.feedpos_timeout);
    } else {
      setTimeout(nextTrial,parameters.feedneg_timeout);
    }

  }
}

function handleNoResponse() {

  sdata.resp_timestamp[coding.index]         = NaN;
  sdata.resp_reactiontime[coding.index]      = NaN;
  sdata.resp_category[coding.index]          = NaN;
  sdata.resp_correct[coding.index]           = NaN;
  sdata.resp_reward[coding.index]            =   0; // didn't plant tree

  if(!isFullscreen() && startedexperiment && !finishedexperiment) {
//    finishExperiment_noresponse();
  }
}

function saveResponse(key,category) {

  sdata.resp_timestamp[coding.index]         = getTimestamp();
  sdata.resp_reactiontime[coding.index]      = getSecs(coding.timestamp);
  sdata.resp_category[coding.index]          = category;
  sdata.resp_correct[coding.index]           = bin2num((sdata.expt_catIDX[coding.index]>=0)==sdata.resp_category[coding.index]);
  sdata.resp_reward[coding.index]            = sdata.expt_rewardIDX[coding.index]*category;
  sdata.resp_return[coding.index]            = (coding.trial) ? (sum(sdata.resp_reward.slice(coding.return,coding.index+1))) : (0); //cumsum within current block up to current trial.
  // save reward & return for optimal policy
  sdata.expt_rewardOPT[coding.index]         = sdata.expt_rewardIDX[coding.index]*bin2num(sdata.expt_catIDX[coding.index]>0);
  sdata.expt_returnOPT[coding.index]          = (coding.trial) ? (sum(sdata.expt_rewardOPT.slice(coding.return,coding.index+1))) : (0);

  //debugging:
  if (false) {
    console.log("**********************")
    console.log('TRIAL ' +                        coding.trial);
    console.log('task '  + sdata.expt_contextIDX[coding.index]);
    console.log(treeName);
    console.log("Stimulus Category (good or bad tree): "   +   sdata.expt_catIDX[coding.index]);
    console.log("Response Category (plant or not plant): " + sdata.resp_category[coding.index]);
    console.log('\n');
    console.log("Stimulus Reward: " + sdata.expt_rewardIDX[coding.index]);
    console.log("Optimal Reward: "  + sdata.expt_rewardOPT[coding.index]);
    console.log("Response Reward: " +    sdata.resp_reward[coding.index]);
    console.log('\n');
    console.log("Optimal Return: "  + sdata.expt_returnOPT[coding.index]);
    console.log("Response Return: " +    sdata.resp_return[coding.index]);
    console.log('\n');
    console.log("Response Correct:" +   sdata.resp_correct[coding.index]);
  }
}

var checks=[], summaries=[];
function check(x,label){if(!x)throw Error(label);checks.push(label);}
for(var regime of [1,2,3])for(var map of [1,2,3,4])for(var key of [0,1])for(var block of (regime===3?[3]:[1,2,3])){
  thisId=''+regime+map+key+block;seed=5;setExperiment();
  var inputFields=['expt_index','expt_trial','expt_block','expt_branchIDX','expt_leafIDX','expt_rewardIDX','expt_catIDX','expt_contextIDX','expt_sessIDX','expt_exemplarIDX'];
  var frozen=JSON.stringify(inputFields.map(x=>sdata[x]));
  check(sdata.expt_index.length===600,'600:'+thisId);
  check(sdata.expt_contextIDX.slice(0,400).filter(x=>x===1).length===200,'train balance:'+thisId);
  check(sdata.expt_contextIDX.slice(400).filter(x=>x===1).length===100,'test balance:'+thisId);
  check(sdata.expt_catIDX.slice(400).filter(x=>x===0).length===40,'40 boundary test:'+thisId);
  check(sdata.expt_exemplarIDX.slice(0,400).every(x=>'abcd'.includes(x)),'train exemplars:'+thisId);
  check(sdata.expt_exemplarIDX.slice(400).every(x=>'efgh'.includes(x)),'novel test exemplars:'+thisId);
  if(regime!==3){
    var nb={1:2,2:20,3:200}[block], ctx=sdata.expt_contextIDX.slice(0,400);
    var first=regime===1?1:2, other=first===1?2:1;
    check(ctx.every((v,i)=>v===(Math.floor(i/nb)%2===0?first:other)),'fixed block length:'+thisId);
  }
  coding.index=0;coding.trial=1;coding.return=0;saveResponse('synthetic',0);
  check(frozen===JSON.stringify(inputFields.map(x=>sdata[x])),'choice 0 no input mutation:'+thisId);
  saveResponse('synthetic',1);
  check(frozen===JSON.stringify(inputFields.map(x=>sdata[x])),'choice 1 no input mutation:'+thisId);
  summaries.push(thisId);
}
return {configurations:summaries.length,checks:checks.length,passed:true,scope:'Synthetic task inputs and artificial responses only; no MAT payload read',helpers:'Locally supplied colon/repmat/bin2num/seeded shuffle; source generator/response functions unchanged',preserved_initial_check:'Initial all-expt-fields check failed because saveResponse fills expt_rewardOPT and expt_returnOPT. Input fields were then explicitly restricted to the ten pre-response schedule fields; no source code changed.'};

