angular.module('caretsApp', ['ecw.service.EncDetailsService','ecw.dir.patientidentifier'])
	.controller('caretsController', function($scope, $templateCache, EncDetailsService, $http, $ocLazyLoad, $modal) {
		$scope.patientIdentifier;
		$scope.apptCaption;
		$scope.module;
		$scope.fromHNP;
		let typeOfNote = "Items";
		let noteType = {
			'Exam': 'Observations',
			'HPI': 'Symptoms',
			'ROS': 'Symptoms',
			'PhyExam': 'Organs',
			'Procedures': 'Organs',
			'PreventiveMedicine': 'Symptoms',
			'TherapyAssessment': 'Organs',
			'Therapeutic': 'Organs'
		}

		let sections = {
			'Exam': 'Examination',
			'HPI': 'HPI',
			'ROS': 'ROS',
			'PhyExam': 'Physical Examination',
			'Procedures': 'Procedures',
			'PreventiveMedicine': 'Preventive Medicine',
			'TherapyAssessment': 'Physical Therapy Assessment',
			'Therapeutic': 'Therapeutic Interventions'
		}

		$scope.setPatientIdentifierDetails = function(encounterId, module){
			$scope.module = module;
			typeOfNote = noteType[module];
			var encObj = EncDetailsService.getEncDetailsByEncId(encounterId);
			if(parseInt(encObj.encounterId, 10) === encounterId && encObj.ispatientIdentifierDetails === 1){
				$scope.patientIdentifier=encObj.patientIdentifierDetails;
				$scope.apptCaption = EncDetailsService.getApptCaption();
			}
		}

		$scope.closePopUp = function() {
			$templateCache.remove($scope.popupurl);
			$('#carets').modal('hide');
			if($scope.fromHNP === 'yes'){
				$scope.$close();
			}
		};

		$scope.showItemsNotMergedWarning = function(excludedItems){
			let itemsMsgHeader = '<p>Notes for the listed '+ noteType[$scope.module] +' could not be merged as it has exceeded the maximum characters supported.</p>';
			let notesMsgHeader = "<p>";
			if($scope.module === 'HPI' || $scope.module === 'Exam'){
				notesMsgHeader += "Category ";
			} else {
				notesMsgHeader += "Section ";
			}
			notesMsgHeader += "Notes could not be merged as it has exceeded the maximum characters supported.</p>";
			let message = '<div class="excludedItemsWarnings mr10">';

			let totalItems = JSON.parse(excludedItems);
			if(totalItems.length > 0){
				let url = "/mobiledoc/emr/progressnotes/templates/getItemNames?section=" +$scope.module;
				url = makeURL(url);
				$http({
					headers: {'Content-Type': 'application/json','Accept': 'application/json'},
					dataType: 'json',
					method: 'POST',
					url: url,
					data: JSON.stringify(totalItems)
				}).then(function (response) {
					let items = response.data;
					let iMsg = '';
					let nMsg = '';

					items.forEach(item => {
						if(Object.keys(item.itemsNotMerged).length > 0){
							if(iMsg.length === 0)
								iMsg = "<table class='w100p itemsNotMergedClass ecw-scrollbar'>";
							iMsg += "<tr><td class='w15p mr12'><b>" + item.encDate + ":" +"</b></td><td><table class='w100p'>";
							for (let key in item.itemsNotMerged) {
								iMsg += "<tr><td><div><span class='catNameClass'>" + item.itemsNotMerged[key].catName + "</span>: <span class='itemNamesClass'>" + item.itemsNotMerged[key].items + "</span></div></td></tr>";
							}
							iMsg +=  "</table></td></tr>";
						}
						if(item.annualNotesNotMerged.length > 0){
							if(nMsg.length === 0 && ($scope.module === 'HPI' || $scope.module === 'Exam')){
								nMsg = "<table class='w100p notesNotMergedClass ecw-scrollbar'>";
							}
							if($scope.module === 'HPI' || $scope.module === 'Exam'){
								nMsg += "<tr><td class='w15p mr12'><b> " + item.encDate + ":</b></td><td class='catNameClass'>"  + item.annualNotesNotMerged + "</td></tr>";
							} else {
								if(nMsg === ""){
									nMsg += "<b> " + item.encDate + "</b>";
								} else {
									nMsg += "<b>, " + item.encDate + "</b>";
								}
							}
						}
					})
					if(totalItems.length > 0){
						if(iMsg.length > 0){
							message = message + itemsMsgHeader + iMsg + "</table><br/>";
						}
						if(nMsg.length > 0){
							message = message + notesMsgHeader + nMsg;
							if($scope.module === 'HPI' || $scope.module === 'Exam')
								message += "</table>";
							else
								message += "<br/>";
							message += "<br/>";
						}
						message += "<p><b>Review the " + sections[$scope.module] + " Notes to ensure the accuracy of merged notes.</b></p></div>";
						showWarning(message);
					}

				}, function (response) {
				});
			}
		}

		function showWarning(message){
			commonWarningPopup({
				screenName: sections[$scope.module] + ' > Merge',
				screenTitle: 'Character Limit exceeded',
				buttons: [{label: "OK",cssClass: 'btn-blue',callbackEvent: function () { }}],
				message : message,
				isErrorPopup: true,
				screenSpecificClass: '',
				isKeyboardClose:true
			}, $ocLazyLoad, $modal);
		}
	});
