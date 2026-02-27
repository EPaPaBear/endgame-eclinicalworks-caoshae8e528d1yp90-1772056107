angular.module('milestoneStatusLoaderModule', []).directive('milestoneStatusLoaderDir', function ($ocLazyLoad) {
    return {
        restrict: 'EA',
        scope: {
            patientId: '=',
            progressTitle: '=',
            percentage: '=?',
            milestoneStatus: '=',
            statusMessage: '=',
            resetAnimation: '=?',
        },
        templateUrl: '/mobiledoc/jsp/interop/milestone/view/loaderView.html',
        controllerAs: 'ihubStatusLoaderCtrl',
        controller: function ($scope, $rootScope, $interval, $timeout, $sce) {
            var ihsLoaderCtrl = this;
            ihsLoaderCtrl.showProgressBox = false;
            ihsLoaderCtrl.patientId = $scope.patientId;
            ihsLoaderCtrl.progressTitle = $scope.progressTitle;
            ihsLoaderCtrl.milestonePercent = $scope.percentage;
            ihsLoaderCtrl.milestoneStatus = $scope.milestoneStatus;
            ihsLoaderCtrl.statusMessage = $sce.trustAsHtml($scope.statusMessage);

            ihsLoaderCtrl.init = function () {
                ihsLoaderCtrl.refreshLoader();
            };
            ihsLoaderCtrl.refreshLoader = function () {
                ihsLoaderCtrl.showProgressBox = true;
                if (ihsLoaderCtrl.milestoneStatus === 'failed') {
                    ihsLoaderCtrl.showProgressBox = false;
                    ihsLoaderCtrl.showSuccessMsg = false;
                    ihsLoaderCtrl.showErrorMsg = true;
                } else if (ihsLoaderCtrl.milestonePercent < 100) {
                    ihsLoaderCtrl.showProgressBox = true;
                    ihsLoaderCtrl.showSuccessMsg = false;
                    ihsLoaderCtrl.showErrorMsg = false;

                } else if (ihsLoaderCtrl.milestonePercent === 100) {

                    ihsLoaderCtrl.showSuccessMsg = true;
                    ihsLoaderCtrl.showErrorMsg = false;
                    $timeout(function () {
                        ihsLoaderCtrl.showProgressBox = false;
                    }, 1000);
                }
            };
            ihsLoaderCtrl.resetAnimation = function () {
                ihsLoaderCtrl.milestonePercent = 0;
                ihsLoaderCtrl.showProgressBox = true;
                ihsLoaderCtrl.showSuccessMsg = false;
                ihsLoaderCtrl.showErrorMsg = false;
            };
            ihsLoaderCtrl.hideLoader = function () {
                ihsLoaderCtrl.milestonePercent = 0;
                ihsLoaderCtrl.showProgressBox = false;
                ihsLoaderCtrl.showSuccessMsg = false;
                ihsLoaderCtrl.showErrorMsg = false;
            }
        },
        link: function (scope, element, attrs) {

            scope.$watch('milestoneStatus', function (newValue, oldValue) {
                if (!newValue || angular.equals(newValue, oldValue))
                    return;
                if (newValue === 'resetLoader') {
                    scope.ihubStatusLoaderCtrl.resetAnimation();
                }
                scope.ihubStatusLoaderCtrl.milestoneStatus = newValue;
                scope.ihubStatusLoaderCtrl.refreshLoader();
            });
            scope.$watch('statusMessage', function (newValue, oldValue) {
                if (!newValue || angular.equals(newValue, oldValue))
                    return;
                scope.ihubStatusLoaderCtrl.statusMessage = newValue;
                scope.ihubStatusLoaderCtrl.refreshLoader();
            });
            scope.$watch('percentage', function (newValue, oldValue) {
                if (!newValue || angular.equals(newValue, oldValue))
                    return;
                scope.ihubStatusLoaderCtrl.milestonePercent = newValue;
                scope.ihubStatusLoaderCtrl.refreshLoader();
            });
            scope.$watch('resetAnimation', function (newValue, oldValue) {
                if (!newValue || angular.equals(newValue, oldValue))
                    return;
                scope.ihubStatusLoaderCtrl.hideLoader();
            });
        }
    }
});