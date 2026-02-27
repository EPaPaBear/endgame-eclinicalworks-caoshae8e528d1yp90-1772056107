/**
 * @author Chris
 */

angular.module("bh.service.documentationLogs",[]).service('bhLogsService', function($http){
    const URL = '/mobiledoc/behavioralhealth/bhLogs/';
    let findAll = function (param){ return doPost(URL+'findAll', param);};
    let save = function (param) { return doPost(URL+'save', param)};
    let saveAll = function (param) { return doPost(URL+'saveAll', param)};
    //HRA START
    let getAssessment = function (url,param) { return doPost(url, param)};
    //HRA END

    //CarePlanReviewSetup START
    let getProgramsData = function (url,param) { return doPost(url, param)};
    //CarePlanReviewSetup END

    function doPost(url, data) {
        return $http({method: 'POST', url: url, data: data, headers: {'Content-Type': 'application/json'}});
    }

    return{save : save, saveAll : saveAll, findAll : findAll,getAssessment:getAssessment,getProgramsData:getProgramsData}
});