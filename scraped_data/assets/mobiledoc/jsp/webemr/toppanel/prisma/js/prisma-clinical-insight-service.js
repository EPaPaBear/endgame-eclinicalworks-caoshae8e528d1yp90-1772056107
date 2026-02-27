(function() {
    angular.module('prismaAppClinicalInsightService', [])
        .factory('prismaClinicalInsightService', PrismaClinicalInsightService);
    function PrismaClinicalInsightService( $http ) {
        return {
            getClinicalInsightData  : getClinicalInsightData,
            getAllLabs              : getAllLabs,
            getAllProblems          : getAllProblems,
            getAllMeds              : getAllMeds,
            getAllVitals            : getAllVitals,
            getAllReferrals         : getAllReferrals,
            getAppointmentDetails   : getAppointmentDetails,
            getCareTeam             : getCareTeam,
            getLabPanelAndSiblings  : getLabPanelAndSiblings,
            getAllImagingAndProcedures : getAllImagingAndProcedures,
            getDiseaseBasedViewData : getDiseaseBasedViewData
        }

        function getCareTeam(request){
            return $http({
                method: "POST",
                headers    :  {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'},
                url: '/mobiledoc/prisma/overview/getCareTeamData',
                data: $.param(request)
            });
        }

        function getAppointmentDetails(request){
            return $http({
                method: "POST",
                headers    :  {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'},
                url: '/mobiledoc/prisma/clinicalinsight/getAppointmentDetails',
                data: $.param(request)
            });
        }
        function getClinicalInsightData(patientId) {
            return $http({
                method: "GET",
                headers    :  {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'},
                url: `/mobiledoc/prisma/clinicalinsight/getClinicalInsightMeta/${patientId}`
            });
        }

        function getDiseaseBasedViewData(patientId){
            return $http({
                method: "GET",
                headers    :  {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'},
                url: `/mobiledoc/prisma/clinicalinsight/getClinicalInsightMeta/${patientId}?isProblemBasedView=true`
            });
        }
        function getAllLabs(patientId){
            return $http({
                method: "GET",
                headers    :  {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'},
                url: `/mobiledoc/prisma/clinicalinsight/allLabs/${patientId}`
            });
        }

        function getLabPanelAndSiblings(panelId, source, patientId, fromLabId){
            return $http({
                method: "GET",
                headers    :  {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'},
                url: `/mobiledoc/prisma/clinicalinsight/getLabPanelAndSiblings/${panelId}/${source}/${fromLabId}/${patientId}`
            });
        }

        function getAllProblems(patientId){
            return $http({
                method: "GET",
                headers    :  {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'},
                url: `/mobiledoc/prisma/clinicalinsight/allProblems/${patientId}`
            });
        }

        function getAllMeds(patientId){
            return $http({
                method: "GET",
                headers    :  {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'},
                url: `/mobiledoc/prisma/clinicalinsight/allMeds/${patientId}`
            });
        }

        function getAllVitals(patientId) {
            return $http({
                method: "GET",
                headers    :  {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'},
                url: '/mobiledoc/prisma/clinicalinsight/getVitalDetails?patientId='+patientId
            });
        }

        function getAllReferrals(patientId) {
            return $http({
                method: "GET",
                headers: {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'},
                url: `/mobiledoc/prisma/clinicalinsight/getReferralData?patientId=${patientId}`
            });
        }

        function getAllImagingAndProcedures(patientId) {
            return $http({
                method: "GET",
                headers: {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'},
                url: `/mobiledoc/prisma/clinicalinsight/getImagingAndProcedures/${patientId}`
            });
        }
    }
})();