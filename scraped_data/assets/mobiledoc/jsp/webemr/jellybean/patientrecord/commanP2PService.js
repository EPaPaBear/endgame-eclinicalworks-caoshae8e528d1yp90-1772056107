angular.module("p2pCommanObjsModule", []).factory('p2pCommonService', function ($http,$modal, $ocLazyLoad) {
	var p2pCommanObjs = {};
	p2pCommanObjs.uploadAttachmentObj = {
		 refReqId : '0',
         patientId : '0',
         assignedToId : '0',
         assignedTo : '',                
         date : '',
         prioritiy : '0',
         trType : '',
         trId : '',
         scannedBy : ''
	};
	
	return {        
		prepareP2pParams: function (params) {
			p2pCommanObjs.uploadAttachmentObj = params;
		},
        uploadP2PAttachmentToFTP: function () {
            try {
                 params = $.param(p2pCommanObjs.uploadAttachmentObj);
                 return $http({
                     method: "POST",
                     url: makeURL("/mobiledoc/jsp/ereferralemr/getHtmlForAttachments.jsp"),
                     data: params,
                     headers: {'Content-Type': 'application/x-www-form-urlencoded'}
                 });
            } catch (err) {
            	console.log(err);
            }
        },
    validateBreakGlass : function(btgObject,okCallback,cancelCallback) {
      if(btgObject.patientId > 0 && getItemKeyValue("EnterpriseDirectory").toLowerCase() === "yes"
          && getItemKeyValue("EnableBreakGlass").toLowerCase() === "yes"
          && getPermission("EnableBreakGlass",global.TrUserId)) {
        var warningObj = checkEnterpriseAccess(btgObject.patientId, global.TrUserId);
        if(warningObj.Warning === "true") {
          this.openBreakGlassModal(btgObject.patientId, global.TrUserId, warningObj.WarnId,okCallback,cancelCallback);
          return false;
        }
      }
      return true;
    },
    openBreakGlassModal : function(patientId, nTrUserId, warningid,okCallback,cancelCallback) {
      $ocLazyLoad.load({
        name: "breakGlassWarning",
        files: [
          "/mobiledoc/jsp/webemr/menu/file/enterpriseDirectory/js/breakGlassWarningController.js"
        ],
        cache: true
      }).then(function() {
        var url = '/mobiledoc/jsp/webemr/menu/file/enterpriseDirectory/breakGlassWarning.jsp?nTrUserId=' + nTrUserId + '&ptid=' + patientId + '&warningid=' + warningid;
        var customStructModalInstance = $modal.open({
          templateUrl: makeURL(url),
          controller: 'breakGlassWarningController',
          windowClass: 'app-modal-window bluetheme breakGlassModalDiv',
          backdrop: "false",
          keyboard:false
        });
        customStructModalInstance.result.then(okCallback,cancelCallback);
      });
    }
    };
});