import { Config, monitorScreenForChanges, unmonitorScreenForChanges } from "./screen-utils.js";
import { MutationObserverUtils } from "../utils/mutationObserverUtils.js";

export class IframeManager {

    mutationConfig = {
        childList: true,
        subtree: true,
        characterData: false
    };

    constructor(document, domUtils) {
        this.document = document;
        this.domUtils = domUtils;
    }

    init() {
        this.setupIframeLoadListeners();
    }

    setupIframeLoadListeners() {
        new MutationObserver((mutations) => this.monitorChanges(mutations)).observe(this.document, this.mutationConfig);
    }

    monitorChanges(records) {
        setTimeout((mutationItems) => {
            if (mutationItems.length > 0 && mutationItems[0].target != null) {
                // Elements with JScrollPane update a div non-stop, which keeps triggering the MutationObserver. If we detect that the Observer was
                // triggered by JScrollPane, then we will ignore it.
                const jScrollPaneRecords = mutationItems.every(x => (x.target.className === "jspContainer" && (x.addedNodes.length === 1 || x.removedNodes.length === 1)) || x.target.className === "jspHorizontalBar" || x.target === "jspVerticalBar");
                if (jScrollPaneRecords) {
                    return;
                }

                const recordsWithBody = mutationItems.filter(x => x.target.ownerDocument != null && x.target.ownerDocument.body.childNodes.length > 0);
                if (recordsWithBody.length > 0) {
                    this.processChanges(recordsWithBody[0].target.ownerDocument);
                }
            }
        }, 0, records);
    }

    processChanges(doc) {
        Array.from(doc.getElementsByTagName("iframe")).forEach((iframeElement) => {
            if (iframeElement.classList.contains("managed-iframe")) {
                return;
            }
            iframeElement.classList.add("managed-iframe");
            MutationObserverUtils.initFrame(iframeElement, (iframe) => {
                this.tryInitializeIFrame(iframe, 0);
            });
        });
    }

    tryInitializeIFrame(iframe, counter) {
        if (iframe.contentWindow != null) {
            setTimeout(() => {
                try {
                    if (iframe.contentWindow != null) {
                        iframe.contentWindow.altParent = iframe.ownerDocument.defaultView;
                        if (iframe.contentWindow.document.body.isContentEditable) {
                            return;
                        }
                        this.onScreenOpen(iframe);
                        new MutationObserver((mutations) => this.monitorChanges(mutations)).observe(iframe.contentWindow.document, this.mutationConfig);
                        iframe.contentWindow.addEventListener("unload", () => this.onScreenClose(iframe));
                    }
                } catch {
                    // We can't access the frame, so nothing to do here
                }
            });
        } else if (counter < 10) {
            setTimeout(() => this.tryInitializeIFrame(iframe, counter + 1), 500);
        }
    }

    onScreenOpen(iframe) {
        this.domUtils.dispatchEvent(this.document, Config.screenOpenEventName, {
            screen: iframe.contentWindow.document.body,
            isModal: false,
            isWarningOrConfirmationPopup: false,
            isIframe: true
        });
        monitorScreenForChanges(iframe.contentWindow.document.body);
    }

    onScreenClose(iframe) {
        this.domUtils.dispatchEvent(this.document, Config.screenCloseEventName, {
            screen: iframe.contentWindow.document.body,
            isModal: false,
            isWarningOrConfirmationPopup: false,
            isIframe: true
        });
        unmonitorScreenForChanges(iframe.contentWindow.document.body);
    }
}
