/*
 * JS file for deletePtRecordLogs.jsp and other supporting functions
 * File:        deletePtRecordLogsController.js
 * Author:      VishalM
 * Created:     30/10/2017
 */
angular.module("deletePtRecordLogAppService",[]).factory('deletePtRecordLogService', function($http) {
    return {
    	getDeletedPtRecord : function(param){
            return $http({
                method: "POST",
                url: makeURL("/mobiledoc/jsp/webemr/jellybean/patientrecord/getDeletedPtRecord.jsp"),
                data: param,
                headers: {'Content-Type': 'application/x-www-form-urlencoded'}
            }).then(function(response) {
                return response.data;
            }, function() {
                throw "Internal Error occured, Please try after some time";
            });
        }
    };
});

angular.module("deletePtRecordLogsApp", ['deletePtRecordLogAppService']).controller('deletePtRecordLogsController', function($scope, $http,deletePtRecordLogService, $ocLazyLoad, $templateCache, $filter) {
	$scope.deletedPtRecord = {};
	$scope.currentTimeZone = getTZ();
	$scope.currntTimeZoneName = getTZName();
	$scope.callFrom = $('#callFrom').val();

	$scope.pagination = {
		recordPerPage: 20,
		currentPage: 1,
		totalRecords: 0
	};

	$scope.initDelPtRecord = function(isInit) {
		var params = {
			referralType : 'PTRECORD_I',
			timeZone :$scope.currentTimeZone,
			timeZoneName :$scope.currntTimeZoneName,
			isTotalCountRequire: isInit
		};

		params = $.extend({}, $scope.pagination, params);
		params = $.param(params);
		
		deletePtRecordLogService.getDeletedPtRecord(params).then(function(res){
			if(res) {

				$scope.deletedReferrls = res.records;
				if (res.totalCount) {
					$scope.pagination.totalRecords = res.totalCount;
				}

				$scope.deletedPtRecords = validateResultArray(res.records);
			}
       });
	}
	

	$scope.closePTRecLog = function(){
		closeP2PModal('deletePtRecordLogModal');
		if($scope.callFrom && $scope.callFrom == 'ccmr') {
			window.external.CloseForm();
		}
    };
	
	$scope.openDelPtRecordlog=function(ptRecord){
		var strValue = "";			
		$scope.deletePtRecordLogPortal = "";
			strValue = getItemKeyValue("inoutreferrallogs", strValue);
			if ("yes" == strValue.toLowerCase())
	 		{
 				$ocLazyLoad.load({
 					name: 'viewPtRecordlog',
 					files: ['/mobiledoc/jsp/webemr/jellybean/patientrecord/ptRecordLogsController.js','/mobiledoc/jsp/webemr/templates/pagination-tpl.js']
 				}).then(function() {
 					$scope.deletePtRecordLogPortal = makeURL("/mobiledoc/jsp/webemr/jellybean/patientrecord/getPtRecordLogs_10e.jsp?ptRecordLogType=" + "PTRECORD_I" + "&referralId=" + ptRecord.referralId +"&patientId="+ptRecord.patientId+"&timeZone="+getTZ()+"&timeZoneName="+getTZName()+"&callFrom=web");
 				}, function(e) {
 					console.log(e);
 				});
	 		}
		};
});