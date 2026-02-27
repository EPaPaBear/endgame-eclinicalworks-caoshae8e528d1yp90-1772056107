angular.module('ecw.service.alerts', []).factory('alertsService', ['$http', function($http) {
	var alertsService = {};
	
	/**
	 * Checks whether the specified "suppress until" date is valid, alerting the user if it is not.
	 * 
	 * @param dueDate the due date of the alert prior to suppression (in a format parseable by moment.js).
	 * @param suppressUntilDate the date until which the alert is to be suppressed (in a format parseable by moment.js).
	 * @param isSuppressionPermanent true if the suppression is permanent, false otherwise.
	 * @return true if the "suppress until" date is valid, false otherwise.
	 */
	alertsService.validateSuppressUntilDate = function(dueDate, suppressUntilDate, isSuppressionPermanent) {
		// The date is irrelevant if the alert is being permanently suppressed:
		if (isSuppressionPermanent) {
			return true;
		}
		
		var oldDueDate = moment(dueDate).startOf('day');
		var newDueDate = moment(suppressUntilDate || '').startOf('day');
		
		var isDateValid = newDueDate.isValid() && !newDueDate.isBefore(oldDueDate);
		
		if (!isDateValid) {
			ecwAlert("Please enter a valid date (on or after the alert's current due date of " + oldDueDate.format("MM/DD/YYYY") + ").");
		}
		
		return isDateValid
	};
	
	/**
	 * Gets the alerts associated with the specified patient.
	 * 
	 * @param patient an object containing patient data, for example:
	 *        {
	 *        	id: 12345,
	 *        	ageWithUnits: '20Y',
	 *        	sex: 'M' // or 'male'
	 *        }
	 * @param includeMyAlertsOnly true if only alerts that are either (1) associated with the
	 *        logged-in user, or (2) not associated with any user should be retrieved; false otherwise.
	 * @param encounterId (optional) the unique ID of the encounter in context, if any.
	 * @return HttpPromise a promise resolving to an object containing an array of alerts for each alert type.
	 */
	alertsService.getAlerts = function(patient, includeMyAlertsOnly, encounterId) {
		var url = '/mobiledoc/jsp/webemr/alerts/cdss/getPatientAlertData.jsp';
		
		var data = {
				patientID: patient.id,
				patientAgeWithUnits: patient.ageWithUnits,
				showMyAlertsOnly: includeMyAlertsOnly,
				encounterID: encounterId || 0,
				patientSex: patient.sex
		};
		
		return $http.post(url, $.param(data));
	};

	/**
	 * Returns the publish to portal value based on the item type(labs/DI/Procedures)
	 *
	 * @param itemType - labs/DI/Procedures; '0'-labs, '1'-DI, '3'- procedures
	 * @return '1' if this item type should be published to Patient Portal by default; '0' otherwise.
	 */
	alertsService.getPortalPublishValueBasedOnLabType= function(itemType) {
		let  publishToPortal = '0';
		const ITEM_TYPE_DI = '1';
		const ITEM_TYPE_PROCEDURE = '3';
		let itemKeyUsed = '';
		if (getItemKeyValue('EnableWebPortal',true) === '1') {
			switch(itemType)
			{
				case ITEM_TYPE_DI :
					itemKeyUsed = 'DefaultDoNotPublishDImaging';
					break;
				case ITEM_TYPE_PROCEDURE :
					itemKeyUsed = 'DefaultDoNotPublishProcedures';
					break;
				default :
					itemKeyUsed = 'DefaultDoNotPublishLabs';
					break;
			}
			publishToPortal = angular.lowercase(getItemKeyValue(itemKeyUsed)) === 'yes'?'1':'0';
		}
		return publishToPortal;
	};

	alertsService.isAlertValidForDueDateType = function(filterBy, dueDate) {

		//All alerts are required
		if(filterBy === "100") {
			return true;
		}

		let currentDate = moment(new Date().format('mm/dd/yyyy'));
		let alertDate = moment(dueDate);

		return alertDate.isSameOrBefore(currentDate.add(parseInt(filterBy),'months'));

	}

	alertsService.getPopHealthMeasuresLabsDiProcedures = patientId => $http.post("/mobiledoc/jsp/webemr/providerHub/HedisMeasuresRequestHandler.jsp", $.param({
		callingFor: "getPopHealthMeasuresLabsDiProcedures",
		patientId
	}));

	alertsService.callRealtimeRefreshJob = function(patientId, measuresList) {
		var url = '/mobiledoc/jsp/webemr/alerts/cdss/getRealtimeRefreshForCDSS.jsp';

		var data = {
			action: "getRealtimeRefreshForCDSS",
			patientId: patientId,
			measuresArr: measuresList
		};

		return $http.post(url, $.param(data));
	};
	
	return alertsService;
}]);