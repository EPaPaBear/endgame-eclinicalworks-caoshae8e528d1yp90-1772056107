angular.module('prismaImportDirectiveServiceApp', []).service("prismaImportDirectiveService", ["$http", "$q", function ($http, $q) {
    return ({
        getImportItemListAndShowCCRImportExceptionModal:getImportItemListAndShowCCRImportExceptionModal,
        processCompleteSnomedToICD:processCompleteSnomedToICD,
        convertSnomeToICD:convertSnomeToICD,
        setIcdData:setIcdData,
        getSnomeedAddress:getSnomeedAddress,
        searchDrugName:searchDrugName,
        getDosageInfo:getDosageInfo,
        saveMappedMeds: async function (param) {
            param.calledFrom="prisma";
            return await $http({
                method: "POST",
                headers    :  {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'},
                url: '/mobiledoc/jsp/empi/dashboard/saveMappedMeds.jsp',
                data: $.param(param)
            });
        },
    });

    function getSnomeedAddress(){
        return $http({
            method: "POST",
            headers    :  {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'},
            url: '/mobiledoc/prisma/overview/getSnomedAddress',
            data: {}
        });
    }

    function setIcdData(nRefId) {
        var data='snomedInput={"refId": "'+$.trim(nRefId)+'", "action": "getIcd", "requestSource": "WebClient"}';
        return $http({
            method: "POST",
            headers :{'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'},
            url: '/mobiledoc/jsp/catalog/xml/edi/snomedicd10/snomedIcdConversionService.jsp',
            data: data
        });
    }

    function convertSnomeToICD(data){
        return $http({
            method: "POST",
            headers    :  {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'},
            url: '/mobiledoc/jsp/catalog/xml/edi/snomedicd10/snomedIcdConversionService.jsp',
            data: $.param(data)
        });
    }

    function processCompleteSnomedToICD(dataObj){
        return $http({
            method: "POST",
            headers    :  {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'},
            url: '/mobiledoc/jsp/catalog/xml/edi/snomedicd10/snomedToIcdPost.jsp',
            data:'calledFrom=prisma&formData=' + JSON.stringify(dataObj),
        });
    }

    function getImportItemListAndShowCCRImportExceptionModal(data){
        data.calledFrom="prisma";
        return $http({
            method: "POST",
            headers    :  {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'},
            url: '/mobiledoc/jsp/webemr/rightpanel/serviceEhxRightPane.jsp',
            data: $.param(data)
        });
    }

    function searchDrugName(data){
        return $http({
            method: "POST",
            headers    :  {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'},
            url: makeURL("/mobiledoc/jsp/empi/dashboard/searchDrugName.jsp"),
            data: $.param(data)
        });
    }

    function getDosageInfo(data,medicSpanEnable){
        var urlDoseage="";
        if(medicSpanEnable){
            urlDoseage = "/mobiledoc/jsp/ecwrx/getDoses.jsp";
        }else{
            urlDoseage = "/mobiledoc/jsp/catalog/xml/getDosesForRx.jsp";
        }
        return $http({
            method: "POST",
            headers    :  {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'},
            url: urlDoseage,
            data: $.param(data)
        });
    }

}])