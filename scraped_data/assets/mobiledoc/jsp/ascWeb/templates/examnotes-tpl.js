angular.module('inPatient.dir.ipexamnotes',[]).directive('ipexamnotes', function() {
	return {
		restrict : 'AE',
		replace : 'true',
		templateUrl : '/mobiledoc/ascWeb/PnPanel.go/templates/examNotes',
		scope : {
			notesoptions : '=notesoptions',
			customCancel : '&onCustomcancel',
			customSave : '&onCustomsave',
			customnavigation : '&onCustomnavigation',
			customNext : '&onCustomnext',
			customPrevious : '&onCustomprevious',
			redirectCustom : '&onRedirectcustom',
			drawingClick : '&onDrawingclick',
			selectedcategoryitem : '=selectedcategoryitem',
			isthumbnailvisible : '=isthumbnailvisible'
		},
		link : function(scope) {
			scope.delimeter = "Comma";
			scope.delimetersymbol = ", ";
			scope.isAllowCustomizaton = getPermission("Keywords",global.TrUserId);
			//This Will append note into Text Area component
			scope.appendNote = function(note) {
				var notes2 = scope.notesoptions.selectedExamNotes;
				var formattedText = '';
				var boldflag = '0';
				var underlineflag = '0';

				if (notes2 !== '') {
					notes2 = notes2 + '<FONT size=2>' + scope.delimetersymbol + '</FONT>';
				}
				formattedText = '<FONT id=' + note.pDetailId;
				if (note.color !== '') {
					note.color = note.color.replace("#", "");
					formattedText = formattedText + ' ' + 'color=#' + note.color.toLowerCase();
				}
				formattedText = formattedText + ' size=2>';
				if (note.bold === '1') {
					formattedText = formattedText + '<B>';
					boldflag = '1';
				}
				if (note.underline === '1') {
					formattedText = formattedText + '<U>';
					underlineflag = '1';
				}
				formattedText = formattedText + note.value;
				if (underlineflag === '1') {
					formattedText = formattedText + '</U>';
				}
				if (boldflag === '1') {
					formattedText = formattedText + '</B>';
				}
				formattedText = formattedText + '</FONT>';
				notes2 = notes2 + formattedText;
				scope.notesoptions.selectedExamNotes = notes2;

			};

			scope.changeDelimeter = function(delimeterValue, delimetersymbol) {
				scope.delimeter = delimeterValue;
				scope.delimetersymbol = delimetersymbol;
				$("#delimeterDropdown").removeClass("open");
			};

			scope.clearContent = function() {
				if (scope.notesoptions.selectedExamNotes !== '') {

					ecwConfirm("Are you sure you want to delete Notes ?",
						"Delete Notes",
						function() {
							scope.$apply(function() {
								scope.notesoptions.selectedExamNotes = "";
							});
						},
						function() {});
				//                    var removalFlag = confirm("Are you sure you want to delete Notes ?");
				//                    if (removalFlag) {
				//                        scope.notesoptions.selectedExamNotes = "";
				//                    }
				}
			};

			scope.appendTimeStamp = function() {
				var fullDate = new Date();
				if (scope.notesoptions.selectedExamNotes.length >= 1)
					scope.notesoptions.selectedExamNotes = scope.notesoptions.selectedExamNotes + ("\n" + fullDate);
				else
					scope.notesoptions.selectedExamNotes = scope.notesoptions.selectedExamNotes + fullDate;
			};

			scope.navigateToNotes = function(notescategory) {
				scope.notesoptions.notescategory = notescategory;
				scope.customnavigation();
			};
		}
	};
});