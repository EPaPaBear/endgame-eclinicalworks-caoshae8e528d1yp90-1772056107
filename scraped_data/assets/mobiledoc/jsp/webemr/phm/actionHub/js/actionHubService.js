angular.module('actionHubService',[]).factory("actionHubModuleService", function($http) {
    var result= {
        getPatientDemographicsDetail:getPatientDemographicsDetail,
        checkIfPatientIsRPMEligible:checkIfPatientIsRPMEligible,
        urlGet:urlGet
    };

    function getPatientDemographicsDetail(template_param){
        var url='/mobiledoc/phm/actionHub/getPatientDemographicsDetail';
        return $http({
            method: 'POST',
            url:makeURL(url),
            data: $.param(template_param),
            headers: {'Content-Type': 'application/x-www-form-urlencoded'}
        });
    }

    function checkIfPatientIsRPMEligible(template_param){
        var url='/mobiledoc/phm/cmHub/fetchPatientRPMDetails';
        return $http({
            method: 'POST',
            url:makeURL(url),
            data: $.param(template_param),
            headers: {'Content-Type': 'application/x-www-form-urlencoded'}
        });
    }

    function urlGet(dataUrl) {
        return $http({
            method: 'GET',
            url:makeURL(dataUrl),
            data: '',
            headers: {'Content-Type': 'application/x-www-form-urlencoded'}
        });
    }

    return result;
});