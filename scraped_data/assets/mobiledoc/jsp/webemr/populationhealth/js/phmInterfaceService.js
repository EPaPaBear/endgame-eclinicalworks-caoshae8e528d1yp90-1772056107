/**
 * @author Pritam K.
 */
(function () {
    var populationHealthModule = angular.module('populationhealth', []);

    populationHealthModule.service('phmInterface', phmInterface);

    function phmInterface($http) {

        const PHM_MODULE_REQUEST_URL_HEADING = '/mobiledoc/populationhealth';

        function getRequestCall(url) {
            return $http({
                method: 'GET',
                url: url
            });
        }

        function getRequestCallWithParam(url,params) {
            return $http({
                method: "GET",
                url: url,
                params:params,
                cache: false
            });
        }

        function postRequestCall(url, requestParams) {
            return $http({
                headers:{"isAjaxRequest":"true"},
                method: 'POST',
                url: url,
                data: JSON.stringify(requestParams)
            });
        }

        function postRequestWithSerializedParams(url, requestParams) {
            return $http({
                method: 'POST',
                url: url,
                data: $.param(requestParams),
                headers: {"isAjaxRequest":"true",'Content-Type': 'application/x-www-form-urlencoded'}
            });
        }

        /* The function below used to make server side call only for PHM module - GET requests */
        function getRequestForPhmModule(url) {
            let finalURL = PHM_MODULE_REQUEST_URL_HEADING + url;
            return getRequestCall(finalURL);
        }

        /* The function below used to make server side call only for PHM module - POST requests */
        function postRequestForPhmModule(url, requestParams) {
            let finalURL = PHM_MODULE_REQUEST_URL_HEADING + url;
            return postRequestCall(finalURL, requestParams);
        }

        /* The function below used to make server side call only for PHM module - POST requests With Serialized Params*/
        function postRequestForPhmModuleWithSerializedParams(url, requestParams) {
            let finalURL = PHM_MODULE_REQUEST_URL_HEADING + url;
            return postRequestWithSerializedParams(finalURL, requestParams);
        }

        return {
            getRequestCall: getRequestCall,
            getRequestCallWithParam: getRequestCallWithParam,
            postRequestCall: postRequestCall,
            postRequestWithSerializedParams: postRequestWithSerializedParams,
            getRequestForPhmModule: getRequestForPhmModule,
            postRequestForPhmModule: postRequestForPhmModule,
            postRequestForPhmModuleWithSerializedParams: postRequestForPhmModuleWithSerializedParams
        }
    }
})();