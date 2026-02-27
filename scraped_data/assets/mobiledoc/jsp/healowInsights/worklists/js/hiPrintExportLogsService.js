(function () {
    angular.module('hiPrintExportLogsService', []).service('hiPrintExportLogsService', function ($http) {
        return {
            savePrintExportLogData: function (reqParams) {
                return $http({
                    method: "POST",
                    url: makeHealowInsightsAPIURL('worklists/printexportlogs/save'),
                    data: JSON.stringify(reqParams),
                    cache: false
                });
            },
        };
    });
})();