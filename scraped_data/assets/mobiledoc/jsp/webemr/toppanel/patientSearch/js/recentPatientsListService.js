(function () {
angular.module('recentPatientsListServiceModule',[]).service("recentPatientsListService", [ "$http","$q",
    function ($http, $q) {
        return {
            getRecentPatientHistory: getRecentPatientHistory
        };

        function httpPost(url, data) {
            return $http({
                method: "post",
                headers: {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'},
                url: makeURL(url),
                data: $.param(data)
            });
        };
        function getRecentPatientHistory() {
            var request = httpPost('/mobiledoc/patientsearch/recentHistory/getRecentPatientHistory',{});
            return (request.then(handleSuccess, handleError));
        };

        function handleError(response) {
            return $q.reject("Something went wrong, Please try again later.");
        };

        function handleSuccess(response) {
            if (response && response.data && response.data.status && response.data.status === 'success') {
                return $q.resolve(response.data);
            } else  if (response && response.data && response.data.status && response.data.status === 'failed'){
                return $q.reject("Something went wrong, Please try again later.");
            }else{
                return $q.reject("Something went wrong, Please try again later.");
            }
        };
    }
]);
})();