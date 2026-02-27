angular.module('prisma.clinicalInsights.referralsTile', []).directive('referralsTile', function () {
    return {
        restrict: 'E',
        scope: {
            model: '=',
            options: '=',
            error: '=',
            header:"@"
        },
        templateUrl: '/mobiledoc/jsp/webemr/toppanel/prisma/template/referralsTile.html',
        controller: function ($scope) {},
        link: function (scope, element, attrs) {}
    };
})