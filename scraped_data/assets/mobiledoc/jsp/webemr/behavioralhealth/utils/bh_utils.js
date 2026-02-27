/**
 * Function to get Local System DateTime value 
**/
function getLocalDateTimeString(){
	var dateTime = "";
	var today = new Date();
	var dd = today.getDate();
	var mm = today.getMonth()+1;
	var yyyy = today.getFullYear();
	if(dd<10){dd='0'+dd;}
	if(mm<10){mm='0'+mm;}
	var date = mm+'/'+dd+'/'+yyyy;	
	
	var hour    = today.getHours();
    var minute  = today.getMinutes();
    var second  = today.getSeconds();
	if(hour<10){hour = '0'+hour;}
	if(minute<10){minute = '0'+minute;}
	if(second<10){second = '0'+second;}   
	var timeString = hour+':'+minute+':'+second;
	dateTime = date+" "+timeString;
	return dateTime; 
}

function strip(html) {
	try {
		html = html.replace(new RegExp("<br>", 'g'), " ");
		html = html.replace(new RegExp("<BR>", 'g'), " ");
	} catch (err) {

	}
	var tmp = document.createElement("DIV");
	tmp.innerHTML = html;
	return tmp.textContent || tmp.innerText || "";
}

function isDecimal(evt)
{
	var charCode = (evt.which) ? evt.which : evt.keyCode;
	if (charCode != 46 && charCode > 31
		&& (charCode < 48 || charCode > 57))
		return false;

	return true;
}