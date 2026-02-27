/* 
 * To change this license header, choose License Headers in Project Properties.
 * To change this template file, choose Tools | Templates
 * and open the template in the editor.
 */


angular.module('SWSFormModule', ['oc.lazyLoad','ecw.service.EncDetailsService','ecw.dir.dynamicContent','ComponentCleanUp'])
    .controller('SWSFormCtrl', function($scope,$http,$ocLazyLoad, $filter, EncDetailsService,$attrs) {
        $scope.section = "";
        $scope.action = 'showmain';
        $scope.enc = {};
    	 $scope.titleCaption = "";
         $scope.patientId = -1 ;
         $scope.encounterId = -1;

        /*for section next and prev starts*/
        var section2 = 'Assessment';
        var nextLabel = getNextLabel(section2);
        var prevLabel = getPrevLabel(section2);

        $scope.nextLabel = getLabel(nextLabel);
        $scope.prevLabel = getLabel(prevLabel);
        $scope.loadSection = function(type) {
            if (type === "Next")
                $scope.loadProgressNotePopup(getLinkForSection(nextLabel));
            else
                $scope.loadProgressNotePopup(getLinkForSection(prevLabel));
        };
        $scope.loadData = function() {
            try {
            	$scope.patientId = ($attrs.patientid)? $attrs.patientid:"" ;
           	 	$scope.encounterId =($attrs.encounterid)? $attrs.encounterid:"";
           	 	
           	 	if(EncDetailsService.getEncDetailsByEncId($scope.encounterId) === undefined ||  EncDetailsService.getEncDetailsByEncId($scope.encounterId).encounterId !== $scope.encounterId ){
           	 		EncDetailsService.fetchEncDetails($scope.encounterId);
           	 	}
           	 	$scope.enc = EncDetailsService.getEncDetailsByEncId($scope.encounterId);
                $scope.titleCaption = EncDetailsService.getCaption($scope.patientId, $scope.encounterId);
            }
            catch(e){}
        }
        /*for section next and prev ends*/

        // function called when cancel button clicked as a result of dirty Pop up appears on close button
        $scope.cancelOnClose = function() {
            refreshDashboard($scope.encounterId, $scope.patientId, "", "pn-medicalhx");
        };
        
        $scope.saveData = function()
        {
        }
        
        $scope.removeBackdrop = function() {
    		$(".modal-backdrop").css('position','relative');
    	};
    	
    	$scope.closeSpecModal = function (){
    	    try{
                var pnControllerScope = angular.element("#pnController").scope();
                if(pnControllerScope !== null && pnControllerScope !== undefined) {
                    pnControllerScope.checkForCQWUnAnsweredFound();
                }
            }catch(e){}

    		$("#SWSFormModel").modal('hide');
    		$("#SWSFormModel").remove();

    	};
    });

	function getTagValue_sws_pn(xmString, tagName){
		var xmlDoc = $.parseXML(xmString);
        var $xml = $( xmlDoc );
        var $tag = $xml.find( tagName);
        return $tag.text();
	}

		
