angular.module('milestoneStatusModule', []).directive('milestoneStatusDir', function ($ocLazyLoad) {
    return {
        restrict: 'EA',
        scope: {
            patientId: '=',
            percent: '=?',
            milestoneStatus: '=?',
            resetAnimation: '=?'
        },
        templateUrl: '/mobiledoc/jsp/interop/milestone/view/iHubStatusView.html',
        controllerAs: 'ihubStatusCtrl',
        controller: function ($scope, $rootScope, $interval, $timeout) {
            var ihsCtrl = this;
            ihsCtrl.animation;
            ihsCtrl.p = 0;
            ihsCtrl.s = '';
            ihsCtrl.patientId = $scope.patientId;
            ihsCtrl.milestonePercent = $scope.percent;
            ihsCtrl.milestoneStatus = $scope.milestoneStatus;

            ihsCtrl.progress = 0;
            ihsCtrl.distance = 0;
            ihsCtrl.showProgressBox = true;
            ihsCtrl.showSuccessMsg = false;
            ihsCtrl.currentDistance = 0;

            ihsCtrl.init = function () {
                ihsCtrl.increaseProgress(ihsCtrl.milestonePercent, ihsCtrl.milestoneStatus);
            }

            ihsCtrl.resetAnimation = function () {
                document.getElementById('wrap').style.setProperty('--distance', ihsCtrl.distance + '%');
                const outerBtn = document.querySelector('#milestoneOuterBtn');
                outerBtn.classList.remove('failure-btn');
                outerBtn.classList.remove('green-theme');
                outerBtn.classList.remove('done');
                outerBtn.classList.add('square-btn');
                outerBtn.classList.add('btn');
                ihsCtrl.increaseProgress("resetLoader", 0);
            }

            ihsCtrl.increaseProgress = function (value, status) {
                ihsCtrl.distance = value;
                document.getElementById('wrap').style.setProperty('--distance', ihsCtrl.distance + '%');
                const squareBtn = document.querySelector('#milestoneOuterBtn');
                if (status === 'failed') {
                    squareBtn.classList.remove('square-btn');
                    squareBtn.classList.remove('green-theme');
                    squareBtn.classList.add('failure-btn');
                    squareBtn.classList.add('done');
                    $interval.cancel(ihsCtrl.animation);
                    //ihsCtrl.refreshLoader(value,status);
                } else if (ihsCtrl.distance === 100) {
                    squareBtn.classList.add('square-btn');
                    squareBtn.classList.add('green-theme');
                    squareBtn.classList.add('done');
                    $interval.cancel(ihsCtrl.animation);
                    //ihsCtrl.refreshLoader(value,status);
                } else {
                    squareBtn.classList.add('square-btn');
                    squareBtn.classList.remove('done');
                }
            }

            ihsCtrl.refreshLoader = function (value, status) {
                if (status === 'failed') {
                    ihsCtrl.showProgressBox = false;
                    $timeout(function () {
                        ihsCtrl.showErrorMsg = true;
                    }, 2000);
                } else if (value === 100) {
                    ihsCtrl.showProgressBox = true;
                    $timeout(function () {
                        ihsCtrl.showProgressBox = false;
                        ihsCtrl.showSuccessMsg = true;
                    }, 2000);
                }
            }
        },
        link: function (scope, element, attrs) {
            scope.$watch('milestoneStatus', function (newValue, oldValue) {
                if (!newValue || angular.equals(newValue, oldValue))
                    return;
                if (newValue === 'resetLoader') {
                    scope.ihubStatusCtrl.resetAnimation();
                }
                scope.ihubStatusCtrl.milestoneStatus = newValue;
                scope.ihubStatusCtrl.increaseProgress(0, scope.ihubStatusCtrl.milestoneStatus);
            });
            scope.$watch('percent', function (newValue, oldValue) {
                if (!newValue || angular.equals(newValue, oldValue))
                    return;
                scope.ihubStatusCtrl.milestonePercent = newValue;
                scope.ihubStatusCtrl.increaseProgress(newValue, scope.ihubStatusCtrl.milestoneStatus);
            });
        }
    }
});