angular.module('rpmEnrollmentLogsDirectiveWrapper', []).directive('rpmEnrollmentLogsWrapper',
    function($modal, $ocLazyLoad) {
        return {
            restrict : 'AE',
            replace : false,
            scope : {
                patientId : '=',
                ptAcoId : '=',   // allowed values are 'one' and 'all'
                programId : '=',        // icd value if pre selection is available'
                programType : '=',
            },
            template:'<button type="button" class="btn btn-secondary btn-sm btn-xs pull-left ml5" ng-click="launchEnrollmentLogsModal()">Logs</button>',
            link: function (scope,element) {
                scope.launchEnrollmentLogsModal = function() {
                    $ocLazyLoad.load({
                        name: 'rpmEnrollLogsModal',
                        files: ['/mobiledoc/jsp/webemr/ccmr/rpm/enrollment/css/rpm-logs.css',
                            '/mobiledoc/jsp/webemr/ccmr/rpm/css/perfect-scrollbar.css',
                            '/mobiledoc/jsp/resources/jslib/angular-perfect-scrollbar/src/angular-perfect-scrollbar.js',
                            '/mobiledoc/jsp/webemr/ccmr/rpm/js/vendorjs/perfect-scrollbar.min.js',
                            '/mobiledoc/jsp/webemr/ccmr/rpm/enrollment/js/directive/common-directive.js',
                            '/mobiledoc/jsp/webemr/ccmr/rpm/enrollment/js/controller/rpm-enrollment-logs-modal-ctrl.js',
                            '/mobiledoc/jsp/webemr/ccmr/rpm/enrollment/js/directive/printDirective.js']
                    }).then(function () {
                        var modalInstance = $modal.open({
                            templateUrl: makeURL('/mobiledoc/jsp/webemr/ccmr/rpm/enrollment/views/rpm-enrollment-logs-modal.html'),
                            controller: 'rpmEnrollLogsModalCtrl',
                            controllerAs: 'enrollLogs',
                            backdrop: 'false',
                            windowClass: 'custom-modal w1000 zIndex',
                            resolve: {
                                requestParam: function () {
                                    return {
                                        patientID: scope.patientId,
                                        ptacoId: scope.ptAcoId,
                                        modalTitle: "CCM/PCM Logs",
                                        programId: scope.programId,
                                        programType : scope.programType
                                    };
                                }
                            },
                        });
                    });
                };
            }
        };
    });
