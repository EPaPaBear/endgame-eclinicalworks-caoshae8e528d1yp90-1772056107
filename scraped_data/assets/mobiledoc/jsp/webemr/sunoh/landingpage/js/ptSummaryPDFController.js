angular.module('ptSummaryPDFModule', []).controller('ptSummaryPDFController',function ($scope, $timeout, SunohService) {

    var printPreviewTimout, iframeReadyTimeout, styleElement;

    $scope.init = function () {
        $scope.ptSummaryJSON = SunohService.ptSummaryJSON;
        $scope.originalDocTitle = document.title;
        $scope.footerDateTime =sunohGlobal.formatDateWithLocalizedMonth({"date":moment().locale('en').format("MM/DD/YYYY hh:mm A"),"format":"MM/DD/YYYY hh:mm A","toFormat":"DD-MMM-YYYY hh:mm A"}) + ' ' + clientTimeZone();
        $scope.setFacilityDetails();
        var isIpad = window.navigator.userAgent.indexOf("iPad");
        printPreviewTimout = $timeout(function () {
            if(isIpad !== -1)
                printDiv();
            else
                $scope.printPreview();
        });
    }

    $scope.setFacilityDetails = function() {
        let facilityJSON = JSON.parse(getCachedData("/mobiledoc/sunoh/userProfile/facilityDisplayData", "SUNOH_SA_FACILITY"));
        if (!facilityJSON.isDefaultLogo) {
            $scope.logoSrc = facilityJSON.facilityLogo;
        }
        $scope.facilityHeading = facilityJSON.facilityHeading;
    }

    $scope.printPreview = function() {
        let windowContent = "";
        windowContent += $('#sunohPreviewContent').html();
        $('<iframe id="sunohPrintSummaryFrame" style="display: none" name="sunohPrintSummaryFrame">').appendTo('body');
        var doc = $("#sunohPrintSummaryFrame")[0].contentWindow.document;
        doc.open();
        doc.write(windowContent);
        doc.close();
        onReadyState2(false);
    }

    function onReadyState2() {
        try {
            var timeOut;
            iframeReadyTimeout = $timeout(function () {
                if ($('#sunohPrintSummaryFrame').contents().find("body").html()) {
                    timeOut = 0;
                    var originalTitle = document.title;
                    var sunohPrintFrame = window.frames["sunohPrintSummaryFrame"];
                    sunohPrintFrame.addEventListener("beforeprint", (event) => {
                        document.title=$scope.ptSummaryJSON.fileName;
                    });
                    sunohPrintFrame.addEventListener("afterprint", (event) => {
                        document.title=originalTitle;
                    });

                    sunohPrintFrame.focus();
                    sunohPrintFrame.print();
                } else {
                    timeOut++;
                    if (timeOut > 150) {
                        timeOut = 0;
                        ecwAlert("Could not load the requested page, try again!","Sunoh");
                        return false;
                    }
                    onReadyState2();
                }
            }, 200);
        }
        catch (e) {
        }
    }

    function printDiv() {
        $("#sunohPreviewContent").detach().appendTo('body');
        appendStyle();
        const checkContentReady = setInterval(function() {
            const content =$("body > #sunohPreviewContent #ptSummaryPreviewTable").length
            if (content > 0) {
                clearInterval(checkContentReady);
                window.addEventListener("afterprint", afterPrintCallback);
                window.addEventListener("beforeprint", beforePrintCallback);
                window.print();
            }
        }, 100);
    }

    function appendStyle() {
        let styles = `@media print {
            body {
                visibility: hidden;
                overflow: unset !important;
                margin: 10mm;
            }
        }`;
        styleElement = document.createElement('style');
        styleElement.type = 'text/css';
        styleElement.appendChild(document.createTextNode(styles));

        document.head.appendChild(styleElement);
    }

    function beforePrintCallback() {
        document.title=$scope.ptSummaryJSON.fileName;
    }

    function afterPrintCallback() {
        $("#sunohPreviewContent").remove();
        document.title=$scope.originalDocTitle;
        if (styleElement)
            document.head.removeChild(styleElement);
    }

    $scope.toCamelCase = function(str) {
        let lcStr = str.toLowerCase();
        return lcStr.replace(/(?:^|\s)\w/g, function (match) {
            return match.toUpperCase();
        });
    }

    $scope.$on("$destroy", function () {
        $timeout.cancel(printPreviewTimout);
        $timeout.cancel(iframeReadyTimeout);
        window.removeEventListener("afterprint", afterPrintCallback);
        window.removeEventListener("beforeprint", beforePrintCallback);
        $("#sunohPrintSummaryFrame").remove();
    });
});
