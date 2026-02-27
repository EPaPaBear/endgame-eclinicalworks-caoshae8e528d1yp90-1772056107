(function () {
    var refToLookupToggleModule = angular.module("refToLookupToggleModule", ['ecw.p2p.referral.refToLookupDependencyModule']);

    refToLookupToggleModule.controller("refToLookupToggleController",
        ["$scope", "$ocLazyLoad", "$attrs", "refToLookupModuleDependencyService", refToLookupToggleController]);

    function refToLookupToggleController($scope, $ocLazyLoad, $attrs, refToLookupService) {
        $scope.uniqueIdentifier = (Math.random() + '').substring(2, 6);
        $scope.refToLookupToggleUrl = '';
        $scope.refToLookupToggleType = $attrs.lookupType === '0' ? 'classic' : 'modern';
        let queryParams = getQueryParams();
        $scope.refToLookupToggleType = queryParams.isBookNow === 'true' ? 'modern' : $scope.refToLookupToggleType;
        queryParams.refToToggleLookupIdentifier = 'refToToggleLookup' + $scope.uniqueIdentifier;

        $scope.toggleRefToLookup = function (type) {
            $scope.refToLookupToggleUrl = '';
            $ocLazyLoad.load(refToLookupService.getModule(type)).then(function () {
                $scope.refToLookupToggleUrl = makeURL(refToLookupService.getModalURL(type) + "?" + $.param(queryParams));
            }, function (e) {
                ecwAlert('Unable to load P2P Provider Lookup, Please try again.');
            });
        };

        $scope.toggleRefToLookup($scope.refToLookupToggleType);

        function getQueryParams() {
            let qParams = {};
            let skipParams = ['sessionDID', 'TrUserId', 'Device', 'ecwappprocessid', 'rnd2', 'timestamp', 'clientTimezone', 'gd'];
            let params = $(".ref-to-toggle-lookup-modal").find('input[type=hidden][name="refToLookupToggleParams[]"]');
            for (let i = 0; i < params.length; i++) {
                if (params[i]) {
                    let input = $(params[i]);
                    let paramName = input.attr("param-name");
                    if (paramName && !skipParams.includes(paramName)) {
                        qParams[paramName] = input.attr("param-value");
                    }
                }
            }
            return qParams;
        }
    }
})();