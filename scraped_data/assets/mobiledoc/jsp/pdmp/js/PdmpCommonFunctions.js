var closeModal = function() {
    $('body').removeClass('modal-open');
    $('body').find('.modal-backdrop').last().remove();
};

var ecwPdmpAlert = function(msg, title, okCallbBack, btnLbl, theme, elementId, hascloseButton) {

    title = String.prototype.trim.call( title == null ? "" : title );
    btnLbl = String.prototype.trim.call( btnLbl == null ? "" : btnLbl );
    hascloseButton = String.prototype.trim.call( hascloseButton == null ? "" : btnLbl );
    elementId = String.prototype.trim.call( elementId == null ? "" : elementId );
    theme = String.prototype.trim.call( theme == null ? "" : theme );

    if (angular.isUndefined(title) || (title).length == 0) {
        title = "eClinicalWorks";
    }
    if (angular.isUndefined(btnLbl) || (btnLbl).length == 0) {
        btnLbl = "OK";
    }
    if (angular.isUndefined(hascloseButton) || (hascloseButton).length == 0) {
        hascloseButton = true;
    }
    var oMsg = bootbox.dialog({
        message: escapeHtml(msg),
        title: title,
        closeButton: hascloseButton,
        buttons: {
            Yes: {
                label: escapeHtml(btnLbl),
                callback: function() {
                    if (okCallbBack && okCallbBack != "") {
                        setTimeout(okCallbBack, 0);
                        closeModal();
                        return;
                    }
                    if (!angular.isUndefined(elementId) && (elementId).length > 0) {
                        setTimeout(function() {
                            $('#' + elementId).trigger('focus');
                        }, 100);
                    }
                    return;
                }
            }
        }
    });
    setTimeout(function(){
        $(oMsg).find('button[data-bb-handler=Yes]').trigger('focus');
    },500);
    if (!angular.isUndefined(theme) && (theme).length > 0) {
        oMsg.removeClass("bluetheme").addClass(theme);
    }
};

var ecwPdmpConfirm = function(msg, title, yesCallBack, noCallBack, theme,hascloseButton, bHideDefaultBtn, yesLabel, noLabel, className, isConcurMsg) {

    hascloseButton = String.prototype.trim.call( hascloseButton == null ? "" : hascloseButton );
    yesLabel = String.prototype.trim.call( yesLabel == null ? "" : yesLabel );
    noLabel = String.prototype.trim.call( noLabel == null ? "" : noLabel );
    theme = String.prototype.trim.call( theme == null ? "" : theme );

    if (angular.isUndefined(hascloseButton) || (hascloseButton).length == 0) {
        hascloseButton = true;
    }
    if(angular.isUndefined(yesLabel) || (yesLabel).length == 0)
        yesLabel = "Yes";
    if(angular.isUndefined(noLabel) || (noLabel).length == 0)
        noLabel = "No";
    var oMsg = bootbox.dialog({
        message: escapeHtml(msg),
        title: title,
        className:className,
        closeButton:hascloseButton,
        close: "",
        buttons: {
            No: {
                label: escapeHtml(noLabel),
                className: isConcurMsg ? "btn btn-lgreenConcur btn-xs btn-default" : "btn btn-lgrey btn-xs btn-default",
                callback: function() {
                    if (noCallBack && noCallBack != "") {
                        setTimeout(noCallBack, 0);
                    }
                    return;
                }
            },
            Yes: {
                label: escapeHtml(yesLabel),
                className: "btn btn-blue btn-xs",
                callback: function(e) {
                    e.currentTarget.disabled = true;
                    if (yesCallBack && yesCallBack != "") {
                        setTimeout(yesCallBack, 0);
                    }
                    return;
                }
            }
        }
    });
    if (!angular.isUndefined(theme) && (theme).length > 0) {
        oMsg.removeClass("bluetheme").addClass(theme);
    }
    if(!bHideDefaultBtn){
        setTimeout(function(){
            $(oMsg).find('button[data-bb-handler=Yes]').trigger('focus');
        },500);
    }
};

var fnAjaxPdmpSuppressAlert = function(encIdPDMP,userIdPDMP,patientIdPDMP,screenName) {
    $.ajax({
        type: 'POST',
        url: "/mobiledoc/jsp/pdmp/pdmpSuppressAlert.jsp",
        data: ({
            TrUserId: userIdPDMP,
            patientId: patientIdPDMP,
            screenName:screenName
        }),
        success: function () {
        },
        error: function () {
            alert("Error PDMP Alert Suppression");
        }
    });
};


