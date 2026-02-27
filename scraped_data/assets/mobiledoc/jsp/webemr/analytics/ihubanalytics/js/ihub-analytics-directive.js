!function () {
    let app = angular.module("iHubAnalyticsDirective", []);

    app.directive('ihubAnalytics', function ($ocLazyLoad, $modal) {
        return {
            restrict: 'AE',
            replace: 'true',
            link: function (scope, element) {
                let isIHubDashboardBtnClicked = false;
                element.on('click', function () {
                    if (!isIHubDashboardBtnClicked) {
                        isIHubDashboardBtnClicked = true;
                        let allFiles = getHighchartsFiles();
                        let moduleFiles = [
                            '/mobiledoc/jsp/webemr/analytics/ihubanalytics/js/service/ihub-analytics-service.js',
                            '/mobiledoc/jsp/webemr/analytics/ihubanalytics/js/ihub-analytics-modal-controller.js',
                            '/mobiledoc/jsp/webemr/analytics/ihubanalytics/css/ihub-analytics.css',
                            '/mobiledoc/jsp/resources/jslib/highcharts/modules/treemap.js',
                            '/mobiledoc/jsp/resources/jslib/highcharts/modules/no-data-to-display.js',
                            '/mobiledoc/jsp/resources/jslib/highcharts/highcharts-3d.js',
                            '/mobiledoc/jsp/resources/jslib/highcharts/highcharts-more.js',
                            '/mobiledoc/jsp/resources/jslib/highcharts/modules/solid-gauge.js',
                            '/mobiledoc/jsp/resources/jslib/bootstrap-datepicker/js/bootstrap-datepicker.js',
                            '/mobiledoc/jsp/resources/jslib/bootstrap-datepicker/dist/css/bootstrap-datepicker.css',
                            '/mobiledoc/jsp/resources/jslib/angular-ui-bootstrap/dist/ui-bootstrap-tpls.js',
                            '/mobiledoc/jsp/resources/jslib/perfect-scrollbar/css/perfect-scrollbar.css',
                            '/mobiledoc/jsp/resources/jslib/perfect-scrollbar/dist/perfect-scrollbar.js',
                            '/mobiledoc/jsp/resources/jslib/angular-perfect-scrollbar/src/angular-perfect-scrollbar.min.js',
                            '/mobiledoc/jsp/webemr/analytics/ihubanalytics/js/ihub-analytics-controller.js',
                            '/mobiledoc/jsp/webemr/analytics/ihubanalytics/js/ihub-analytics-constants.js'];
                        allFiles = allFiles.concat(moduleFiles);
                        $ocLazyLoad.load({
                            name: 'iHubAnalyticsModalApp',
                            files: allFiles,
                            serie: true,
                            cache: false
                        }).then(function () {
                            let modalInstance = $modal.open({
                                templateUrl: makeURL('/mobiledoc/jsp/webemr/analytics/ihubanalytics/ihub-analytics-modal.html'),
                                controller: 'iHubAnalyticsModalController',
                                controllerAs: 'iHubModalCtrl',
                                windowClass: 'ihub-analytics ihub-analytics-modal bluetheme',
                                backdrop: "static",
                                size: 'lg'
                            });
                            modalInstance.result.then(function(response) {
                            }, function() {
                                isIHubDashboardBtnClicked = false;
                            });
                        }, function () {
                            isIHubDashboardBtnClicked = false;
                            ecwAlert("Failed to load page, Please try again.", "eClinicalWorks", null, "", "orangetheme");
                        });

                        function getHighchartsFiles() {
                            let highchartsFiles = [];
                            if ((!window.Highcharts) || (window.Highcharts && !window.Highcharts.stockChart)) {
                                highchartsFiles = [
                                    '/mobiledoc/jsp/resources/jslib/highcharts/highstock.js',
                                    '/mobiledoc/jsp/resources/jslib/highcharts/modules/map.js',
                                    '/mobiledoc/jsp/resources/jslib/highcharts/modules/exporting.js'
                                ];
                            }
                            return highchartsFiles;
                        }
                    }
                });
            }
        };
    });
}();