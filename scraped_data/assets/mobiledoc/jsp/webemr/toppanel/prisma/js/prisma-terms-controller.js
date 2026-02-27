(function(){
    angular.module('prismaAppTerms', [])
    .controller('termsAndPolicyCtrl', ['$scope', 'requestParam', '$modalInstance', 'PrismaAppService', '$sce',
    function ($scope, requestParam, $modalInstance, PrismaAppService, $sce) {
        let termsAndPolicyCtrl = this;
        termsAndPolicyCtrl.isTermsLoaded = false;
        termsAndPolicyCtrl.isTermsLoadedSuccessfully = false;
        termsAndPolicyCtrl.apuId = getItemKeyValue('AutoUpgradeKey');
        termsAndPolicyCtrl.title = requestParam.title
        termsAndPolicyCtrl.termsUrl = requestParam.termsUrl;
        termsAndPolicyCtrl.termsInfo = requestParam.termsInfo;
        termsAndPolicyCtrl.cancel = function(){
            $modalInstance.dismiss('cancel');
        }

        termsAndPolicyCtrl.getPrismaTerms = function(){
            PrismaAppService.getServerVersion().then(function (version) {
                if(undefined !== version && typeof version === "string"){
                    PrismaAppService.getPrismaTerms(termsAndPolicyCtrl.termsInfo,version, termsAndPolicyCtrl.apuId).then(function (result) {
                        termsAndPolicyCtrl.isTermsLoaded = true;
                        if(undefined !== result && typeof result === "string" && result.includes("~") && result.split("~")[0].trim().length>0){
                            termsAndPolicyCtrl.isTermsLoadedSuccessfully = true;
                            termsAndPolicyCtrl.notes = $sce.trustAsHtml(result.split("~")[0]);
                        }else{
                            termsAndPolicyCtrl.isTermsLoadedSuccessfully = false;
                        }
                    }, function () {
                        termsAndPolicyCtrl.isTermsLoaded = true;
                        termsAndPolicyCtrl.isTermsLoadedSuccessfully = false;
                    });
                }
            }, function () {
                termsAndPolicyCtrl.isTermsLoaded = true;
                termsAndPolicyCtrl.isTermsLoadedSuccessfully = false;
            });
        }
    }])
})()