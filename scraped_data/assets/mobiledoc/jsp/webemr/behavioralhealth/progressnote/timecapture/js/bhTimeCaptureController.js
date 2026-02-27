/**Pritam K
 *
 */
(function () {
    var BHTimecaptureModule = angular.module('BHTimecaptureModule', []);

    function bhTimeCaptureController($scope, $http, $ocLazyLoad) {
        var bhTimeCtrl = this;
        bhTimeCtrl.timeCapDetailsArray = [];
        bhTimeCtrl.encId = bh_encounterId;
        bhTimeCtrl.patientId = bh_patientId;
        bhTimeCtrl.openStopTimerModal = bh_OpenStopTimerModal;
        bhTimeCtrl.pnLinkFooterObj = {showPnFooter:false,showPrevButton:false,showNextButton:true,prevLabel:"",nextLabel:"",sectionName:"TimeCapture"};
        bhTimeCtrl.concurrencyObj = {concurrency:true,concurrencyKey:"bh_timecapture",lockObj:{},concurrencyFailCallBack:""};
        bhTimeCtrl.concurrencyObj.lockObj = {
            formName: bhTimeCtrl.concurrencyObj.concurrencyKey,
            uniqueKey: bhTimeCtrl.concurrencyObj.concurrencyKey + "_" + bhTimeCtrl.encId,
            g_cancel: false,
            strKey: "",
            isOpenform: false,
            categoryId: "0"
        };

        bhTimeCtrl.checkConcurrency = function () {
           acquireFormLock(bhTimeCtrl.concurrencyObj.lockObj, acquireFormLockCallBackBhTimeCatpture);
        }

        function acquireFormLockCallBackBhTimeCatpture() {
            if (bhTimeCtrl.concurrencyObj.lockObj.g_cancel) {
                bhTimeCtrl.closeTimeCaptureAndRefreshProgressNote();
            }else if(bh_OpenStopTimerModal){
                bhTimeCtrl.stopTimer();
            }
        }

        bhTimeCtrl.closeTimeCaptureAndRefreshProgressNote = function () {
            $('#pn').modal('hide');
            refreshDashboard(bhTimeCtrl.encId, bhTimeCtrl.patientId, "progressNote", "");
        }

        bhTimeCtrl.stopTimer = function(){} // declare for reference - bind with directive
        bhTimeCtrl.checkConcurrency();
    }

    BHTimecaptureModule.controller("bhTimeCaptureController", bhTimeCaptureController);
})();