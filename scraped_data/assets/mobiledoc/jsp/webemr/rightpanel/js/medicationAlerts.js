var medicationSummAlertApp = angular.module('medicationSummAlertApp', []);
medicationSummAlertApp.controller('medicationSummAlertController', function ($scope, $http, $timeout, $modalInstance,$ocLazyLoad,$templateCache,medicationAlertDataObject) {
	$scope.patientIdInMedicationAlerts = medicationAlertDataObject.patientId;
	$scope.getMedicationAlertList=function(){
		 var url="/mobiledoc/jsp/webemr/rightpanel/getMedicationAlert.jsp";
		 var data=$.param({patientaId:medicationAlertDataObject.patientId ,encId:medicationAlertDataObject.encounterId,userId:global.TrUserId});
	   	 var httpRequest= $http.post(url,data);
	    httpRequest.success(function (response){
	   	 $scope.medicationSummaryAlertList = ($.isArray(response.MedicationAlertsList) ? response.MedicationAlertsList : x2js.asArray(response.MedicationAlertsList)[0]);
	 	 $scope.medicationAlertEncDate=response.MedicationAlertsEncDate;
	 	 $scope.medicationAlertEncTime=response.MedicationAlertsEncTime;
	   	 }).error(function(data, status, headers, config){
	   		 
	   	 });	   	 
	   	
	};
	
	$scope.getMedicationAlertList();	
	
	$scope.closeMedAlertDialog = function () {			   
		  $modalInstance.close(true);      
	    };
	    
	    
    $scope.dismissMedAlertMsg = function (){    
   	 var serverUrl = '/mobiledoc/jsp/ecwrx/Rx_Medication_Alert_Save.jsp'; 
   	 var alertIds="";
   	 for(var i=0;i<$scope.medicationSummaryAlertList.length;i++){
   		 if(i==0){
   		   alertIds=$scope.medicationSummaryAlertList[i].Id;
   		 }else{
   		   alertIds=alertIds+","+$scope.medicationSummaryAlertList[i].Id;;
   		 }
   	 }
   	 var data=$.param({patientid:medicationAlertDataObject.patientId,encid:medicationAlertDataObject.patientId,TrUserId:global.TrUserId,alertIds:alertIds});
   	 var httpRequest= $http.post(serverUrl,data);
   	 httpRequest.success(function (response){
   		$modalInstance.dismiss("success"); 
   	 }).error(function(data, status, headers, config){
   		
   	 });
   	
   };

});

