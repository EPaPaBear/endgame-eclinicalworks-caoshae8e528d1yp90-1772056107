$(".sticky").attr('contenteditable',true).focus();
function setOBPNheight()
{
	try{
		$(window).resize(function()
		 {		
			$('.ob-topcont,.ob-list').jScrollPane({autoReinitialise:true,verticalDragMinHeight: 100,verticalDragMaxHeight: 200,contentWidth: '0px',hijackInternalLinks: true,animateScroll:false});
			$('.stk_cont').jScrollPane({autoReinitialise:true,verticalDragMinHeight: 20,verticalDragMaxHeight: 20,contentWidth: '0px',hijackInternalLinks: true,animateScroll:true});
			$('.overflowauto').jScrollPane({autoReinitialise:true,autoReinitialiseDelay: 200,hijackInternalLinks: true,animateScroll:true});		 	 		
		  });
		   // call `resize` to center elements
		 $(window).resize();
	}catch(err){
		
	}
}