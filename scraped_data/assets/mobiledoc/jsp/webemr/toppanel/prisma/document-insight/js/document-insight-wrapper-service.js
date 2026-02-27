(() => {
    'use strict';

    angular.module('ecw.documentInsight')
        .service('DocumentInsightTileWrapperService', ['$http', function ($http) {

            this.validateFileSizeAndGetSettings = (filename, path, extension) => {
                return $http({
                    method: "POST", url: makeURL('/mobiledoc/prisma/document-insights/validateFileSizeAndGetSettings'),
                    headers: {'Content-Type': 'application/json'},
                    params: {filename, path, extension}
                })
            };

            this.saveTileSettings = (tileSequence, rcpSetting) => {
                return $http({
                    method: "POST",
                    headers: {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'},
                    data: $.param({tileSequence, defaultRightPanel: rcpSetting}),
                    url: '/mobiledoc/prisma/document-insights/saveUserSetting'
                })
            };

            this.setTileSettings = tileSettings => this.tileSettings = tileSettings;
            
            this.getTileSettings = () => this.tileSettings;
            
            this.setDocumentInsights = params => this.params = params;

            this.getDocumentInsights = () => this.params;

            this.importProblemList = (patientId, problemList, notes) => {
                return $http({
                    method: "post",
                    headers: {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'},
                    url: "/mobiledoc/prisma/document-insights/importProblemList",
                    data: $.param({'patientId': patientId, 'problemList': problemList, 'notes': notes}),
                    transformResponse: function (data) {
                        return data;
                    }
                });
            };

            this.hasAIDocInsightSecAccess = () => {
                return hasSecurityPermission("AllowDocumentInsights");
            }

            function trimString(data) {
                return String.prototype.trim.call(data === null || data === undefined ? "" : data);
            }

            function hasSecurityPermission(permissionKey) {
                var permission = false;
                $.ajax({
                    type: "POST",
                    url: "/mobiledoc/jsp/catalog/xml/security/getPermission.jsp",
                    async: false,
                    cache: false,
                    data: {permission: permissionKey},
                    success: function (response) {
                        permission = trimString(response);
                        if (permission == true || permission == "true") {
                            permission = true;
                        } else {
                            permission = false;
                        }
                        return false;
                    }
                });
                return permission;
            }

            this.showAIErrorMessage = (headerText, message) => {
                showAlertMessage("<div class='text-left mt-24'><i class='icon icon-ai-primary mr5'></i>&nbsp;<b>" + ((!headerText) ? "Error" : headerText) + "</b><br/></br>" + ((!message) ? errMessage : message) + " </div>", '', 'ErrorMsg', '', '', '400px;', 'ok', '', 'showAlert', '', '', '', '', false);
            }

            this.getDocInsights = (patientId, recordId, recordType, refreshClicked) => {
                return $http({
                    method: "POST",
                    headers: {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'},
                    url: '/mobiledoc/prisma/document-insights/generateDocInsights',
                    data: $.param({patientId, recordId, recordType, refreshClicked})
                })
            }

            this.getSummarizationTransactionStatus = (patientId, transactionId) => {
                return $http({
                    method: "POST",
                    headers: {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'},
                    url: '/mobiledoc/prisma/summarization/getSummarizationTransactionStatus',
                    data: $.param({patientId, transactionId})
                })
            }

            this.getPatientDetails = (patientId) => {
                return $http({
                    method: "POST",
                    headers: {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'},
                    url: '/mobiledoc/prisma/document-insights/getPatientDetails',
                    data: $.param({patientId})
                });
            };
        }]);
})();
