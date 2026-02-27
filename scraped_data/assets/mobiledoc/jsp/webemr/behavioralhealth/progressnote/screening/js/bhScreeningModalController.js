(function () {
var dependencies = ['ui.bootstrap','behavioralhealth.service'];
var bhScreeningModalApp = angular.module('bhScreeningModal', dependencies);
	bhScreeningModalApp.controller('bhScreeningModalController',['$scope','$http','$modalInstance','$modal','behavioralHealthService','encDetailsFromPN',
function($scope,$http, $modalInstance, $modal,behavioralHealthService,encDetailsFromPN) {
	var bhScreeningModalCtrl = this;

	bhScreeningModalCtrl.initBhScreeningModal = function(){
		bhScreeningModalCtrl.calledFrom ="ProgressNotes";
		bhScreeningModalCtrl.calledFromEncId = encDetailsFromPN.encId;
		bhScreeningModalCtrl.calledFromEncDate = encDetailsFromPN.encDate;
		bhScreeningModalCtrl.patientId=encDetailsFromPN.ptId;
		bhScreeningModalCtrl.documentedFormsBtnUrl= makeURL('/mobiledoc/jsp/webemr/behavioralhealth/progressnote/screening/views/behavioralHealthScreening.html');

		let data = {
			"patientId": encDetailsFromPN.patientId,
			"calledFrom": bhScreeningModalCtrl.calledFrom,
			"encounterId": bhScreeningModalCtrl.calledFromEncId,
			"encounterDate": bhScreeningModalCtrl.calledFromEncDate
		};
		behavioralHealthService.setBehavioralHealthObj(data);
		behavioralHealthService.setPatientId(encDetailsFromPN.ptId);

	};

	bhScreeningModalCtrl.cancelScreeningDocumentedForms = function(){
		$modalInstance.close();
		refreshDashboard(bhScreeningModalCtrl.calledFromEncId, encDetailsFromPN.patientId, "", "pn");
	}
}]);
})();