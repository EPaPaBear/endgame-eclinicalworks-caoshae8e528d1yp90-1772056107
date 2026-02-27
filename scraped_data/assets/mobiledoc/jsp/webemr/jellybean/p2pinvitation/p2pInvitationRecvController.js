angular.module("p2pInvitationRecvApp",[]).factory('p2pInvitationRecvService', function($http) {
    return {       
    	updateP2PInvitation: function(param) {
            try {
                return $http({
                    method: "POST",                    
                    url: makeURL("/mobiledoc/jsp/ereferralemr/requestHandler.jsp"),
                    data: param,
                    headers: {'Content-Type': 'application/x-www-form-urlencoded'}
                });
            } catch (err) {
            }
        },
        setReadFlag: function(param) {
            try {
                return $http({
                    method: "POST",                    
                    url: makeURL("/mobiledoc/jsp/catalog/xml/telenc/setFlag.jsp"),
                    data: param,
                    headers: {'Content-Type': 'application/x-www-form-urlencoded'}
                });
            } catch (err) {
            }
        },
    };
});

angular.module("p2pInvitationReceived", ['oc.lazyLoad','p2pInvitationRecvApp']).controller('p2pInvitationRecvController', function($scope,$timeout,$location,$window,$ocLazyLoad,$templateCache,p2pInvitationRecvService) {
	$scope.providerFullName = $('#providerFullName').val();
	$scope.invitationMsg = $('#msg_invitation').val();
	$scope.communityInvitationMsg = $('#msg_community_invitation').val();
	$scope.invitaionDetails = {};
	$scope.fromProDetails = {};
	$scope.inviterAddress = "";
	
	$scope.initInvitationDetails = function() {
		if(p2pInvitatinRcvd_status == 0){
			var readFlagXml = getReadFlagXML(p2pInvitatinRcvd_invitationId);
			var params = {
				MessageId : p2pInvitatinRcvd_invitationId,
				FormData : readFlagXml,
				p2pInvitation: true
			}
			
			params = $.param(params);
			
			p2pInvitationRecvService.setReadFlag(params).success(function(data) {
				
			});
		}
		
		if(p2pInvitatinRcvd_invitationJson){
			$scope.invitaionDetails = JSON.parse(p2pInvitatinRcvd_invitationJson);
		}
		
		var data = xml2json($scope.invitaionDetails.fromdoctordetails);
		if(!angular.isUndefined(data.InviterDetails)){
			$scope.fromProDetails = data.InviterDetails;
		}
		
		$('#messageArea').html("<b>"+escapeHtml($scope.invitaionDetails.message)+"</b>");
		
		if($scope.fromProDetails.providerAddL1 != '') {
			$scope.inviterAddress = $scope.fromProDetails.providerAddL1;
		}
		if($scope.fromProDetails.providerAddL2 != '') {
			$scope.inviterAddress =$scope.inviterAddress + "," + $scope.fromProDetails.providerAddL2;
		}
		if($scope.fromProDetails.providerCity != '') {
			$scope.inviterAddress = $scope.inviterAddress + "," + $scope.fromProDetails.providerCity;
		}
	};
	
	$scope.updateP2PInvitation = function(p2pInvitatinRcvd_invitationId,msgType,elementId) {
		var params = {
			invitationId : p2pInvitatinRcvd_invitationId,
			type : msgType,
			returntype : 2,
			TrUserId : global.TrUserId
		};
		
		params = $.param(params);
		p2pInvitationRecvService.updateP2PInvitation(params).success(function(data) {
			if(data) {
				if(data.success == "true") {
					if(data.docfound == "true") {
						$scope.closeDiv(elementId,elementId);
					};
				};
			};
        });
	};
	
	$scope.closeDiv = function(elementId,controllerId) {
		$scope.$parent.filterP2PInvitation();
		closeP2PModal(elementId,controllerId);
	};
});

function getReadFlagXML(messageId) {
    var xw = new XMLWriter('ISO-8859-1', '1.0');
    startSoapPacket(xw);
    xw.writeStartElement('return');
    xw.writeAttributeString('xsi:type', 'xsd:string');
    xw.writeStartElement('Status');
    xw.writeAttributeString('xsi:type', 'xsd:string');
    
    addElement(xw, 'MessageId', messageId, 'xsi:type', 'xsd:int');
    addElement(xw, 'MessageStatus', 1, 'xsi:type', 'xsd:int');
    addElement(xw, 'p2pinvitation', 'true', 'xsi:type', 'xsd:string');
    
    xw.writeEndElement();
    xw.writeEndElement();
    endSoapPacket(xw);
    return xw.flush();
}