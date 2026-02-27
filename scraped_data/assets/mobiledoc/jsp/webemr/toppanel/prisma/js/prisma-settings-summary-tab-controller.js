(function () {
    angular.module('prismaSummarySettingsTabModule', [])
        .controller('prismaSummarySettingsTabController', ['$scope', 'PrismaAppService', '$observableService', '$timeout', 'PrismaSettingsService', function ($scope, PrismaAppService, $observableService, $timeout, PrismaSettingsService) {
            var summarySettingsCtrl = this;
            summarySettingsCtrl.dirtyFlag = false;
            summarySettingsCtrl.pnDefaultMode=1;

            summarySettingsCtrl.initMethod = function () {
                summarySettingsCtrl.getSummarySectionSettings();
            }


            summarySettingsCtrl.setDirtyFlag = function (flag) {
                summarySettingsCtrl.dirtyFlag=flag;
                PrismaAppService.setPrismaDirtyCheck(flag);
            }

            $observableService.subscribe('saveSummarySectionSettings', function (response) {
                if (summarySettingsCtrl.dirtyFlag) {
                    summarySettingsCtrl.saveSummarySectionSettings(response);
                }
            });

            summarySettingsCtrl.getSummarySectionSettings = () => {
                PrismaSettingsService.getSummarySectionSettings()
                    .then((response) => {
                        if (response) {
                            let defaultMode=response.prismaUserProfileSettingData.pnDefaultMode
                            summarySettingsCtrl.pnDefaultMode = defaultMode!==0?1:0;
                        } else {
                            ecwAlert("Something went wrong, please try again later.");
                        }
                    }, function () {
                        ecwAlert("Something went wrong, please try again later.");
                    })
            }
            summarySettingsCtrl.saveSummarySectionSettings = function () {
                let sendObject = {
                    "pnDefaultMode": summarySettingsCtrl.pnDefaultMode
                }
                PrismaSettingsService.saveSummarySectionSettings(sendObject)
                    .then((response) => {
                        if (response) {
                            if (response.status && "failed" === response.status) {
                                ecwAlert("Something went wrong, please try again later.");
                                return;
                            }
                            summarySettingsCtrl.setDirtyFlag(false);
                        }
                        notification.show('success','', "Section settings saved successfully.", 4000, '','.summary-settings');
                    }, function () {
                        ecwAlert("Something went wrong, please try again later.");
                    })
            }
            $scope.$on("$destroy", function (event) {
                $observableService.unsubscribe('savePrismaHighlightsSettings');
            });
        }])

})()