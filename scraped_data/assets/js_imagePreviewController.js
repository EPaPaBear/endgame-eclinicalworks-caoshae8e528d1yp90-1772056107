    angular.module('ecw.telemed')
    .directive('imagePreview', ['mySharedService',
        function (mySharedService) {
            return {
                restrict: 'E',
                replace: 'false',
                templateUrl: '/mobiledoc/jsp/webemr/telemed/image-preview.html',
                scope: {
                },
                link: function (scope) {
                    scope.showImagePreview = true;
                }
            };
        }]
    );

