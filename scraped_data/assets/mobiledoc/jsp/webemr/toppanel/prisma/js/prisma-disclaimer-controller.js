angular.module('prismaAppDisclaimerModule',[]).controller("PrismaDisclaimerController", function ( $scope, $ocLazyLoad, $timeout,$modal, PrismaAppService, $observableService, $window, PRISMA_CONSTANT, requestParam, $modalInstance, $sce) {
    var prismaDisclaimerCtrl = this;
    prismaDisclaimerCtrl.showDisclaimer = false;
    prismaDisclaimerCtrl.close = function (){
        if (!prismaDisclaimerCtrl.hideDisclaimerDoNotShowMsg) {
            if(!prismaDisclaimerCtrl.isDisclaimerHideChecked){
                PrismaAppService.setPrismaDisclaimerDate();
            }
            PrismaAppService.getProfileData()['showprismadisclaimer'] = prismaDisclaimerCtrl.isDisclaimerHideChecked;
        }
        $modalInstance.close();
    }
    prismaDisclaimerCtrl.init = function (){
        let data = requestParam.data;
            if(data){
                    prismaDisclaimerCtrl.showDisclaimer = true;
                    prismaDisclaimerCtrl.isDisclaimerHideChecked = 1;
                    prismaDisclaimerCtrl.hideDisclaimerDoNotShowMsg = false;
                    prismaDisclaimerCtrl.notes =$sce.trustAsHtml(decodeHTMLContent((data.disclaimerNotes)));
                    prismaDisclaimerCtrl.showCISINotes = false;
                    if(data.cisiDisclaimerNotes){
                        prismaDisclaimerCtrl.cisiNotes = $sce.trustAsHtml(decodeHTMLContent((data.cisiDisclaimerNotes)));
                        prismaDisclaimerCtrl.showCISINotes = true;
                    }
            }else {
                $modalInstance.dismiss("ERROR");
                ecwAlert("Something went wrong, Please try after sometime.");
            }
    }

    prismaDisclaimerCtrl.openPrismaTerms = function (prismaTermsType) {
        if(undefined !== prismaTermsType && typeof prismaTermsType === "string" && ('TERMS_AND_CONDITIONS'===prismaTermsType || 'PRIVACY_POLICY'===prismaTermsType)){
            let termsUrl;
            let title;
            let termsInfo;
            if('TERMS_AND_CONDITIONS'===prismaTermsType){
                termsUrl = getItemKeyValue('PrismaTermsAndConditionsUrl');
                title = "Terms and Conditions";
                termsInfo = "prismaTermsConditions";
            }else if('PRIVACY_POLICY'===prismaTermsType){
                termsUrl = getItemKeyValue('PrismaPrivacyPolicyUrl');
                title = "Privacy Policy";
                termsInfo = "prismaPrivacyPolicy";
            }
            if(undefined !== termsUrl && typeof termsUrl === "string" && termsUrl.length>0){
                if(termsUrl.startsWith("http")){
                    let window_datetime = new Date().getTime();
                    window.open(termsUrl,"Prisma_terms"+window_datetime);
                }else{
                    let params = {
                        termsUrl:termsUrl,
                        title:title,
                        termsInfo:termsInfo
                    }
                    $modal.open({
                        templateUrl: '/mobiledoc/jsp/webemr/toppanel/prisma/template/prisma-terms-container.html',
                        windowClass: 'prismaTerms',
                        controller: 'termsAndPolicyCtrl',
                        controllerAs: 'termsAndPolicyCtrl',
                        backdrop: false,
                        size: 'lg',
                        backdropClass: 'fadeBackdrop',
                        resolve : {
                            requestParam: function () {
                                return params;
                            }
                        }
                    });
                }
            }else{
                ecwAlert("Invalid configuration found.");
            }
        }else{
            ecwAlert("Invalid request received.");
        }
    }
})