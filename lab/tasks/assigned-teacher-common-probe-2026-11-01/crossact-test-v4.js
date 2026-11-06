/**
 * crossact - test
 * plugin for comprehension test trials
 * Martin Zettersten
 */

jsPsych.plugins['crossact-test'] = (function() {

  var plugin = {};
  
  var context = new AudioContext();
  
  jsPsych.pluginAPI.registerPreload('crossact-test', ['image1','image2','image3','image4','image5','image6'], 'image');
  jsPsych.pluginAPI.registerPreload('crossact-test', 'audioStim', 'audio');

  plugin.trial = function(display_element, trial) {
	  
      // default values
      trial.canvas_size = trial.canvas_size || [1024,700];
      trial.image_size = trial.image_size || [150, 150];
	  trial.audio = trial.audio || "true";
	  trial.timing_post_trial = typeof trial.timing_post_trial == 'undefined' ? 500 : trial.timing_post_trial;
	  trial.duration = trial.duration || 1000;
	  trial.imageArrayKey = trial.imageArrayKey || ["0","1","2","3","4","5"];
	  trial.circleArrayKey = trial.circleArrayKey || ["0","1","2","3","4","5"];
	  trial.imageArrayIndex = trial.imageArrayIndex || [0,1,2,3,4,5];
	  trial.circleArrayIndex = trial.circleArrayIndex || [0,1,2,3,4,5];
	  trial.button_html = trial.button_html || '<button class="jspsych-btn">%choice%</button>';
	  trial.finalPause = trial.finalPause || 250;
	  trial.audioDuration = trial.audioDuration || 1000;
	  trial.standardIm = trial.standardIm || ["stims/Bear_Smile.png"];
	  trial.standardImTalk = trial.standardImTalk || ["stims/Bear_Talk.png"];
	  trial.standardIm2 = trial.standardIm2 || ["stims/space_helmet.png"];
	  trial.objectNum = trial.objectNum || 6;
	  trial.responseKind = trial.responseKind || "click";
	  
      // if any trial variables are functions
      // this evaluates the function and replaces
      // it with the output of the function
      trial = jsPsych.pluginAPI.evaluateFunctionParameters(trial);
	  
	  display_element.append($("<svg id='jspsych-test-canvas' width=" + trial.canvas_size[0] + " height=" + trial.canvas_size[1] + "></svg>"));

      var paper = Snap("#jspsych-test-canvas");	  
	  
	  
	  var choice = "NA";
	  var choiceIm = "NA";
	  var choiceType = "NA";
	  var choiceIndex = "NA";
	  var choiceKey = "NA";
	  var choiceLabel = "NA";
	  var rt = "NA";
	  var learningStartRT = "NA";
	  var trialDuration = "NA";
	  var word1 = "NA";
	  var curImageArrayIndex = trial.imageArrayIndex;
	  var isRight = "NA";
	  
	  
	  var circle1 = paper.circle(190, 530, 100);
	  var circle2 = paper.circle(610, 530, 100);
	  var circle3 = paper.circle(190, 100, 100);
	  var circle4 = paper.circle(610, 100, 100);
	  if (trial.objectNum == 6) {
		  var circle5 = paper.circle(700, 315, 100);
		  var circle6 = paper.circle(100, 315, 100);
	  };
	  
	  var standardTalk = paper.image(trial.standardImTalk,311,200,179,258);
	  var standardBack = paper.image(trial.standardIm,311,200,179,258);
	  var standard2 = paper.image(trial.standardIm2,288,162,230,210);
	  var standard = paper.image(trial.standardIm,311,200,179,258);
	  standard.attr({opacity:0});
	  
	  //create circle set and dict
	  var circleDict = {0: circle1, 1: circle2,2: circle3, 3: circle4, 4: circle5, 5: circle6};
	  var circleSet= Snap.set(circle1,circle2,circle3,circle4,circle5,circle6);
	  
	  circleSet.attr({
	   		  fill: "#9ecae1",
	   		  stroke: "#000",
		  strokeWidth: 5});

	  
		  var imageLocations = {
			  pos1: [115, 455],
			  pos2: [535, 455],
			  pos3: [115, 25],
			  pos4: [535, 25],
			  pos5: [625, 240],
			  pos6: [25, 240],
		  };
	  
		  var image1 = paper.image(trial.image1, imageLocations["pos1"][0], imageLocations["pos1"][1], trial.image_size[0],trial.image_size[1]);
		  var image2 = paper.image(trial.image2, imageLocations["pos2"][0], imageLocations["pos2"][1], trial.image_size[0],trial.image_size[1]);
		  var image3 = paper.image(trial.image3, imageLocations["pos3"][0], imageLocations["pos3"][1], trial.image_size[0],trial.image_size[1]);
		  var image4 = paper.image(trial.image4, imageLocations["pos4"][0], imageLocations["pos4"][1], trial.image_size[0],trial.image_size[1]);
		  if (trial.objectNum == 6) {
			  var image5 = paper.image(trial.image5, imageLocations["pos5"][0], imageLocations["pos5"][1], trial.image_size[0],trial.image_size[1]);
			  var image6 = paper.image(trial.image6, imageLocations["pos6"][0], imageLocations["pos6"][1], trial.image_size[0],trial.image_size[1]);
		  };
 if (trial.objectNum == 6) {
  var imageDict = {0: image1, 1: image2,2: image3, 3: image4, 4: image5, 5: image6};
} else {
  var imageDict = {0: image1, 1: image2,2: image3, 3: image4};
}
	  //create audio
	  //var audio = new Audio(trial.audio);

	  var start_time = (new Date()).getTime();
	  var test_start_rt = "NA";
	  var test_start_time = "NA";
	    
	  var trial_data={};
	  
	  if (trial.responseKind == "touch") {
		  standard.touchstart(function() {
			  standard.untouchstart();
			  standardBack.attr({opacity: 0});
			 test_start_time = (new Date()).getTime();
			 console.log(test_start_time);
			  test_start_rt = test_start_time - start_time;
			  playSound(trial.audioStim);
			  start_test(test_start_time);
		  });
	  } else {
		  standard.click(function() {
			  standard.unclick();
			  standardBack.attr({opacity: 0});
			 test_start_time = (new Date()).getTime();
			 console.log(test_start_time);
			  test_start_rt = test_start_time - start_time;
			  playSound(trial.audioStim);
			  start_test(test_start_time);
		  });
	  }
	  
	  
	  function start_test(test_start_time) {
		  if (trial.responseKind == "touch") {
			  image1.touchstart(function() {
		  		  var end_time = (new Date()).getTime();
				  console.log(end_time);
				  console.log(test_start_time);
		  		  rt = end_time - test_start_time;
		  		  circle1.attr({
		  			  fill: "#FFD3D6"
		  		  });
		  		  choiceIndex = 0;
		  		  finalize_test(choiceIndex,rt);
			  });
		  
			  image2.touchstart(function() {
		  		  var end_time = (new Date()).getTime();
				  console.log(end_time);
				  console.log(test_start_time);
		  		  rt = end_time - test_start_time;
		  		  circle2.attr({
		  			  fill: "#FFD3D6"
		  		  });
		  		  choiceIndex = 1;
		  		  finalize_test(choiceIndex,rt);
			  });

		  image3.touchstart(function() {
		  		  var end_time = (new Date()).getTime();
				  console.log(end_time);
				  console.log(test_start_time);
		  		  rt = end_time - test_start_time;
		  		  circle3.attr({
		  			  fill: "#FFD3D6"
		  		  });
		  		  choiceIndex = 2;
		  		  finalize_test(choiceIndex,rt);
		  });

		  image4.touchstart(function() {
		  		  var end_time = (new Date()).getTime();
				  console.log(end_time);
				  console.log(test_start_time);
		  		  rt = end_time - test_start_time;
		  		  circle4.attr({
		  			  fill: "#FFD3D6"
		  		  });
		  		  choiceIndex = 3;
		  		  finalize_test(choiceIndex,rt);
		  });
		  if (trial.objectNum == 6) {
		  image5.touchstart(function() {
		  		  var end_time = (new Date()).getTime();
				  console.log(end_time);
				  console.log(test_start_time);
		  		  rt = end_time - test_start_time;
		  		  circle5.attr({
		  			  fill: "#FFD3D6"
		  		  });
		  		  choiceIndex = 4;
		  		  finalize_test(choiceIndex,rt);
		  });

		  image6.touchstart(function() {
		  		  var end_time = (new Date()).getTime();
				  console.log(end_time);
				  console.log(test_start_time);
		  		  rt = end_time - test_start_time;
		  		  circle6.attr({
		  			  fill: "#FFD3D6"
		  		  });
		  		  choiceIndex = 5;
		  		  finalize_test(choiceIndex,rt);
		  });
	  };
		  } else {
			  image1.click(function() {
		  		  var end_time = (new Date()).getTime();
				  console.log(end_time);
				  console.log(test_start_time);
		  		  rt = end_time - test_start_time;
		  		  circle1.attr({
		  			  fill: "#FFD3D6"
		  		  });
		  		  choiceIndex = 0;
		  		  finalize_test(choiceIndex,rt);
			  });
		  
			  image2.click(function() {
		  		  var end_time = (new Date()).getTime();
				  console.log(end_time);
				  console.log(test_start_time);
		  		  rt = end_time - test_start_time;
		  		  circle2.attr({
		  			  fill: "#FFD3D6"
		  		  });
		  		  choiceIndex = 1;
		  		  finalize_test(choiceIndex,rt);
			  });

		  image3.click(function() {
		  		  var end_time = (new Date()).getTime();
				  console.log(end_time);
				  console.log(test_start_time);
		  		  rt = end_time - test_start_time;
		  		  circle3.attr({
		  			  fill: "#FFD3D6"
		  		  });
		  		  choiceIndex = 2;
		  		  finalize_test(choiceIndex,rt);
		  });

		  image4.click(function() {
		  		  var end_time = (new Date()).getTime();
				  console.log(end_time);
				  console.log(test_start_time);
		  		  rt = end_time - test_start_time;
		  		  circle4.attr({
		  			  fill: "#FFD3D6"
		  		  });
		  		  choiceIndex = 3;
		  		  finalize_test(choiceIndex,rt);
		  });
		  if (trial.objectNum == 6) {
		  image5.click(function() {
		  		  var end_time = (new Date()).getTime();
				  console.log(end_time);
				  console.log(test_start_time);
		  		  rt = end_time - test_start_time;
		  		  circle5.attr({
		  			  fill: "#FFD3D6"
		  		  });
		  		  choiceIndex = 4;
		  		  finalize_test(choiceIndex,rt);
		  });

		  image6.click(function() {
		  		  var end_time = (new Date()).getTime();
				  console.log(end_time);
				  console.log(test_start_time);
		  		  rt = end_time - test_start_time;
		  		  circle6.attr({
		  			  fill: "#FFD3D6"
		  		  });
		  		  choiceIndex = 5;
		  		  finalize_test(choiceIndex,rt);
		  });
	  };
		  	
		  }

  };
	  
	  function finalize_test(choiceIndex,rt) {
		  if (trial.responseKind == "touch") {
			  image1.untouchstart();
			  image2.untouchstart();
			  image3.untouchstart();
			  image4.untouchstart();
			  if (trial.objectNum == 6) {
			  image5.untouchstart();
			  image6.untouchstart();
		  };
	  } else {
		  image1.unclick();
		  image2.unclick();
		  image3.unclick();
		  image4.unclick();
		  if (trial.objectNum == 6) {
		  image5.unclick();
		  image6.unclick();
	  };
  }
		  
		  //choice info
		  choiceLabel=trial.wordList[choiceIndex];
		  choice=trial.imageList[choiceIndex];
		  choiceKey=trial.imageArrayIndex[choiceIndex];
		  choiceImage = imageDict[choiceKey];
		  choiceCircle = circleDict[choiceKey];
		  console.log(trial.targetImage);
		  console.log(choice);
		  console.log(choice == trial.targetImage);
		  if (choice == trial.targetImage) {
			  isRight = 1;
		  } else {
			  isRight = 0;
		  };
		  

    	setTimeout(function(){
    			endTrial();
    	},1000);

	  };


	  function playLearningTrial() {
		  
		var learningStartTime = (new Date()).getTime();
	      
		playSound("stims/"+choiceLabel+".m4a");
  		setTimeout(function(){
  			endTrial();
  		},trial.audioDuration);
		  
	  };
	  
	//function to play audio
	  function playSound(buffer) {
	    var source = context.createBufferSource(); // creates a sound source
	    source.buffer = jsPsych.pluginAPI.getAudioBuffer(buffer);                    // tell the source which sound to play
	    source.connect(context.destination);       // connect the source to the context's destination (the speakers)
	    source.start(0);                           // play the source now
	  };
	  
      function endTrial() {
		var final_time = (new Date()).getTime();
		trialDuration = final_time - start_time;
		
		if (trial.objectNum == 6) {
        var trial_data = {
			"image1": trial.image1,
			"image2": trial.image2,
			"image3": trial.image3,
			"image4": trial.image4,
			"image5": trial.image5,
			"image6": trial.image6,
			"choice": choiceIndex,
			"choiceImage": choice,
			"learningLocationChoice": trial.learningPos,
			"choiceLabel":choiceLabel,
			"rt": rt,
			"isRight": isRight,
			"testStartRT": test_start_rt,
			"trialDuration": trialDuration,
			"targetLabel": trial.audioStim,
			"targetImage": trial.targetImage
		};
	} else {
	        var trial_data = {
				"image1": trial.image1,
				"image2": trial.image2,
				"image3": trial.image3,
				"image4": trial.image4,
				"choice": choiceIndex,
				"choiceImage": choice,
				"learningLocationChoice": trial.learningPos,
				"choiceLabel":choiceLabel,
				"rt": rt,
				"isRight": isRight,
				"testStartRT": test_start_rt,
				"trialDuration": trialDuration,
				"targetLabel": trial.audioStim,
				"targetImage": trial.targetImage
			};
		}
		

		setTimeout(function(){
			display_element.html('');
			jsPsych.finishTrial(trial_data);
		},trial.finalPause);
		
      };
  };	  
		
		return plugin;
})();
