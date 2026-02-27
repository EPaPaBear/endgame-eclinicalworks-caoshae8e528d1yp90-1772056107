var apps = angular.module('pdmpNarxLogs', ['ecw.pagination','ecw.service.PDMPNarxLogService']);

apps.controller('PDMPNarxLogController',function($scope,$http,PDMPNarxLogService,$ocLazyLoad,$modalInstance,requestParam){
	$scope.patientId = requestParam.patientId;
	$scope.userId = requestParam.userId;
	$scope.encounterId = requestParam.encounterId;
	$scope.showNarxScoreRefreshIcon = requestParam.showNarxScoreRefreshIcon;

	$scope.currentPage = 1;
	$scope.totalItems = 0;
	$scope.pageRecords = 5;

	$scope.init = init;
	$scope.closePDMPNarxScore = closePDMPNarxScore;
	$scope.loadPDMPNarxLogData = loadPDMPNarxLogData;
	$scope.getLatestPdmpReportLogList = getLatestPdmpReportLogList;
	$scope.getSortIconClass = getSortIconClass;
	$scope.setSortOrder = setSortOrder;

	$scope.pdmpReportLogList = [];
	$scope.pdmpReportLogLatestRecord = {};
	$scope.sortColumnName = "RequestDateTime";
	$scope.sortOrder = "desc";
	$scope.isPDMPShowLoadingButton = false;

	var errorMessage = "Error occurred getting Narx Score data from Bamboo Health.";

	$scope.init();

	function init(){
		setPatientIdentifierParameters();
		loadPDMPNarxLogData();
	}

	function closePDMPNarxScore() {
    	$modalInstance.dismiss($scope.pdmpReportLogLatestRecord);
    }

	function setPatientIdentifierParameters(){
		var patientDataUrl='/mobiledoc/jsp/webemr/util/getIdentifiersForPatient.jsp';
		var data = 'patient=' + encodeURIComponent($scope.patientId);
		var ptResponse = urlPost(patientDataUrl, data);

		if(ptResponse) {
			$scope.patientIdentifiers = JSON.parse(ptResponse);
		}
	}

	function loadPDMPNarxLogData(){
		PDMPNarxLogService.getPdmpReportLogList($scope.patientId,$scope.currentPage,$scope.pageRecords,$scope.sortColumnName,$scope.sortOrder).success(function(data) {
			var strJSON = data;
			$scope.pdmpReportLogList = [];
			$scope.pdmpReportLogLatestRecord = {};
			if(strJSON.status === 'success'){
				$scope.pdmpReportLogLatestRecord = strJSON.pdmpReportLogLatestRecord;
				$scope.pdmpReportLogList = strJSON.pdmpReportLogList;
				$scope.totalItems = strJSON.totalCounts;
				$scope.currentPage = strJSON.currentPage;
				return;
			}
			ecwAlert(errorMessage, 'Narx Score Error', null, 'Close', null, null, false);
			loadPDMPNarxLogData();
		}).error(function (data) {
			$scope.isPDMPShowLoadingButton = false;
			ecwAlert(errorMessage, 'Narx Score Error', null, 'Close', null, null, false);
		});;
	}

	function getLatestPdmpReportLogList(){
		$scope.isPDMPShowLoadingButton = true;
		PDMPNarxLogService.getLatestPdmpReportLogList($scope.patientId,$scope.encounterId).success(function(data) {
			var strJSON = data;
			if(strJSON.status === 'success'){
				$scope.isPDMPShowLoadingButton = false;
				loadPDMPNarxLogData();
				return;
			}
			ecwAlert(errorMessage, 'Narx Score Error', null, 'Close', null, null, false);
			loadPDMPNarxLogData();
			$scope.isPDMPShowLoadingButton = false;
		}).error(function (data) {
			$scope.isPDMPShowLoadingButton = false;
			ecwAlert(errorMessage, 'Narx Score Error', null, 'Close', null, null, false);
		});
	}

	function getSortIconClass(sortColumn) {
		if($scope.sortColumnName !== sortColumn){
			return "sort-black";
		}

		if($scope.sortOrder === 'asc'){
			return "sort-black-up";
		}

		if($scope.sortOrder === 'desc'){
			return "sort-black-down";
		}
		return "sort-black";
	}

	function changeSortOrder(sortColumnName){
		if($scope.sortColumnName !== sortColumnName){
			$scope.sortColumnName = sortColumnName;
			$scope.sortOrder = 'asc';
			return;
		}
		if($scope.sortOrder === 'asc'){
			$scope.sortOrder = 'desc';
			return;
		}
		if($scope.sortOrder === 'desc'){
			$scope.sortOrder = 'asc';
			return;
		}
	}

	function setSortOrder(sortColumnName){
		changeSortOrder(sortColumnName);
		loadPDMPNarxLogData();
	}
});