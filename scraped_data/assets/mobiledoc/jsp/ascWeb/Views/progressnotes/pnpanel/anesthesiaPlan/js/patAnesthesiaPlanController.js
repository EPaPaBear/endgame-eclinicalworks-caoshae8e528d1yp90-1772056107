angular.module('ascWeb.service.patAnesthesiaPlanService', []).service('patAnesthesiaPlanService', function($http) {
	return {

	};
});

angular.module("patAnesthesiaPlan", ['ascWeb.service.patAnesthesiaPlanService'])
.controller('patAnesthesiaPlanController', function ($scope, $http,patAnesthesiaPlanService,$ocLazyLoad){

	var section2 = 'Anesthesia Plan';
    var nextLabel = getNextLabel(section2);
    var prevLabel = getPrevLabel(section2);
    $scope.nextLabel = getLabel(nextLabel);
    $scope.prevLabel = getLabel(prevLabel);
    $scope.nextPrevType="";

	$scope.lockObj = {formName: "PatAnesthesiaPlan", uniqueKey: "PatAnesthesiaPlan" + encounterId, g_cancel: false, strKey: "", isOpenform: false};
	
	$scope.init=function(){
        acquireFormLock($scope.lockObj, acquireFormLockCallBack);
        function acquireFormLockCallBack() {
            if ($scope.lockObj.g_cancel) {
                $("#pn").modal('hide');
            }
        }
		$scope.encounterId =encounterId;
		$scope.encounterType =encounterType;
		$scope.$parent.setTitle("Anesthesia Plan");
		$scope.loadAnesthesiaPlanScreen();
		setHeader();
	}
	
	$scope.loadAnesthesiaPlanScreen = function () {
        $ocLazyLoad.load({
            name: 'anesthesiaPlanApp',
            files: ['/mobiledoc/jsp/ascWeb/Views/progressnotes/pnpanel/anesthesiaPlan/js/AnesthesiaPlanController.js']
        }
        ).then(function () {
        	$scope.anesthesiaPlanUrl = makeURL("/mobiledoc/ascWeb/PnPanel.go/anesthesiaPlan/" + $scope.encounterId + '/' + $scope.encounterType);
        }, function (e) {
            console.log(e);
        });
    };
    
    $scope.setNextPrevType=function(nextPrev){
    	$scope.nextPrevType=nextPrev;
    }
    
    function setHeader(){            	
    	$(".iconlist .nav li").removeClass("active");
    	$("#anesthesiaPlanHeader").addClass("active");
    };
    
    $scope.notifyModal=function(args){
    	afterSuccessSave(args,$scope.nextPrevType);
    };
    
    $scope.refreshDashboard = function() {
        refreshDashboard(encounterId,patientId, "", "pn");
    };
    
    $scope.loadSection=function(nextPrevType){
    	$scope.nextPrevType=nextPrevType;
    	$scope.$broadcast('saveAndClose', {'closeDialog': "false", 'section': ""});
    }
    
    function afterSuccessSave(args,type){
    	if (args !== undefined && args.closeDialog !== undefined && args.closeDialog === true) {
            releaseFormLock($scope.lockObj);
        	closePatAnesthesiaPlanModal();
            $scope.$parent.clearContent();
            $scope.refreshDashboard();
        } else if (type) {
            releaseFormLock($scope.lockObj);
            renewSection(type);
        }
        $scope.$parent.navigateToPNSection();
    }
    
    function closePatAnesthesiaPlanModal() {
              refreshDashboard(encounterId, patientId, "", "pn");
          }
    
    $scope.contentLoaded=function(){
    	
    }
    
    var renewSection = function(type) {
        if (type === "Next")
        {
            $scope.loadProgressNote(getLinkForSection(nextLabel));
        }
        else
        {
            $scope.loadProgressNote(getLinkForSection(prevLabel));
        }
    };
    
});

