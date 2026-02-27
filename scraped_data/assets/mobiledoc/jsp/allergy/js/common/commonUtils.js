/* 
 * For Allergy Module common JS functions
 */

function IsParamMissingMatchStr(param, matchStr) {
	if (param !== undefined && param !== null && param.toLowerCase() === matchStr){
		return false;
	}else{
		return true;
	}
}

function getWarningPopupMessageDetails(errorTitle, errorMessage, concurrencyAlertType){
	let warningPopupMessageDetail = {};
	warningPopupMessageDetail.title = errorTitle;
	warningPopupMessageDetail.type = concurrencyAlertType.WARNING;
	warningPopupMessageDetail.beforeList = errorMessage;
	warningPopupMessageDetail.afterList = "";
	warningPopupMessageDetail.closeMsg = "";
	warningPopupMessageDetail.messageIconType = concurrencyAlertType.WARNING;
	return warningPopupMessageDetail;
}

function checkDuplicateWithType(obj, objMatch, type, index){
	let duplicateFound = false;
	switch (type) {
		case 'bottle':
			$.each(obj,function(k,v){
				if (v.bottle_id !== objMatch.bottle_id && v.bottle_name.toUpperCase() === objMatch.bottle_name.toUpperCase()){
					duplicateFound = true;
					return false;
				}
			});
			break;
		case 'templateIdName':
			$.each(obj,function(k,v){
				if (v.ID !== objMatch.ID && v.TEMPLATE_NAME.toUpperCase() === objMatch.TEMPLATE_NAME.toUpperCase()){
					duplicateFound = true;
					return false;
				}
			});
			break;
		case 'templateName':
			$.each(obj,function(k,v){
				if (v.TEMPLATE_NAME.toUpperCase() === objMatch.toUpperCase()){
					duplicateFound = true;
					return false;
				}
			});
			break;
		case 'bottleName':
			$.each(obj,function(k,v){
				if (v.BOTTLE_NAME.toUpperCase() === objMatch.toUpperCase()){
					duplicateFound = true;
					return false;
				}
			});
			break;
		case 'concentrationName':
			$.each(obj,function(k,v){
				if (k !== index && validateAndChangeToUpperCase(v.CONCENTRATION_NAME) === validateAndChangeToUpperCase(objMatch)){
					duplicateFound = true;
					return false;
				}
			});
			break;
		case 'concObjName':
			$.each(obj,function(k,v){
				if (!checkIsNullEmptyUndefined(v.conObj) && k !== index && validateAndChangeToUpperCase(v.conObj.NAME) === validateAndChangeToUpperCase(objMatch.NAME)){
					duplicateFound = true;
					return false;
				}
			});
			break;
		default:
			duplicateFound = false;
	}
	return duplicateFound;
}

function validateAndChangeToUpperCase(param){
	let rtnVal = "";
	if (!checkIsNullEmptyUndefined(param)){
		rtnVal = param.toUpperCase();
	}
	return rtnVal;
}
function checkForRepetition(obj,matchColName){
	var hasDuplicate = function hasDuplicate(arrayObj, colName) {
		var hash = Object.create(null);
		return arrayObj.some(function (arr) {
			return arr[colName] && (hash[arr[colName]] || !(hash[arr[colName]] = true));
		});
	};
	return hasDuplicate(obj, matchColName);

};
function checkIsNullEmptyUndefined(param){
	let rtnVal = false;
	if (param === undefined || param === null || param === ""){
		rtnVal = true;
	}
	return rtnVal;
};

function openModalInstance($modal,tplUrl, ctrl, requestParam, className)
{
	var windowClass =  'w1300 bluetheme '+className;
	return $modal.open({
		templateUrl      : tplUrl,
		controller       : ctrl,
		animation        : true,
		bindToController : true,
		backdrop         : "static",
		keyboard         : true,
		cache            : false,
		size             :'lg',
		windowClass      : windowClass,
		resolve          : requestParam || {}
	});
}

function setCancelBubbleAllergy(event, mainDivId){
	if(!event.target.hasAttribute("data-toggle") && event.target.getAttribute("data-toggle") !== "dropdown" && !$(event.target).hasClass("clearable")){
		event.cancelBubble = true;

		let dropDowns = $("#"+mainDivId).find("[data-toggle='dropdown']");
		$.each(dropDowns,function(k,v){
			if($(v.parentElement).hasClass("open")){
				$(v.parentElement).removeClass("open")
			}
		});
	}
}

function digitWithMaxLength(event, element, maxLength){
	let keyCode = event.charCode ? event.charCode : event.keyCode;
	if(keyCode < 48 || keyCode > 57) {
		return false;
	}
	if($(element).val().length >= maxLength){
		return false;
	}
	return true;
}

function trimValue(value){
	return String.prototype.trim.call( value === null || value === undefined ? "" : value );
}

function callSecurityAccessApi(modalName,key){
	return requestAccess_showRequestPermissionPopup(modalName,key);
}