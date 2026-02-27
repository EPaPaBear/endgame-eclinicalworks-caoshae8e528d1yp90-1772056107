(function() {
    'use strict';

    angular.module('ecw.documentInsight')
        .service('ProblemListService', ['$q', 'DocumentInsightTileWrapperService', ProblemListService]);

    function ProblemListService($q, DocumentInsightTileWrapperService) {
        this.getProblemListData = (patientId) => {
            return DocumentInsightTileWrapperService.getDocumentInsights(patientId);
        };
    }
})();