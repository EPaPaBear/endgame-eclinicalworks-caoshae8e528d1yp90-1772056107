var stripLastEmptyLineUtils = (function () {

	this.removeLastBrTag = function(notesHtml){
		var initial = notesHtml;
		notesHtml = removeEOSBreakline(notesHtml);

		if(hasSamePlainText(initial, notesHtml)){
			return notesHtml;
		}
		return initial;
	}

	this.capitalizeAllBRAndRemoveLastBR = function(notesHtml) {
		try{
			var tempNotes = notesHtml.replace(/<br>/g, "<BR>");
			while (tempNotes.match(/<BR>$/)) {
				tempNotes = tempNotes.replace(/<BR>$/, "");
			}
			if(hasSamePlainText(notesHtml, tempNotes)){
				notesHtml = tempNotes;
			}
		} catch(err){
		}
		return notesHtml;
	}

	var removeEOSBreakline = function(notesHtml){
		try{
			var tempNotes = notesHtml;
			var br = "<BR>";
			var maxIteration = 20;
			while(tempNotes.match(/<BR>[\s*</FONT>\s*]*$/i) && maxIteration>0){
				var lastIndexOfBR = tempNotes.toUpperCase().lastIndexOf(br);
				tempNotes = tempNotes.substring(0, lastIndexOfBR) + tempNotes.substring(lastIndexOfBR + br.length, tempNotes.length);
				maxIteration -= 1;
			}
			notesHtml = tempNotes;
		} catch(err){
		}
		return notesHtml;
	}

	var hasSamePlainText = function(initial, final){
		try{
			var plainTextBeforeChange = stripForHtml(initial).trim();
			var plainTextAfterChange = stripForHtml(final).trim();
			if(plainTextBeforeChange.length == plainTextAfterChange.length && plainTextBeforeChange === plainTextAfterChange){
				return true;
			}
		} catch(err){}
		return false;
	}

	var stripForHtml = function(html) {
		try {
			html = html.replace(new RegExp("<br>", 'g'), " ");
			html = html.replace(new RegExp("<BR>", 'g'), " ");
		} catch (err) {

		}
		var tmp = document.createElement("DIV");
		tmp.innerHTML = html;
		return tmp.textContent || tmp.innerText || "";
	}

	return this;
})();

module.exports = stripLastEmptyLineUtils;