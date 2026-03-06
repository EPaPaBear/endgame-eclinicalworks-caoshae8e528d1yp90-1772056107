angular.module('actionHubWrapper', []).directive('actionHubWrapper', function ($ocLazyLoad) {
    return {
        restrict: 'AE',
        replace: false,
        scope: {
            module: '=',
            elementEvent: '=',
            parentScope: '=',
            screen: '=',
            template: '=',
            callFrom: '=',
            patientId: '=',
            ptacoid: '=',
            menuList: '=',
            encId: '=',
            isFromAngular:'='
        },
        link: function ($scope, element, attrs, modelCtrl) {
            $scope.isEnabled = false;
            $ocLazyLoad.load({
                files: ['/mobiledoc/jsp/webemr/phm/actionHub/js/actionHubService.js',
                    '/mobiledoc/jsp/webemr/ccm/userfacing/dashboard/enrollmentqueue/js/ccmPcmEnrollmentQueueService.js',
                    '/mobiledoc/jsp/resources/jslib/angular-ui-bootstrap/dist/ui-bootstrap-tpls.js',
                    '/mobiledoc/jsp/webemr/phm/actionHub/js/actionHub-tpl.js']
            }).then(function () {
                $scope.isEnabled = true;
            });
            $scope.$on('$destroy', function () {
                $scope.parentScope.callBack = null;
                $scope.parentScope = null
            })
        },
        template: '<div ng-if="isEnabled"><button action-hub-app is-from-angular="isFromAngular" menu-list="menuList" patient-id="patientId" module="module" element-event="elementEvent" parent-scope="parentScope" screen="screen" template="template" callFrom="callFrom" ptacoid="ptacoid" encId="encId" class="emr-ng-btn emr-ng-btn-action-hub emr-ng-btn-secondary"><i class="icon bhi-icon-dots-vertical"></i></button></div>',
    };
});