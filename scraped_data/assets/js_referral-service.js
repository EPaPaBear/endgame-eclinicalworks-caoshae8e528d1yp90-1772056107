(function() {
    'use strict';

    angular.module('ecw.documentInsight')
        .service('ReferralService', ['$http', ReferralService]);

    function ReferralService($http) {
        this.getIncomingReferral = (patientId, docId) => {
            return $http({
                method: "POST",
                headers: {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'},
                url: '/mobiledoc/prisma/document-insights/getReferralData',
                data: $.param({docId: docId, patientId: patientId})
            });
        };
    }

})();