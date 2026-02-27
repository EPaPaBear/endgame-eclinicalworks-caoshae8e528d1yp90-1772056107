(function () {
    angular.module('prismaHighlightsSettingsTabModule', [])
        .controller('prismaHighlightsSettingsTabController', ['$scope', 'PrismaAppService', '$observableService', '$timeout', 'PrismaSettingsService', function ($scope, PrismaAppService, $observableService, $timeout, PrismaSettingsService) {
            var highlightsSettingsCtrl = this;
            highlightsSettingsCtrl.dirtyFlag = false;
            highlightsSettingsCtrl.pnDefaultMode=0;

            highlightsSettingsCtrl.initMethod = function () {
                highlightsSettingsCtrl.getHighlightsSectionSettings();
                highlightsSettingsCtrl.activeRecordType = null;
            }

            highlightsSettingsCtrl.sortableOption = {
                'items': 'tr', 'handle': '.handle', 'cursor': 'move', start: function (e, ui) {
                }, stop: function (e, ui) {
                    setDirtyFlag(true);
                }
            }

            highlightsSettingsCtrl.changeOnRecordEnableDisable = function ($index, valueStatus) {
                highlightsSettingsCtrl.sectionSettings[$index] = valueStatus;
                setDirtyFlag(true);
            }

            function setDirtyFlag(flag) {
                highlightsSettingsCtrl.dirtyFlag = flag;
                PrismaAppService.setPrismaDirtyCheck(flag);
            }
            highlightsSettingsCtrl.setDirtyFlag = function (flag) {
                setDirtyFlag(flag);
            }

            $observableService.subscribe('savePrismaHighlightsSettings', function (response) {
                if (highlightsSettingsCtrl.dirtyFlag) {
                    highlightsSettingsCtrl.saveHighlightsSectionSettings(response);
                }
            });

            highlightsSettingsCtrl.getHighlightsSectionSettings = () => {
                highlightsSettingsCtrl.sectionSettings = null;
                const PATIENT_LEVEL_SUMMARY_TITLE_ID = 102;
                PrismaSettingsService.getHighlightsSectionSettings({titleId: PATIENT_LEVEL_SUMMARY_TITLE_ID})
                    .then((response) => {
                        if (response) {
                            highlightsSettingsCtrl.pnDefaultMode = response.prismaUserProfileSettingData.pnDefaultMode;
                            highlightsSettingsCtrl.sectionSettings = response.userPreferredSections;
                            highlightsSettingsCtrl.sectionSettings.forEach(item => { item.isEnabled = item.isEnabled === 1});
                        } else {
                            ecwAlert("Something went wrong, please try again later.");
                        }
                    }, function () {
                        ecwAlert("Something went wrong, please try again later.");
                    })
            }
            highlightsSettingsCtrl.saveHighlightsSectionSettings = function (response) {
                for (let i = 0; i < highlightsSettingsCtrl.sectionSettings.length; i++) {
                    highlightsSettingsCtrl.sectionSettings[i].sectionOrder = i + 1;
                }
                const clonedObject = JSON.parse(JSON.stringify(highlightsSettingsCtrl.sectionSettings));
                for (let i = 0; i < clonedObject.length; i++) {
                    clonedObject[i].isEnabled = clonedObject[i].isEnabled ? 1 : 0;
                }
                let sendObject = {
                    "sectionSettings": JSON.stringify(clonedObject),
                    "pnDefaultMode": highlightsSettingsCtrl.pnDefaultMode
                }
                PrismaSettingsService.saveHighlightsSectionSettings(sendObject)
                    .then((response) => {
                        if (response) {
                            if (response.status && "failed" === response.status) {
                                ecwAlert("Something went wrong, please try again later.");
                                return;
                            }
                            setDirtyFlag(false);
                        }
                        notification.show('success','', "Section settings saved successfully.", 4000, '','.highlights-settings');
                    }, function () {
                        ecwAlert("Something went wrong, please try again later.");
                    })
            }
            $scope.$on("$destroy", function (event) {
                $observableService.unsubscribe('savePrismaHighlightsSettings');
            });
        }])

})()