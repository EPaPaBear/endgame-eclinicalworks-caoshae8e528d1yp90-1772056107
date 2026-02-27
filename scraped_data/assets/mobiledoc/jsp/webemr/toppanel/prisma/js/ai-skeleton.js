angular.module('ai-skeleton-app', [])
    .directive('dynamicHeight', dynamicHeight)
    .directive('skeletonLoader', skeletonLoader);

dynamicHeight.$inject = ['$timeout'];
function dynamicHeight($timeout) {
    return {
        restrict: 'A',
        scope: {
            getHeightFunction: '&',
            randomizeId:'<'
        },
        link: linkFunction
    };

    function linkFunction(scope, element) {
        function setDynamicHeight() {
            let dynamicHeight = scope.getHeightFunction();
            angular.element('.summarize-modal-container-'+scope.randomizeId+' .summararize-content-hgt-dynamic').height((dynamicHeight - angular.element('.summarize-modal-container-'+scope.randomizeId+' .fnt-w.ai-theme').height()) + 'px');
        }

        // Set the initial height
        scope.dynamicHeightTimeout = $timeout(setDynamicHeight, 500);

        // Update the height on window resize
        angular.element(window).on('resize', setDynamicHeight);

        // Cleanup the event listener when the scope is destroyed
        scope.$on('$destroy', function() {
            angular.element(window).off('resize', setDynamicHeight);
            $timeout.cancel(scope.dynamicHeightTimeout);
        });
    }
}

skeletonLoader.$inject = [];
function skeletonLoader() {
    return {
        restrict: 'E',
        scope: {
            calculateDynamicHeight: '&',
            loaderMsg: '@'
        },
        templateUrl: '/mobiledoc/jsp/webemr/ai/skeleton-loader.html',
        link: skeletonLoaderLinkFunction
    };

    function skeletonLoaderLinkFunction(scope, element) {
        scope.getHeight = () => {
            return scope.calculateDynamicHeight();
        }
    }
}