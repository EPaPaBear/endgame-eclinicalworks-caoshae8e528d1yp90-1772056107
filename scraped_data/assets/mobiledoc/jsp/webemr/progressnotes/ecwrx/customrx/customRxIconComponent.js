(function() {
    let customRxIconApp = angular.module('ecw.customrxicon', []);

    customRxIconApp.controller('customRxCtrl', ['$timeout',
        function($timeout) {
            $timeout(function () {
                $('.customrx-icon').tooltip({
                    container: 'body',
                    template: '<div class="tooltip tooltip-custom custrxtooltip-custom"><div class="tooltip-arrow"></div><div class="tooltip-inner"></div></div>'
                });
            });
    }]);
    customRxIconApp.directive('customRxIcon', function(){
        return {
            restrict: 'AE',
            scope: {
                isCustomRx: '='
            },
            templateUrl: "/mobiledoc/jsp/webemr/progressnotes/ecwrx/customrx/html/customRxIcon-tpl.html"
        };
    })
})();