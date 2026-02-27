angular.module('ecw.service.globalalerts',[]).factory('globalAlertsService',function(){
	var globalAlertsService = {};
	globalAlertsService.doesPatientHaveMUOrBillingAlerts= function(patientId) {
		var isAlertsCheckNeededForPatient = (getItemKeyValue('EnableBillingAlertOnPatientHubforNewTelEnc').toLowerCase() === 'yes')&& (patientId > 0);
		return isAlertsCheckNeededForPatient ? (doesPatientHaveMUAlerts(patientId) || doesPatientHaveBillingAlerts(patientId)):false;
	}

	function doesPatientHaveMUAlerts(patientId) {

		if (getItemKeyValue('MUParticipate').toLowerCase() === 'yes') {
			var MUAlerts =  urlPost('/mobiledoc/jsp/webemr/billingalert/getMUAlertText.jsp?patientId=' +patientId);
			return MUAlerts ? !!MUAlerts.trim() : false;
		}
		return false;
	}

	function doesPatientHaveBillingAlerts(patientId) {
		var doesPatientHaveBillingAlerts = false;
		var billingAlertsResponse = urlPost('/mobiledoc/jsp/catalog/xml/IsBillingAlertExist.jsp', 'PatientId=' + patientId);
		if(billingAlertsResponse && billingAlertsResponse.trim() !== ''){
			var billingAlertsResponseData = xml2json(billingAlertsResponse.trim());
			var billingAlerts = billingAlertsResponseData.Envelope.Body['return'];
			if(billingAlerts.status === 'success'){
				doesPatientHaveBillingAlerts = (billingAlerts.BillingAlert === '1') || (billingAlerts.GivenToColl === '1');
			}else{
				ecwAlert("An error occurred in loading billing/global alerts for patient.");
			}
		}
		return doesPatientHaveBillingAlerts;
	}
	return globalAlertsService;
});