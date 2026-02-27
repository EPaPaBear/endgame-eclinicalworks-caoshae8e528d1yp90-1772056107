(function() {
    let autoRenewalIconApp = angular.module('ecw.autoRenewaltooltipicon', []);

    autoRenewalIconApp.controller('autoRenewalIconCtrl', ['$timeout',
        function($timeout) {
            $timeout(function () {
                $('.icon-30dayormoresupply').tooltip({
                    container: 'body',
                    template: '<div class="tooltip tooltip-custom autoRenewaltooltip-custom"><div class="tooltip-arrow"></div><div class="tooltip-inner"></div></div>'
                });
                $('.icon-8dayormoresupply').tooltip({
                    container: 'body',
                    template: '<div class="tooltip tooltip-custom autoRenewaltooltip-custom"><div class="tooltip-arrow"></div><div class="tooltip-inner"></div></div>'
                });
                $('.icon-7dayorlesssupply').tooltip({
                    container: 'body',
                    template: '<div class="tooltip tooltip-custom autoRenewaltooltip-custom"><div class="tooltip-arrow"></div><div class="tooltip-inner"></div></div>'
                });
                $('.icon-nosupply').tooltip({
                    container: 'body',
                    template: '<div class="tooltip tooltip-custom autoRenewaltooltip-custom"><div class="tooltip-arrow"></div><div class="tooltip-inner"></div></div>'
                });
                $('.icon-unknownsupply').tooltip({
                    container: 'body',
                    template: '<div class="tooltip tooltip-custom autoRenewaltooltip-custom"><div class="tooltip-arrow"></div><div class="tooltip-inner"></div></div>'
                });
                $('.icon-loadingPill').tooltip({
                    container: 'body',
                    template: '<div class="tooltip tooltip-custom autoRenewaltooltip-custom"><div class="tooltip-arrow"></div><div class="tooltip-inner"></div></div>'
                });
            });
        }]);
})();