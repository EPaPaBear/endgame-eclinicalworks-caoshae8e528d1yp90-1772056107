angular.module('messageRouting', []).directive('genieMessageRouting', function ($ocLazyLoad) {
    return {
        restrict: 'AE',
        scope: {
            isGenieFlow: '=?',
            taskType: '=?',
            dirtyFlag: '=',
            dirtyFlagChange: '&',
            dirtySaveChange: '&'
        },
        template: '<div ng-include="messageRoutingUrl"></div>',
        link: function($scope) {

            $scope.$watch('taskType', function (newVal, oldVal) {
                if(newVal) {
                   openMessageRouting();
                }
            });

            function openMessageRouting() {
                $ocLazyLoad.load({
                    name: 'PatientPortalSetting',
                    files: ['/mobiledoc/jsp/webemr/portal/portalSettingHelper.js'],
                    cache: true
                }).then(() => {
                    $scope.messageRoutingUrl = makeURL(
                        "/mobiledoc/jsp/webemr/portal/getMessageRouting.jsp?isGenieFlow=" + $scope.isGenieFlow + "&taskType=" + $scope.taskType);
                }, function (e) {
                    console.log(e);
                });
            }

        }
    }

});