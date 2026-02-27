/**
 * @author amang
 * 
 * This file defines AUC directive which places a button on screen.
 * It has following attributes:
 * 
 * 		1. encounterId: Encounter id.
 * 		2. patientId: patientId
 *		3. buttonClass: CSS class to be applied on button
 *		4. autoAucMode: Pass 1 to automatically perform AUC viz. AUC button will be hidden and AUC will be triggered automatically on event defined by user 
 *		   For ex - User can decide to perform AUC automatically when close icon is clicked to close modal and save data in Manage Orders screen.
 *		   Default value for this parameter is 0.		   
 *		5. handle: As name defines it's handle to directive user can use this object to call function(s) defined inside directive.
 *		   User can pass an empty/undefined object here and it will be defined inside directive with a function openAUCConsultModal(). 
 *		   User can call this function on a flow where he decides AUC to be performed. 
 *  
 */
(function(){
	angular.module('pama', ['ui.bootstrap', 'oc.lazyLoad'])
	.config(['$ocLazyLoadProvider', configureLazyLoad]).run(['$ocLazyLoad', lazyLoader])
	.directive('auc', [aucDirective]);
	
	function aucDirective(){
		return{
			restrict: 'AE',
			template: '<button id="aucButtonDirective" class={{aucDirCtrl.buttonClass}} ng-click="aucDirCtrl.openAUCConsultModal()" ng-if="!aucDirCtrl.isAucFeatureDisabled" ng-hide="aucDirCtrl.isAutoModeOn" ng-disabled="aucDirCtrl.disableAucButton">Perform AUC</button>',
			scope:{
				encounterId: "@",
				patientId: "@",
				context: "@",
				buttonClass: "@",
				autoAucMode: "@",
				callback: "&?",
				disableAucButton:"=?", 
				handle: '=?'
			},
			controller: 'aucDirectiveController',
			controllerAs: 'aucDirCtrl',
			cache: false,
			bindToController: true,
			link: function(scope, elem, attrs){
				
			}
		}
	}
	
	function configureLazyLoad($ocLazyLoadProvider){
		$ocLazyLoadProvider.config({
			modules: [
				{
					name: 'pama',
					files: getDependencies('pama')
				}
			]
		});
	}
	
	function lazyLoader($ocLazyLoad){
		$ocLazyLoad.load(getDependencies('pama'));
	}
})();
