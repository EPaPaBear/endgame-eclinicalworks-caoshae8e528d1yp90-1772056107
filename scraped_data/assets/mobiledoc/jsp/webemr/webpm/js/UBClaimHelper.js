var sendAsyncReqUB = function(type, url, fromData, callbackFunc, $http) {
	var req = $http({
    	method: type,
    	url: url,        
    	data: fromData,
    	headers: {'Content-Type': 'application/x-www-form-urlencoded'}
    });
	req.success(function(data) {
    	try {    		
			var conjson = convertInJSON(data);
			var value = conjson.Envelope.Body['return'];
			callbackFunc(value);
		} catch (e) {
	    	callbackFunc(undefined);
		}
	});
};
var sendAsyncReqAndGetXMLUB = function(type, url, fromData, callbackFunc, $http) {
	var req = $http({
    	method: type,
    	url: url,        
    	data: fromData,
    	headers: {'Content-Type': 'application/x-www-form-urlencoded'}
    });
	req.success(function(data) {
    	try {    		
			callbackFunc(data);
		} catch (e) {
	    	callbackFunc(undefined);
		}
	});
};
var sendAsyncReqAndGetHTMLUB = function(type, url, fromData, callbackFunc, $http) {
	var req = $http({
    	method: type,
    	url: url, 
    	dataType:"text/html",
    	data: fromData,
    	headers: {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'}
    });
	req.success(function(data) {
    	try {    		
			callbackFunc(data);
		} catch (e) {
	    	callbackFunc(undefined);
		}
	});
};
var sendAsyncReqNRetUB = function(type, url, fromData) {
    var obj;
    $.ajax({
        type: type,
        url: url,
        async: false,
        data: fromData,
        headers: {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"},
        success: function(data) {
            try {
                var conjson = convertInJSON(data);
                var value = conjson.Envelope.Body['return'];
                obj = value;
            } catch (e) {
                obj = undefined;
            }
        }
    });
    return obj;
};
var sendAsyncReqNRetHTMLUB = function(type, url, fromData) {
    var obj;
    $.ajax({
        type: type,
        url: url,
        async: false,
        data: fromData,
        headers: {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"},
        success: function(data) {
            try {
                obj = data;
            } catch (e) {
                obj = undefined;
            }
        }
    });
    return obj;
};
var GetInsSeqStringFromNumberUB = function(nSeqNo) {
    var insSeqStringFromNumber = "";
    if (nSeqNo == 1) {
        insSeqStringFromNumber = "P";
    } else if (nSeqNo == 2) {
        insSeqStringFromNumber = "S";
    } else if (nSeqNo == 3) {
        insSeqStringFromNumber = "T";
    } else {
        insSeqStringFromNumber = "";
    }
    return insSeqStringFromNumber;
};
function getICDLookupXmlUB(ICDCode, serviceDate) {
    var xw = new XMLWriter('ISO-8859-1', '1.0');
    startSoapPacket(xw);
    	xw.writeStartElement('lookup');
    	xw.writeAttributeString('xsi:type', 'xsd:string');
    		addElement(xw, 'searchBy', 'code', 'xsi:type', 'xsd:string');
    		addElement(xw, 'code', ICDCode + '', 'xsi:type', 'xsd:string');
	    	addElement(xw, 'ShowCodes', 1 + '', 'xsi:type', 'xsd:string');
    		addElement(xw, 'counter', 1 + '', 'xsi:type', 'xsd:int');
			addElement(xw, 'maxcount', 1 + '', 'xsi:type', 'xsd:int');
    		addElement(xw, 'keyName', 'Assessments', 'xsi:type', 'xsd:string');
            addElement(xw, 'ValidDate', serviceDate, 'xsi:type', 'xsd:string');
    	xw.writeEndElement();
    endSoapPacket(xw);
    return xw.flush();
}
//function maskIt() {
//    $('.dateTd').inputmask("99/99/9999");
//}
var setVoidClaimInfo = function(voidClaim) {
    var strMsg = " ";
    var strVoidToClaimId = $.trim(voidClaim.VoidToClaimId);
    var strCopyToClaimId = $.trim(voidClaim.CopyToClaimId);
    var strVoidFromClaimId = $.trim(voidClaim.VoidFromClaimId);
    var strCopyFromClaimId = $.trim(voidClaim.CopyFromClaimId);

    var msgVoidToAndCopiedTo = "";
    if (strVoidToClaimId !== "-1" && strCopyToClaimId !== "-1") {
        msgVoidToAndCopiedTo = " <Voided To: " + strVoidToClaimId + ", Copied To: " + strCopyToClaimId + ">";
    }

    var msgVoidFromOrCopiedFrom = "";
    if (strVoidFromClaimId !== "-1") {
        msgVoidFromOrCopiedFrom = " <Voided From: " + strVoidFromClaimId + ">";
    } else if (strCopyFromClaimId !== "-1") {
        msgVoidFromOrCopiedFrom = " <Copied From: " + strCopyFromClaimId + ">";
    }
    if (msgVoidToAndCopiedTo !== "") {
        strMsg = strMsg + msgVoidToAndCopiedTo;
    }
    if (msgVoidFromOrCopiedFrom !== "") {
        strMsg = strMsg + msgVoidFromOrCopiedFrom;
    }
    return strMsg;
};