/**
 * This directive is used for generating Requested Fill Message Types & 'i' icon allow the prescribers to specify which type of fill notification they will like to receive from the pharmacy
 * 
 * Usage:
 * <rx-fill-indicator ng-model="scope.requestedFillMessageType"> </rx-fill-indicator> 
 * 
 */
angular.module('ecw.dir.rxFillIndicator', []).directive('rxFillIndicator', function() {
	return {
        restrict: 'E',
        replace: true,
        scope: {
          ngModel: '=', 
          rxType: '@',
          calledFrom: '@',
          disableFillIndicator: "=?",
          rxFillIndicatorClick: "&"
        },
        templateUrl: '/mobiledoc/jsp/webemr/jellybean/refillrequest/RxFillIndicator.html',
        link: function(scope, element, attrs) {
            try {scope.disableFillIndicator = !(scope.disableFillIndicator) ? false : scope.disableFillIndicator;}catch (e) {}

            scope.selectRxFillIndicator = function(){
                if(scope.calledFrom === 'commonSend'){
                    scope.rxFillIndicatorClick();
                }
            }
        }
    };
});