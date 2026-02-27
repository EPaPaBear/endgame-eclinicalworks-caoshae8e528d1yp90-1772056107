// summary-service.js

(function() {
    'use strict';

    angular.module('ecw.documentInsight')
        .service('SummaryService', ['$http', 'DocumentInsightTileWrapperService', SummaryService]);

    function SummaryService($http, DocumentInsightTileWrapperService) {
        this.getSummary = (patientId) => {
            // Replace this with the actual API call to get the summary
            return "Summary for patient " + patientId;
        };
    }
})();