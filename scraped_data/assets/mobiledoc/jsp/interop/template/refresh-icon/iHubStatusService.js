angular.module('iHubStatusServiceModule', []).service("iHubStatusService", ["$http", function ($http) {
    return ({
        getIhubTransactionStatus: getIhubTransactionStatus,
        hasNewTransaction: hasNewTransaction,
        getRefreshInterval: getRefreshInterval
    });

    function getIhubTransactionStatus(data, onSuccess, onFailed) {
        const request = httpPostRequestBody('/mobiledoc/interop/milestone/getIhubTransactionStatus', data);
        request.then(onSuccess, onFailed);
    }

    function hasNewTransaction(data, onSuccess, onFailed) {
        const request = httpPostRequestBody('/mobiledoc/interop/milestone/getNewTransaction', data);
        request.then(onSuccess, onFailed);
    }

    function getRefreshInterval(onSuccess, onFailed) {
        const data = {}
        const request = httpPostRequestBodywithDataParam('/mobiledoc/interop/milestone/getRefreshInterval', data);
        request.then(onSuccess, onFailed);
    }

    function httpPostRequestBody(url, data) {
        return $http({
            method: "POST",
            url: url,
            params: data
        });
    }

    function httpPostRequestBodywithDataParam(url, data) {
        return $http({
            method: "POST",
            url: url,
            data: ''
        });
    }
}])