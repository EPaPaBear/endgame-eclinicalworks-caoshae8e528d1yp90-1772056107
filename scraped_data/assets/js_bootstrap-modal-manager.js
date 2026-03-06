import { Config, monitorScreenForChanges, unmonitorScreenForChanges } from "./screen-utils.js";

export class BootstrapModalManager {

    constructor(document, domUtils) {
        this.document = document;
        this.domUtils = domUtils;
    }

    init() {
        $(document).on("show.bs.modal", this.onScreenOpen.bind(this));
        $(document).on("hide.bs.modal", this.onScreenClose.bind(this));
    }

    onScreenOpen(event) {
        if (event.target.hasAttribute(Config.screenManagerHandledAttributeName)) {
            // Screen is already being monitored
            return;
        }
        event.target.setAttribute(Config.screenManagerHandledAttributeName, 1);

        this.domUtils.dispatchEvent(this.document, Config.screenOpenEventName, {
            screen: event.target,
            isModal: true,
            isWarningOrConfirmationPopup: event.target.classList.contains("bootbox"),
        });
        monitorScreenForChanges(event.target);
    }

    onScreenClose(event) {
        event.target.removeAttribute(Config.screenManagerHandledAttributeName);

        this.domUtils.dispatchEvent(this.document, Config.screenCloseEventName, {
            screen: event.target,
            isModal: true,
            isWarningOrConfirmationPopup: event.target.classList.contains("bootbox"),
        });
        unmonitorScreenForChanges(event.target);
    }
}
