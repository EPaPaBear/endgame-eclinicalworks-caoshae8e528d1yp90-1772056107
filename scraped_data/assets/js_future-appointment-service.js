// future-appointment-service.js

(function() {
    'use strict';

    angular.module('ecw.documentInsight')
        .service('FutureAppointmentService', ['$http', 'DocumentInsightTileWrapperService', FutureAppointmentService]);

    function FutureAppointmentService($http, DocumentInsightTileWrapperService) {
        this.getNextAppointment = (patientId) => {
            return $http.get('/mobiledoc/prisma/document-insights/future-appointment/next-appointment/' + patientId);
        };

        this.permissionCheck = (permissionKey) => {
            return getPermission(permissionKey, global.TrUserId);
        };
    }
})();