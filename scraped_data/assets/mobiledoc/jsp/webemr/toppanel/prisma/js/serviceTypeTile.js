angular.module('prisma.clinicalInsights.serviceTypeTile', ['prismaAppClinicalInsightService', 'prismaAppServiceModule'])
    .directive('serviceTypeTile', ['prismaClinicalInsightService', 'PrismaAppService', '$observableService','PRISMA_CONSTANT', (PrismaClinicalInsightService, PrismaAppService, $observableService,PRISMA_CONSTANT) => {
        return {
            restrict: 'E',
            scope: {
                serviceTypes: '=',
                error: '=',
                header: "@",
                isFromSearchInsights: '=',
                patientId: '='
            },
            templateUrl : '/mobiledoc/jsp/webemr/toppanel/prisma/template/serviceTypeTile.html',
            link: scope => {
                scope.showMoreData = true;
                scope.recordIndexMap = {};

                let listener = scope.$watch('serviceTypes', () => {
                    renderTile();

                });

                scope.$on("$destroy", function(){
                    listener();
                });

                scope.checkDate = (date) => {
                    if(!date) {
                        return 'N/A';
                    }
                    return date?.split(' ')[0];

                };

                scope.checkAdmissionDischargeDate = (admissionDate, dischargeDate) => {
                    if(!admissionDate || !dischargeDate) {
                        return 'N/A';
                    }
                    return admissionDate?.split(' ')[0].concat(' - ').concat(dischargeDate?.split(' ')[0]);
                }

                scope.openServiceTypeInRecords = function(recordId, recordType, isSubEnc) {
                    var requestParamObj = {
                        searchContext: 1,
                        sourceList: JSON.stringify([]),
                        visitDate: '',
                        patientId: scope.patientId,
                        loggedUserId: global.TrUserId,
                        currentPage: 1,
                        recordPerPage: 1,
                        suggestionType: '',
                        searchSuggestionId: '',
                        selectedPrismaRecordId: 0,
                        getExtTitleCount: true,
                        isIndexMappingNeeded : angular.equals({}, scope.recordIndexMap),
                        recordType: recordType,
                        recordId : recordId,
                        requestFor : 'SI-tile',
                        sessionCategory:PRISMA_CONSTANT.SESSION_CATEGORY.PRISMA
                    };
                    const responsePromise = PrismaAppService.getPrismaRecords(requestParamObj);
                    responsePromise.then(function (data) {
                        if (data) {
                            let records = PrismaAppService.getExternalvisitRecordData(data);
                            if (angular.equals({}, scope.recordIndexMap)) {
                                if (data.hasOwnProperty('docIndexDetails')) {
                                    scope.recordIndexMap = data.docIndexDetails;
                                }
                            }
                            let recordIndex = scope.recordIndexMap[recordId + "_" + recordType];
                            if (!recordIndex) {
                                ecwAlert("Could not show record detail")
                                return;
                            }
                            recordIndex = recordIndex - 1;
                            let tabData = records['externalVisits'][0][0];
                            tabData.recordIndex = recordIndex;
                            tabData.isSubEnc = isSubEnc;
                            $observableService.publish('JumpToRecordsFromSI', tabData);
                        }
                    }, function (errorMsg) {
                        ecwAlert(errorMsg);
                    });
                }
                
                const renderTile = () => {
                    
                }
            }
        };
    }]);