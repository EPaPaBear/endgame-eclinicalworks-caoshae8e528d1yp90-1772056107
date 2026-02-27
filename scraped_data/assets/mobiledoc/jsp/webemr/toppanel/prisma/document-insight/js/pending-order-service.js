(function() {
    'use strict';

    angular.module('ecw.documentInsight')
        .service('PendingOrderService', ['$http', 'DocumentInsightTileWrapperService', PendingOrderService]);

    function PendingOrderService($http, DocumentInsightTileWrapperService) {
        this.getPendingOrderData = (patientId) => {
            return DocumentInsightTileWrapperService.getDocumentInsights(patientId);
        };

        this.getPendingOrders = (dataToSend, patientId) => {
            return $http({
                method: "POST",
                headers: {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'},
                url: '/mobiledoc/prisma/document-insights/getPendingOrders',
                data: $.param({orders: JSON.stringify(dataToSend), patientId: patientId})
            });
        };
    }
})();
