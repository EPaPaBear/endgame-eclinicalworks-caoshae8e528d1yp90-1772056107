angular.module('prismaHealowHubModule',[]).controller("PrismaHealowHubController", function ( $scope, $timeout, $modal, $sce, PrismaAppService, $observableService) {
    // Tejas Shah
    var prismaHealowHubCtrl = this;
    $observableService.subscribe("callHealowHub", function (data) {
        prismaHealowHubCtrl.patientId = data.data.patientId;
        prismaHealowHubCtrl.encounterId = data.data.encounterId;
        prismaHealowHubCtrl.userId = data.data.userId;
        prismaHealowHubCtrl.init();
    })
    prismaHealowHubCtrl.init = function () {
        PrismaAppService.getHealowHubUrl(prismaHealowHubCtrl.patientId,prismaHealowHubCtrl.userId, prismaHealowHubCtrl.encounterId).then(function (data) {
            if(typeof data !== "undefined" && typeof data.healowHubUrl !== "undefined" && data.healowHubUrl.trim() !== '' && data.healowHubUrl.trim().length>0){
                angular.element('#healowHubContent').html($('<iframe id="healowHubModal" style="border: 0px solid;width: calc(100% - 15px);height: calc(100vh - 145px);overflow: scroll;" />').attr('src', data.healowHubUrl.trim()));
            } else {
                angular.element('#healowHubError').show();
            }
            angular.element('#healowHubProgressBar').hide();
        }, function (errorMsg) {
            angular.element('#healowHubProgressBar').hide();
            angular.element('#healowHubError').show();
            ecwAlert(errorMsg);
        });
    }

    $scope.$on("$destroy", function (event) {
        $observableService.unsubscribe("callHealowHub");
    });

  })
