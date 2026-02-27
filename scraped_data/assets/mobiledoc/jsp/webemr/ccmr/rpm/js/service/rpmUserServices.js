angular.module('rpm.userService',[]).service('rpmUserService', ['$http', '$log', '$q',rpmUserService])
function rpmUserService ($http, $log, $q) {

	var postRequestForRpmData = function(url, requestParams) {
		return $http({
			method: 'POST',
			url: url,
			data: requestParams
		});
	};

	var postRequestForAjaxCall = function(url, requestParams) {
		return $http({
			method: 'POST',
			url: url,
			headers: {'Content-Type': 'application/x-www-form-urlencoded'},
			data: $.param(requestParams)
		});
	};

	var getRequestForRpmData = function(url, requestParams) {
		return $http({
			method: 'GET',
			url: url,
			data: requestParams
		});
	};

	var getClientTime = function() {
		var now = new Date();
		var month = getFormattedValue((now.getMonth()+1));
		var date = getFormattedValue(now.getDate());
		var hours = getFormattedValue(now.getHours());
		var minutes = getFormattedValue(now.getMinutes());
		var seconds = getFormattedValue(now.getSeconds());
		return (now.getFullYear() + "-" + month + "-" + date + " " + hours + ":" + minutes + ":" + seconds);
	};

	var getFormattedValue = function (input) {
		return (input) < 10 ? "0"+(input) : (input);
	}

	return {
		postRequestForRpmData : postRequestForRpmData,
		getRequestForRpmData : getRequestForRpmData,
		postRequestForAjaxCall: postRequestForAjaxCall,
		getClientTime : getClientTime
	}
}
