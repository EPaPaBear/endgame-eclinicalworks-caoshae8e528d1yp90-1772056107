(function() {
    let rxInfoIconApp = angular.module('ecw.rxinfotooltipicon', []);

    rxInfoIconApp.controller('rxInfoIconCtrl', ['$timeout',
        function($timeout) {
            $timeout(function () {
                $('.rxinfotooltip-icon').tooltip({
                    container: 'body',
                    template: '<div class="tooltip tooltip-custom rxtooltip-custom"><div class="tooltip-arrow"></div><div class="tooltip-inner"></div></div>'
                });
            });
    }]);
})();