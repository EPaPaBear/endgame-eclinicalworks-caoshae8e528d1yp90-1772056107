//Changes done for p2p session validation
function initP2PSessionValidator(formId, iframeId, addListener) {
    try {
      if (addListener && addListener === true) {
        removeP2PSessionValidator()
        window.addEventListener('message', receiveP2PMessage);
      }

      if(formId && iframeId){
        let formElement = $('#'+iframeId).parents().find('#'+formId+':first');
        appendP2pSessionValidationElements(formElement, 'p2pSessionValidationTabId', sessionStorage.getItem("tabId"));
        appendP2pSessionValidationElements(formElement, 'p2pSessionValidationFormId', formId);
        appendP2pSessionValidationElements(formElement, 'p2pSessionValidationIframeId', iframeId);
      }
    } catch (e) {
      console.log('Please use standard form id - jtncontentsignonform');
    }
}

function removeP2PSessionValidator() {
  window.removeEventListener('message', receiveP2PMessage);
}

function receiveP2PMessage(e) {
  var nhxserverprotocol = getItemKeyValue("nhxserverprotocol");
  var nhxliveaccessserver = getItemKeyValue("nhxliveaccessserver");
  var domain = nhxserverprotocol + nhxliveaccessserver;
  if (e.origin === domain || !e.data || e.data.length<=0) {
    return;
  } else {
    try {
      var splCloseModel = JSON.parse(e.data);
      if (splCloseModel["action"] === "validateP2PModel") {
        verifyP2PModelSignature(JSON.parse(e.data));
      } else {
        console.log('Unsupported action received')
      }
    } catch (e) {
      return;
    }
  }
}

function verifyP2PModelSignature(jsonObject) {
  if (jsonObject && jsonObject.payload) {
    try {
      var localTabId = sessionStorage.getItem('tabId');
      var tabIdFromP2P = jsonObject.payload.tabId;
      var p2ptabIdArr = tabIdFromP2P.split('#');
      var userEmrId = jsonObject.payload.useremruid;
      if (!tabIdFromP2P || localTabId !== p2ptabIdArr[0]) {
        ecwAlert("Invalid token. Nothing received.")
      }

      var iframeElement = document.getElementById(p2ptabIdArr[2]);
      iframeElement = (iframeElement.contentWindow) ? iframeElement.contentWindow : (iframeElement.contentDocument.document) ? iframeElement.contentDocument.document
          : iframeElement.contentDocument;

      if (iframeElement) {
        var data = {"action": "validateP2PModel", "payload": {"tabId": localTabId, "useremruid": userEmrId}};
        iframeElement.postMessage(JSON.stringify(data), "*");
      }
    } catch (e) {
      console.error('Exception while validating p2p message.')
    }
  }
}

function appendP2pSessionValidationElements(formElement, elementName, elementValue) {
  let tempHiddenInput = formElement.find("#"+elementName);
  if(tempHiddenInput.length===0){
    let hiddenInput = $('<input/>',{type:'hidden',id:elementName,name:elementName,value:elementValue});
    hiddenInput.appendTo(formElement);
  } else {
    tempHiddenInput.val(elementValue);
  }
}