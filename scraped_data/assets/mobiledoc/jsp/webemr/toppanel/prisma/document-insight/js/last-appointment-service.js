(function() {
    'use strict';

    angular.module('ecw.documentInsight')
        .service('LastAppointmentService', ['$http', LastAppointmentService]);

    function LastAppointmentService($http) {
        this.getLastAppointment = (patientId) => {
            return $http.get('/mobiledoc/prisma/document-insights/patient-info/last-appointment/' + patientId);
        };
    }
})();