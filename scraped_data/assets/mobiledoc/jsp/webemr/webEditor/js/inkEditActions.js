var strContext = '';
var patientId = "";
var encId = '';
angular.module('webEditorModule', ['ecw.dir.savePrompt'])
.controller('emrEditorViewController', function ($scope, $http, $window, $timeout)
	{
		
		strContext = context;
		patientId = patientId;
		encId = encounterId;
		var webInking_lockObj = {formName: "", uniqueKey: "", g_cancel: false, strKey: "", isOpenform: false};
		var isConcurrencyRequired = false;
		$scope.patientId = patientId;
		$scope.context = context;
		var viewerElement = document.getElementById('tronViewer');
		var myWebViewer = null;
		var signX=0;
		var signY=0;
        $scope.initTronViewer = function(){

			if(global_webInking.documentId && global_webInking.documentId !== '') {
				isConcurrencyRequired = true;
			}

			if(StreamOn == "yes")
			{
				myWebViewer = new PDFTron.WebViewer({
					path : "/mobiledoc/jsp/webemr/webEditor/lib",
					type : "html5",
					enableAnnotations : true,
					saveAnnotations: true,
					html5Path: "html5-min/ReaderControl.jsp",
					html5MobilePath: "html5-min/ReaderControl.jsp",
					custom : JSON.stringify({
						data : [ fileName, filePath, fileExt, StreamOn, csrfToken, "", "", "", "", "", "", "", eyeExamData,"",global.TrUserName, null, "emrEditorViewController"]
					}),
					initialDoc : "/mobiledoc/jsp/webemr/webEditor/getFileData.jsp?fileName=" +fileName +"&filePath=" + filePath + "&fileExt=" + fileExt,
					streaming: true
					}, viewerElement);
			}
			else
			{
			var pdfModeParameter = {}
            if(loadPath && loadPath.endsWith(".pdf")){
                pdfModeParameter = {
                    ui: 'legacy',
                    l: atob("ZUNsaW5pY2FsV29ya3MgTExDIChlY2xpbmljYWx3b3Jrcy5jb20pOk9FTTplQ2xpbmljYWxXb3JrcywgaGVhbG93OjpCKzpBTVMoMjAyMzA4MzApOjZBQTVEQUVEMDQ3Nzc4MEFGMzYwQjEzQUM5ODIwMjc4NjA2MTBGRkQ5NzQ4N0U5QTBFRkYyQkY0MTg2NDEwRkU3QTQxMzVGNUM3")
                };
            }
				myWebViewer = new PDFTron.WebViewer(Object.assign({
					path: "/mobiledoc/jsp/webemr/webEditor/lib",
					type: "html5",
					enableAnnotations: true,
					saveAnnotations: true,
					html5Path: "html5-min/ReaderControl.jsp",
					html5MobilePath: "html5-min/ReaderControl.jsp",
					custom: JSON.stringify({
	//					data: [fileName, filePath, fileExt, StreamOn, csrfToken]
						data: [fileName, filePath, fileExt, StreamOn, csrfToken, signX, signY, localFileName,isThumbnailCreation, "", "", "", eyeExamData,"",global.TrUserName, null, "emrEditorViewController"]
					}),
					initialDoc: loadPath
				},pdfModeParameter), viewerElement);
			}
			$(myWebViewer.element).bind("documentLoaded",function(){
				if($scope.isFromReloadViewer){
					$scope.isFromReloadViewer = false;
					return;
				}
				$scope.hideShowToolButton("block");

				if(hideAnnotationsTools === true || hideAnnotations.toUpperCase() === 'YES' || isHideTools.toUpperCase() === 'YES')
				{
					canEditDocument = false;
					myWebViewer.getInstance().setAnnotationbarVisibility(false);
				}
			})

        };
		$scope.generatePDFTronCustomData = function(){
			return [fileName, filePath, fileExt, StreamOn, csrfToken, "", "", "", "", "", "", "", eyeExamData,"",global.TrUserName, null, "emrEditorViewController"]
		}
		$scope.deleteDeboundTimeout = null;
		$scope.reloadAfterDeletePage = function () {
			if($scope.deleteDeboundTimeout==null){
				$scope.deleteDeboundTimeout = $timeout(function(){
					clearTimeout($scope.deleteDeboundTimeout);
					$scope.deleteDeboundTimeout=null;
					$scope.reloadViewer();
				},1000)
			}
		}
		$scope.reloadViewer = function(){
			$scope.isFromReloadViewer = true;
			myWebViewer.getInstance().loadDocument(loadPath,{customHeaders: {"X-XSS-Protection": "0; mode=block"},documentId : new Date().getTime(),custom: JSON.stringify($scope.generatePDFTronCustomData())});
		}
		$scope.reloadASCProgressNote = function(){
			let elem=document.getElementById('calLoadingInking');
			angular.element(elem).scope().refreshProgressNoteView();
		}
		$scope.initTronViewer();
		$("#emrInkReferal").modal();
		$scope.changeCloseFlag = false;
		
		$scope.closeWithoutSave = function(){
			$('#emrInkReferal').modal('hide');
			$('#emrInkReferal .det-view').remove();
			removeModalBackDrop();
	        $scope.closeInking();
	        $scope.removeFolderCreated('no');
			if(isConcurrencyRequired && webInking_lockObj && webInking_lockObj.uniqueKey){
				releaseFormLock(webInking_lockObj);
			}
		};
		
		$scope.closeAfterSave = function(){
			if(isConcurrencyRequired && isConcurrencyOccurredInDocument(webInking_lockObj, false)){
				if($scope.context === 'ASC'){
					showIPMessage("Other user has changed data when you were working.\nFor patient data consistency this screen was closed.", "inputelm1","AlertMsg");
					$scope.closeWithoutSave();
					return;
				}else{
					return;
				}
			}
            myWebViewer.getInstance().saveAnnotations().then(function(){
            	 $scope.closeAfterSave2();
    	},function(err){
    	})                        
		};
		var removeModalBackDrop = function(){
			if(strContext !== "vascular"){
				$('.modal-backdrop.fade').remove();
			}
		};
		$scope.closeAfterSave2 = function(){
			/*if(strContext.toUpperCase() == 'ECFORMSHORTCUTS')
	        {
	        	eCliniformSaveToPatient(patientId, fileName, filePath, docType, encId, refID, context);
	        }*/
			
        	$('#emrInkReferal').modal('hide');
			$('#emrInkReferal .det-view').remove();
			removeModalBackDrop();
	        if(isThumbnailCreation == 'true')
	        {
                
	        	if(strContext.toUpperCase() === 'DERM') {
					dermContainerRefreshStoredImages(encId, patientId);
                }else if($scope.context === 'ASC'){
                    $scope.reloadASCProgressNote();
                }else{
                	refreshDashboard(encId, patientId, "progressNote", "");	                	
                }	        	
            }else{
                $scope.closeInking();
            }
	        $scope.removeFolderCreated('no');
			if(isConcurrencyRequired && webInking_lockObj && webInking_lockObj.uniqueKey){
				releaseFormLock(webInking_lockObj);
			}
		};
		
		$scope.setDirtyFlag = function(){
            $scope.changeCloseFlag = true;
            $scope.$digest();
		};
		
		$scope.revertDirtyFlag = function()
		{
			$scope.changeCloseFlag = false;
            $scope.$digest();
		};
		$scope.print = function(){
			var temps1 = document.getElementById('tronViewer').childNodes[0];
            var intervalId = setInterval(function() {
                    $scope.flatteringLetter();
                    clearInterval(intervalId);
                    var intervalId1 = setInterval(function() {
                        var temps1 = document.getElementById('tronViewer').childNodes[0];
                        var button = temps1.contentDocument.getElementById("printButton");
                        if (button != null && button.length !== 0) {
                            temps1.contentDocument.getElementById("printPageNumbers").value="";
                            $('.ui-dialog-buttonset').first().click();
                            temps1.contentDocument.getElementById("printButton").click();
                            temps1 = document.getElementById('tronViewer').childNodes[0];
                            try {
                                temps1.contentDocument.getElementById("printPageNumbers").value="";
                                temps1.contentDocument.getElementsByClassName("ui-dialog-buttonset")[0].firstChild.click();
                                clearInterval(intervalId1);
                            } catch (e) {
                                console.log(e);
                            }
                        } else {
                            console.log("looking for button...");
                        }
                    }, 1000);
            }, 100);
		};
		$scope.flatteringLetter = function(){
			var returnData = {};
			var param = {sRequestFrom :"ImmunizationForms",
					sRequestType:'flattenpdffile',
					fileName:fileName,
					filePath:xodStr
			};
			param = $.param(param);
		    var url = '/mobiledoc/jsp/webemr/labs/LabsRequestHandler.jsp?';
		    url = makeURL(url);
		    $.ajax({
		        url: url,
		        type: "POST",
		        data:param,
		        cache: false,
		        async: false,
		        dataType: "json",
		        headers: {'Content-Type': 'application/x-www-form-urlencoded'},
		        success: function(data) {  
		        	returnData = data;
		        }
				 }); 
			$scope.initTronViewer();
		};

		$scope.acquireDocumentLock = function(){
			if(isConcurrencyRequired) {
				webInking_lockObj = {formName: "PatientDocument", uniqueKey: (global_webInking.isDocumentIdHashed === 'true' ?  "HashId_patientdocument_" + global_webInking.documentId : "patientdocument_" + global_webInking.documentId), g_cancel: false, strKey: "", isOpenform: false};
				var acquireFormLockCallBack = function () {
					if (webInking_lockObj.g_cancel) {
						$scope.closeWithoutSave();
						return;
					}
				}
				acquireFormLock(webInking_lockObj, acquireFormLockCallBack);
			}
		};

		$scope.isConcurrencyOccurred = function(){
			if(isConcurrencyRequired) {
				var status = isConcurrencyOccurredInDocument(webInking_lockObj, false);
				if(status && $scope.context === 'ASC'){
					showIPMessage("Other user has changed data when you were working.\nFor patient data consistency this screen was closed.", "inputelm1","AlertMsg");
					$scope.closeWithoutSave();
				}
				return status;
			}
			else {
				return true;
			}
		};

		$scope.retainElementsStyle = [{elementid:"saveAnnotationsButton",style:{display:"none"}}, {elementid:"deletePageButton",style:{display:"none"}}, {elementid:"toolList",style:{display:"none"}}, {elementid:"stampButton",style:{display:"none"}}];
		$scope.hideShowToolButton = function(displayProperty) {
			var pdfElements = $('#tronViewer').children()[0];
			var element = pdfElements.contentDocument.getElementById("editAnnotationsButton")
			if (element) {
				if(isHideTools.toUpperCase() === 'YES'){
					element.style.display = 'none';
				}else{
					element.style.display = displayProperty;
				}
				$scope.retainElementsStyle.forEach(node => {
					for(var key in node.style) {
						var value = pdfElements.contentDocument.getElementById(node.elementid).style[key];
						pdfElements.contentDocument.getElementById(node.elementid).style[key] = node.style[key];
						node.style[key] = value;
					}
				});
			}
		}
		$scope.isPrintHandleByPlugin = function () {
			return global_webInking.printHandler==='true';
		}
	});

