angular.module('PtEdLogModule',['ui.bootstrap']).controller('PtEdLogCtrl', function ($scope, $http, $filter, $modalInstance, $window, version, url, $sce) {
	$scope.Version = version;
	$scope.PtEducationURL = url;

	$scope.loadPtEducation = function() {

	if ($scope.Version != undefined && $scope.CurrentReleaseDate != undefined) {
		if ($scope.Version != "" && $scope.CurrentReleaseDate != "") {
			if ($scope.Version != $scope.CurrentReleaseDate){				
				ecwAlert("<p>The patient education material you are viewing is not the same material that was printed/published to the patient at the time of their visit. </p><p>  Original version release date: " + $scope.Version+"</p>","eClinicalWorks",'','','orangetheme');			
			}
		}
	}

		$scope.PtEducationURL = $sce.trustAsResourceUrl(url);

	};
	

    $scope.close = function () {
        $modalInstance.dismiss();
    };

    $scope.loadInitData = function(sCurrentReleaseDate) {
    	$scope.CurrentReleaseDate = sCurrentReleaseDate;
			
		$scope.loadPtEducation();
    }

});
