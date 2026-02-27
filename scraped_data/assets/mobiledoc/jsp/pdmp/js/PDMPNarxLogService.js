/* 
 * To change this license header, choose License Headers in Project Properties.
 * To change this template file, choose Tools | Templates
 * and open the template in the editor.
 */
angular.module('ecw.service.PDMPNarxLogService', []).factory('PDMPNarxLogService', function($http,$rootScope) {
    var service = {};

    service.getPdmpReportLogList=function(patinetId, currentPage, recordsPage, sortColumnName, sortOrder){
    	var url = '/mobiledoc/jsp/pdmp/PdmpLogServiceController.jsp';
        url = makeURL(url);
        var reqParam = {
            action : "getPdmpReportLogList",
            patinetId : patinetId,
            currentPage :currentPage,
            recordsPage: recordsPage,
            sortColumnName: sortColumnName,
            sortOrder: sortOrder
        };
        return $http({
            method: 'POST', 
            url: url,
            params: reqParam
        });
    };

    service.getLatestPdmpReportLogList=function(patinetId, encounterId){
        var url = '/mobiledoc/jsp/pdmp/PdmpLogServiceController.jsp';
        url = makeURL(url);
        var reqParam = {
            action : "getLatestNarxScore",
            patinetId : patinetId,
            encounterId: encounterId
        };
        return $http({
            method: 'POST',
            url: url,
            params: reqParam
        });
    };

    return service;
});