function changeCloseIcon()
{
	var elem=document.getElementById('emrEditorViewControllerID');
    angular.element(elem).scope().setDirtyFlag();
}
function reloadDocAfterDelete(name, path){
	var elem=document.getElementById('emrEditorViewControllerID');
    angular.element(elem).scope().reloadAfterDeletePage();
}

function revertDirtyFlag(){
	if(strContext.toUpperCase() === 'ECFORMSHORTCUTS' || strContext.toUpperCase() === 'ASC' || strContext.toUpperCase() === 'DERM')
    {
    	eCliniformSaveToPatient(patientId, fileName, filePath, docType, encId, refID, context);
    	/*$('#emrInkReferal').modal('hide');
    	$('#emrInkReferal .det-view').remove();
        $('.modal-backdrop.fade').remove();*/
        strContext = '';
    }
	else
	{
		var elem=document.getElementById('emrEditorViewControllerID');
	    angular.element(elem).scope().revertDirtyFlag();
	}
}

function setHeight()
{
//	$("#DocumentViewer").jScrollPane({autoReinitialise: true});
	var heightValue = parent.document.body.clientHeight;
//	alert("Set height webedit" +heightValue);
	$("#tronViewer").css({'height':heightValue});
}

function addToLog(fName, action)
{
//	console.log("Add to log");
	$.ajax({
		url: makeURL("/mobiledoc/jsp/webemr/webEditor/addToLogAction.jsp"),
		type: "POST",
		data: "FileName=" + fName + "&action="+action,
 		async: false,
		success: function(data){}
	});
}
function eCliniformSavePatient(){}
function eCliniformSaveToPatient(patientId, fileName, ftpPath, docType, encounterId, refId, strContext)
{
	var flagWebEnabled = 1;
	if(undefined != patientId && patientId.length > 0 && patientId != 0)
	{
		if(undefined == docType || docType.length <= 0)
		{
			if(strContext.toUpperCase() == 'PROGRESSNOTES')
		    {
		    	docType = 2;
		    }
		    else if(strContext.toUpperCase() == 'HUB')
		    {
		    	docType = 4;
		    }
		    else if(strContext.toUpperCase() == 'PATIENTDOCS')
		    {
		    	docType = 4;
		    }
		    else if(strContext.toUpperCase() == 'LEFTMENUECLINIFORM')
		    {
		    	docType = 4;
		    }
		    else
		    {
		    	docType = 4;
		    }
		}
		
		if(encounterId.length == 0 || encounterId == 'null')
		{
			encounterId = 0;
		}
		
		if(refId == 'null' || refId.length == 0)
		{
			refId = 0;
		}
		
	    var result = false;
	    
	    if(fileName.length > 0 && null != fileName)
	    {
	    	if(ftpPath.length <= 0 || ftpPath == "mobiledoc")
	    	{
	    		ftpPath = getFtpDirPath(patientId);
	    	}
			var tempFileName = fileName;
			var lastIndx = tempFileName.lastIndexOf(".");
			tempFileName = tempFileName.substring(0, lastIndx);
	    	if(window.top.webEditorPNImageGlobal){
	    		if(window.top.webEditorPNImageGlobal.customName){
					tempFileName = window.top.webEditorPNImageGlobal.customName;
				}
			}
	    	var xw = new XMLWriter();
	        startSoapPacket(xw);
	        xw.writeStartElement('Document');
	        addElement(xw, 'PatientId', patientId, 'xsi:type', 'xsd:string');
	        addElement(xw, 'FileName', fileName, 'xsi:type', 'xsd:string');
	        addElement(xw, 'catid', docType, 'xsi:type', 'xsd:string');

	        addElement(xw, 'CustomName', tempFileName, 'xsi:type', 'xsd:string');
	        addElement(xw, 'ScannedDate', getCurrentDate(), 'xsi:type', 'xsd:string');
	        addElement(xw, 'ScannedBy', global.TrUserName, 'xsi:type', 'xsd:string');
	        addElement(xw, 'Description', '', 'xsi:type', 'xsd:string');
	        addElement(xw, 'Review', '0', 'xsi:type', 'xsd:string');
	        addElement(xw, 'ReviewerId', global.TrUserId, 'xsi:type', 'xsd:string');
	        addElement(xw, 'ReviewerName', global.TrUserName, 'xsi:type', 'xsd:string');
	        addElement(xw, 'Priority', '0', 'xsi:type', 'xsd:string');
	        addElement(xw, 'encId', encounterId, 'xsi:type', 'xsd:string');
	        addElement(xw, 'refID', refId, 'xsi:type', 'xsd:string');
	        addElement(xw, 'AttachTo', '0', 'xsi:type', 'xsd:string');
	        addElement(xw, 'DocAndLabReview', '0', 'xsi:type', 'xsd:string');
	        addElement(xw, 'PublishToeHX', '0', 'xsi:type', 'xsd:string');
	        addElement(xw, 'FacilityId', '0', 'xsi:type', 'xsd:string');
	        addElement(xw, 'DirPath', ftpPath, 'xsi:type', 'xsd:string');
	        addElement(xw, 'FtpServer', '', 'xsi:type', 'xsd:string');
	        addElement(xw, 'Tags', '', 'xsi:type', 'xsd:string');
	        addElement(xw, 'PublishEcliniFormToPortal', flagWebEnabled, 'xsi:type', 'xsd:string');
	        xw.writeEndElement();
	        endSoapPacket(xw);
	        var xmlData = xw.flush();
	        
	        $.ajax({
	            url: "/mobiledoc/jsp/catalog/xml/patientdocs/getDocs.jsp",
	            type: "POST",
	            data: "nd=" + new Date().getTime() + "&nact=2&flag=1&PatientId=" + patientId + "&FormData=" + xmlData + "&docType=" + docType,
	            async: false,
	            success: function (data) 
	            {
	            	data = data.trim();
					result = true;
					
					var elem=document.getElementById('emrEditorViewControllerID');
				    angular.element(elem).scope().closeAfterSave2();
					window.top.webEditorPNImageGlobal = {};
	            }
	        });
	    }
	}
	
    return result;
}

function getCurrentDate() {
    var date = new Date();
    var dd = date.getDate();
    var mm = date.getMonth() + 1;
    var yyyy = date.getFullYear();

    var currentDate = yyyy + "-" + mm + "-" + dd;
    return currentDate;
}