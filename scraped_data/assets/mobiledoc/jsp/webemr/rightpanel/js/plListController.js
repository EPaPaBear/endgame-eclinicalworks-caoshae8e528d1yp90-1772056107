angular.module('problemlist',['oc.lazyLoad','ecw.dir.datepicker','ecw.dir.AsmtNotesTpl','ecw.dir.keywords','ecw.pagination','ui.sortable','ecw.service.EncDetailsService','ecw.datatruncUtilityModule','assessmentImportModule'])
	.controller('problemListController', function($scope, $http , $timeout,  $modal, $modalInstance, $ocLazyLoad) {

		$scope.pflag = 0;
		$scope.init = function () {
			//$("#problemListMainModal").parents(".modal").css("overflow","hidden");
			//$("#problemListMainModal").modal('show');
			$scope.popupMainPl = "";
			$scope.ptid = problemList_pid;
			$scope.encId = problemList_encId;
			$scope.TrUsrId = problemList_TrUsrId;
			$scope.callFrom = problemList_callFrom;
			$scope.context = problemList_context;
			$("#problemListMainModal").parent().parent().css({'width': '1500px'});
			$ocLazyLoad.load({
				name: 'problemlist2',
				files: ['/mobiledoc/jsp/webemr/js/vendor/jscrollpane.js',
					'/mobiledoc/jsp/webemr/progressnotes/billing/assessmentNotes-tpl.js',
					'/mobiledoc/jsp/resources/jslib/angular-ui-bootstrap/dist/ui-bootstrap-tpls.js',
					'/mobiledoc/jsp/webemr/progressnotes/assessment/assessment-import-module.js',
					'/mobiledoc/jsp/webemr/rightpanel/js/plListControllerFLT.js'
				],
				cache: false
			}).then(function() {
				$scope.popupMainPl = makeURL("/mobiledoc/jsp/webemr/rightpanel/problemListFlt.jsp?pid=" +$scope.ptid+ "&encId="+$scope.encId+"&callFrom="+$scope.callFrom+"&context="+$scope.context+"&TrUserId="+$scope.TrUsrId+"&isMainPl=true");
			}, function(e) {
			});
		};

		$scope.closeMod = function () {
			//$("#problemListMainModal").modal('hide');
			$modalInstance.dismiss();
			$('.modal-backdrop').remove();
		};

		$scope.closeModValue = function (val) {
			//$("#problemListMainModal").modal('hide');
			$modalInstance.close(val);
			$('.modal-backdrop').remove();
		};

		$scope.promptChangesMain = function() {
			$("#problemListBtn8").click();
		};
	});
