(function() {
    'use strict';

    angular.module('ecw.documentInsight')
        .service('alertHIconService', ['$q', alertHIconService]);

    function alertHIconService($q) {
        this.getDropdownData = (params) => {
            return $q.resolve(params);
        };
    }
})();