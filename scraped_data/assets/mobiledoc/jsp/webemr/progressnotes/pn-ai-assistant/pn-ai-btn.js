let pnAiBtnModule = angular.module("ecw.dir.pnAIBtn", []);

pnAiBtnModule.service('pnAiBtnService', pnAiBtnService);
pnAiBtnModule.directive('pnAiBtn', pnAiBtnDirective);

function pnAiBtnService($http) {
    return {
        checkAccess: function(module){
            return $http.get('/mobiledoc/emr/progressnotes/summarize/hasAccess/'+global.TrUserId +"/"+module);
        }
    }
}

function pnAiBtnDirective($ocLazyLoad,$timeout,$modal,pnAiBtnService) {
    return {
        scope: {
            aiRequest: "=",
            aiClasses: "@",
            aiBtnResponsive: "@",
            aiBtnClick: "&",
            applyAiResponse: "&"
        },
        templateUrl : "/mobiledoc/jsp/webemr/progressnotes/pn-ai-assistant/pn-ai-btn.html",
        link: function($scope) {

            $scope.showBtnText = true;
            if ($scope.aiBtnResponsive) {
                if($("#mainPNContent") && $("#mainPNContent").width() <= 960){
                    $scope.showBtnText = false;
                } else if(document.getElementById('pn-modal-icw-btn').classList.contains('active')){
                    $scope.showBtnText = false;
                }
            }

            $scope.hasSecurityAccess = false;
            $scope.isFeatureEnabled = false;
            $scope.title = "";
            let titleObj = [];
            titleObj["HPI"] = {access: "HPI Summarization Assistant", noAccess : "You do not have permission to access HPI Summarization Assistant. Please contact your administrator."}
            $scope.aiClasses = $scope.aiClasses?$scope.aiClasses:"btn btnedit btn-xs btn-lgrey";

            $scope.getTitle = function (module, hasSecurityAccess) {
                if(hasSecurityAccess){
                    $scope.title = titleObj[module].access;
                }else{
                    $scope.title =  titleObj[module].noAccess;
                }
            }

            $scope.checkAIAccess = function (module) {
                pnAiBtnService.checkAccess(module).then(function(response){
                    if(response.data){
                        $scope.isFeatureEnabled = response.data.featureEnabled;
                        $scope.hasSecurityAccess =  response.data.securityAccess;
                    }
                    $scope.getTitle(module, $scope.hasSecurityAccess);
                })
            }

            $scope.checkAIAccess($scope.aiRequest.section);


            $scope.openPNAssistantPopup = function(){
                var initData = {
                    encounterId:$scope.aiRequest.encounterId,
                    patientId:$scope.aiRequest.patientId,
                    categorySelected: $scope.aiRequest.categorySelected,
                    section:$scope.aiRequest.section,
                    parentDomId: $scope.aiRequest.parentDomId,
                    showCategorySearch: $scope.aiRequest.openPopup
                }
                $ocLazyLoad.load({
                    name: 'pnAiAssistantModule',
                    files: [
                        "/mobiledoc/jsp/webemr/progressnotes/pn-ai-assistant/pn-ai-assistant.js",
                        "/mobiledoc/jsp/webemr/progressnotes/pn-ai-assistant/pn-ai-assistant.css",
                        "/mobiledoc/jsp/webemr/progressnotes/templates/category-search.component.js",
                    ]
                }).then(function() {
                    var modalInstance = $modal.open({
                        templateUrl: '/mobiledoc/jsp/webemr/progressnotes/pn-ai-assistant/pn-ai-assistant.html',
                        controller: 'pnAiAssistantController',
                        windowClass: 'pn-ai-popup',
                        backdrop: "static",
                        resolve: {
                            initData: function() {
                                return initData;
                            }
                        }
                    });
                    modalInstance.result.then(function(modalInstanceResponse) {
                        //listening close event
                        $scope.aiRequest.notes = modalInstanceResponse.aiResponse;
                        $scope.aiRequest.categorySelected = modalInstanceResponse.categorySelected;

                        $scope.applyAiResponse();
                    }, function(modalInstanceResponse) {
                        //listening dismiss event
                    });
                }, function(e) {
                    console.log(e);
                });
            };

            $scope.openPNAssistant = function() {
                $scope.aiBtnClick();
                if(!$scope.aiRequest.requestFrom && $scope.aiRequest.requestFrom !== "progressNotesAIBtn"){
                    $timeout(function(){
                        $scope.openPNAssistantPopup();
                    }, 100);
                }
            };


            if($scope.aiRequest.openPopup){
                $scope.openPNAssistant();
            }
        }
    };
}