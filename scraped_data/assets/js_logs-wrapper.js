angular.module('bhLogsWrapper', []).directive('bhLogsWrapper',
    function () {
        return {
            restrict: 'AE',
            replace: false,
            scope: {
                sectionId: '&',
                sectionName: '&',
                uniqueId: '&', /* Only use if call from user facing screen */
                isCallFromAdmin: '&', /* Only use if you want to launch logs directive from admin screen */
            },
            template: '<button class="btn btn-xs btn-lgrey pull-right"  id="bh-logs-id" bh-logs="" section-name="sectionName" is-call-from-admin="isCallFromAdmin"> Logs</button>'
        };
});
