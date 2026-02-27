/** 
 * Author	: taralkumarv
 * Date		: 04-05-2017
 * Template : created using eCW plugin
 */
(function() {
	'use strict';
	var ImplantsService = ImplantsService;
	angular.module('emrImplantsAppService', []).factory('emrImplantsService', ImplantsService);
	function ImplantsService($http) {
			return {
				getImplants				: getImplants,
				addImplant				: addImplant,
				updateImplant			: updateImplant,
				getSnomedInfo			: getSnomedInfo,
				updateVarifyFlag		:updateVarifyFlag,
				getVarifyFlag			:getVarifyFlag,
				isUDIExist              :isUDIExist,
				isDuplicateUDIWarningSecurityKey	:isDuplicateUDIWarningSecurityKey,
				isRemindMeUpdate		:isRemindMeUpdate
			};
			function getImplants(encounterId,patientId){
                return $http({
                	method		: 	'GET',
					url 		: 	makeURL("/mobiledoc/ascWeb/Implants.go/getImplants/"+encounterId+"/"+patientId)
                });
			};
			function addImplant(implants, encounterId,patientId, implantChanged){
                return $http({
                	method		: 	'POST',
					url 		: 	makeURL("/mobiledoc/ascWeb/Implants.go/addImplants/"+encounterId+"/"+encounterId+"/"+patientId+"/"+implantChanged),
					data		:   implants
                });
			};
			function updateImplant(implant){
                return $http({
                	method		: 	'POST',
					url 		: 	makeURL("/mobiledoc/ascWeb/Implants.go/updateImplant"),
					data		:   implant
                });
			};
			
			function getSnomedInfo(udi, encounterId, patientId){
                return $http({
                	method		: 	'GET',
                	url			:	makeURL("/mobiledoc/ascWeb/Implants.go/getSnomedInfo?udi="+ udi+"&encounterId="+encounterId+"&patientId="+patientId)
                });
			}
			function updateVarifyFlag(encId,patientId,flag){
                return $http({
                	method		: 	'POST',
					url 		: 	makeURL("/mobiledoc/ascWeb/Implants.go/updateVarifyFlag"),
					data		:   {"encId":encId,"patientId":patientId,"flag":flag}
                });
			};
			function getVarifyFlag(encId,patientId){
                return $http({
                	method		: 	'GET',
					url 		: 	makeURL("/mobiledoc/ascWeb/Implants.go/getVarifyFlag/"+encId+"/"+patientId),
                });
			};
		function isUDIExist(udi){
			return $http({
				method		: 	'POST',
				url 		: 	makeURL("/mobiledoc/ascWeb/Implants.go/isUDIExist"),
				data		:   {"udi":udi}
			});
		};
		function isDuplicateUDIWarningSecurityKey(userId){
			return $http({
				method		: 	'POST',
				url 		: 	makeURL("/mobiledoc/ascWeb/Implants.go/isDuplicateUDIWarningShow"),
				data		:   {"userId":userId}
			});
		};
		function isRemindMeUpdate(userId){
			return $http({
				method		: 	'POST',
				url 		: 	makeURL("/mobiledoc/ascWeb/Implants.go/isRemindMeUpdate"),
				data		:   {"userId":userId}
			});
		};
		};
})();

//