angular.module('ecw.rpm.viewNotesApp', []).directive('rpmViewNotes',
    function($http, $modal, $ocLazyLoad) {
        return {
            restrict : 'AE',
            replace : 'true',
            scope : {
                notestext : '=',
                callbackfunction: '&',
                devicesList :'=',
                subject :'=',
                tags :'='
            },
            link : function(scope, element, attrs, ngModelCtrl) {
                element.click(function(){
                    $ocLazyLoad.load({
                        name: 'rpmViewNotes',
                        files: ['/mobiledoc/jsp/webemr/ccmr/rpm/timer/js/rpmViewNotesController.js',
                            '/mobiledoc/jsp/webemr/ccmr/rpm/timer/css/rpm-timer-modal.css',
                            '/mobiledoc/jsp/webemr/js/perfect-scrollbar.jquery.min.js'
                        ]
                    }).then(function() {
                        scope.rpmViewNotesData={
                            notestext : scope.notestext,
                            devicesList :scope.devicesList,
                            subject :scope.subject,
                            tags :scope.tags,
                            callbackfunction: scope.callbackfunction
                        };

                        $modal.open({
                            templateUrl: makeURL('/mobiledoc/jsp/webemr/ccmr/rpm/timer/rpmViewNotesModal.html?'),
                            controller: 'rpmViewNotesController',
                            controllerAs:'rpmViewNotesCtrl',
                            keyboard:false,
                            backdrop:'static',
                            size: 'lg',
                            windowClass: 'bluetheme add-manually-model rpm-view-notes',
                            animation: true,
                            resolve : {
                                rpmViewNotesData: function() {
                                    return scope.rpmViewNotesData;
                                }
                            }
                        });
                    }, function(e) {

                    });
                });
            }
        };
    });
