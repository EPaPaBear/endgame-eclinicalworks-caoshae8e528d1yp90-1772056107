var app = angular.module('ecwWarningAlertDirective',[]);
app.directive('ecwWarningAlertModal', function() {
	return {
		restrict : 'E',
		templateUrl : '/mobiledoc/jsp/webemr/common/ecwWarningAlert.html',
		scope: {
			alertTitle: '@warningtitle',
			alertMsg: '@message',
			colortheme:'@colortheme',
			elementId: '@elementId'
		},
		controller : function ($scope,$element,spellCheckService) {
			$scope.setTheme = function(){
				if($scope.colortheme === 'blue'){
					$scope.alertbgcolor = '#2b91d9';
					$scope.okbutton = 'btn btn-blue';
				}

				if($scope.colortheme === 'red'){
					$scope.alertbgcolor = '#f05a5c';
					$scope.okbutton = 'btn btn-blue';
				}

				let id =  ('#' + $element[0].id);
				$(id+' .modal').show();
			}

			$scope.hidewarningAlert = function(){
				let id =  ('#' + $element[0].id);
				angular.element(id).remove();
				$(id+' .modal').hide();
				if($scope.elementId){
					spellCheckService.hidewarningAlert($scope.elementId);
				}
			}
		}
	}
});
