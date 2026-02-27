'use strict';
(function(f) {
    var allergyDirectiveApp = f.module('allergyDirectiveApp', []);
    allergyDirectiveApp.directive('toaster', ['$sce', function ($sce) {
        return {
            restrict: 'E',
            templateUrl: '/mobiledoc/jsp/allergy/assets/directives/toaster/index.html',
            transclude: true,
            scope: {
                message: '@',
                toasterClosed: '&',
            },
            controller: 'toasterController',
            controllerAs: 'vm',
            link: function (scope) {
                scope.toasterVisible = scope.visible;
                scope.trustHtml = function (html) {
                    return $sce.trustAsHtml(html);
                };
                $('#toasterHandler').fadeIn();
                let fadeTimeout = setTimeout(() => {
                    $('#toasterHandler').fadeOut();
                    scope.toasterClosed()
                }, 3000)
                scope.toasterClose = () => {
                    $('#toasterHandler').fadeOut();
                    scope.toasterClosed();
                    clearTimeout(fadeTimeout);
                }

            }
        };
    }]).controller('toasterController', ($scope) => {

    })
})(angular);