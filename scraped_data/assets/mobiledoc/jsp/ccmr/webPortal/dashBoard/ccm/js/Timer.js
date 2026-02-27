var hasTimer = false;
// Init timer start
function start(rowId){
	hasTimer = true;
	$('.timer'+rowId).timer({
		editable : true,
		seconds:0
	});
	$('.start-timer-btn'+rowId+', .resume-timer-btn'+rowId).addClass('hidden');
	$('.pause-timer-btn'+rowId+', .remove-timer-btn'+rowId+', .reset-timer-btn'+rowId).removeClass('hidden');
}

// Init timer resume
function resume(rowId){
	$('.timer'+rowId).timer('resume');
	$('.resume-timer-btn'+rowId+', .start-timer-btn'+rowId).addClass('hidden');
	$('.pause-timer-btn'+rowId+', .remove-timer-btn'+rowId+', .reset-timer-btn'+rowId).removeClass('hidden');
}

//Init timer pause
function pause(rowId){
	$('.timer'+rowId).timer('pause');
	$('.pause-timer-btn'+rowId+', .start-timer-btn'+rowId).addClass('hidden');
	$('.resume-timer-btn'+rowId+', .remove-timer-btn'+rowId+', .reset-timer-btn'+rowId).removeClass('hidden');
}

// Remove timer
function stop(rowId){
	hasTimer = false;
	$('.timer'+rowId).timer('pause');
	$('.start-timer-btn'+rowId).removeClass('hidden');
	$('.pause-timer-btn'+rowId+', .resume-timer-btn'+rowId+', .remove-timer-btn'+rowId+'.reset-timer-btn'+rowId).addClass('hidden');
}

function startFromParticularPoint(rowId,startPoint){
	//alert("startPoint::"+startPoint);
//	debugger;
	hasTimer = true;	
	$('.timer'+rowId).timer({
		action:'start',
		seconds: startPoint
	});
	
	if(startPoint>28800){
		$('.start-timer-btn'+rowId+', .remove-timer-btn'+rowId+', .resume-timer-btn'+rowId).addClass('hidden');
		$('.pause-timer-btn'+rowId+', .reset-timer-btn'+rowId).removeClass('hidden');
	}else{
		$('.start-timer-btn'+rowId+', .resume-timer-btn'+rowId).addClass('hidden');
		$('.pause-timer-btn'+rowId+', .remove-timer-btn'+rowId+', .reset-timer-btn'+rowId).removeClass('hidden');
	}
	
//start(rowId);
}
