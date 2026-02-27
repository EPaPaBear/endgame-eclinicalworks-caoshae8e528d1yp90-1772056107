angular.module("deleteRefLogsAppService",[]).factory('deleteRefLogService', function($http) {
    return {
    	getDeletedReferral : function(param){
            return $http({
                method: "POST",
                url: makeURL("/mobiledoc/jsp/webemr/jellybean/referral/getDeletedReferral.jsp"),
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

angular.module("deleteRefLogApp", ['deleteRefLogsAppService']).controller('deleteReferralLogsController', function($scope, $http,deleteRefLogService, $ocLazyLoad, $templateCache, $filter,PSACService) {
	$scope.deletedReferrls = {};
	$scope.referralType = $('#referralType').val();
	$scope.callFrom = $('#callFrom').val();
	$scope.modalTitle = $scope.referralType === "PTRECORD_O" ? "Deleted Patient Record Logs" : "Deleted Referral Logs";

	
	$scope.currentTimeZone = getTZ();
	$scope.currntTimeZoneName = getTZName();
	$scope.pagination = {
		recordPerPage: 20,
		currentPage: 1,
		totalRecords: 0
	};
	
	$scope.initDelReferral = function(isInit) {
		var params = {
			referralType : $scope.referralType,
			timeZone :$scope.currentTimeZone,
			patientId: $scope.patientIdentifiers ? $scope.patientIdentifiers.id : 0,
			isTotalCountRequire: isInit
		};
		params = $.extend({}, $scope.pagination, params);
		params = $.param(params);
		
		deleteRefLogService.getDeletedReferral(params).then(function(response){
			if (response && response.status === 'success') {
				$scope.deletedReferrls = response.records;
				if (response.totalCount) {
					$scope.pagination.totalRecords = response.totalCount;
				}
			}
       });
	}
	
	$scope.getUserFullName = function(trUserId) {
		var provider = getCachedProviderInfo(trUserId);
		return provider.lastName + "," + provider.firstName
	}
	
	$scope.closePTRecLog = function(){
		closeP2PModal('deleteReferralLogModal');
		if($scope.callFrom && $scope.callFrom == 'ccmr') {
			window.external.CloseForm();
		}
    };

	$scope.openReferralLogs=function(referral) {
		var strValue = "";
		strValue = getItemKeyValue("inoutreferrallogs", strValue);
		if (strValue.toLowerCase() === "yes") {
			PSACService.checkCommonStaffPermission(referral.patientId, function (data) {
				getLogsForDeletedReferral(referral);
			});
		}
	}
	var getLogsForDeletedReferral = function(referral) {
			$ocLazyLoad.load({
				name: 'viewReflog',
				files: ['/mobiledoc/jsp/webemr/jellybean/referral/viewReferralLogsController.js']
			}).then(function() {
				$scope.deleteReferralLogPortal=makeURL("/mobiledoc/p2pmodule/referral/log/getlog/10e?referralLogType=" + $scope.referralType + "&referralId=" + referral.referralId +"&patientId="+referral.patientId+"&timeZone="+$scope.currentTimeZone+"&timeZoneName="+$scope.currntTimeZoneName);
			}, function(e) {
				console.log(e);
			});
 		}
});