(function() {
    'use strict';

    angular.module('ecw.documentInsight')
        .service('MedicationService', ['$q', 'DocumentInsightTileWrapperService', MedicationService]);

    function MedicationService($q, DocumentInsightTileWrapperService) {
        this.getMedicationData = (patientId) => {
            return DocumentInsightTileWrapperService.getDocumentInsights(patientId);
        };
    }
})();