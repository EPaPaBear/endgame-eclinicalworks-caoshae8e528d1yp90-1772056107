(function() {
    'use strict';

    angular.module('ecw.documentInsight')
        .service('AlertService', ['$http', '$q', 'DocumentInsightTileWrapperService', AlertService]);

    function AlertService($http, $q, DocumentInsightTileWrapperService) {
        this.getAlertData = (patientId) => {
            return DocumentInsightTileWrapperService.getDocumentInsights(patientId);
        };

        this.getPatientApplicableAlerts = (patientId, recordId, orders) => {
            return $http({
                method: "POST",
                headers: {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'},
                url: '/mobiledoc/prisma/document-insights/getPatientApplicableAlerts',
                data: $.param({patientId: patientId, recordId: recordId, orders: JSON.stringify(orders)})
            });
        };
    }
})();