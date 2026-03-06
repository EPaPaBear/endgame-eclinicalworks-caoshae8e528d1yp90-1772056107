import { Config, monitorScreenForChanges, unmonitorScreenForChanges } from "./screen-utils.js";

export class AngularRouteManager {

    constructor(angular, document, domUtils) {
        this.angular = angular;
        this.document = document;
        this.domUtils = domUtils;
    }

    init() {
        const angularApp = this.angular.element(this.document.getElementById(Config.appId));

        if (angularApp.scope() != null) {
            this.initializeListeners(angularApp);
        } else {
            window.addEventListener("angularAppReady", () => this.initializeListeners(angularApp), { once: true });
        }
    }

    initializeListeners(angularApp) {
        angularApp.scope().$on("$routeChangeStart", (event, next, prev) => {
            if (next.$$route != null) {
                const element = this.domUtils.querySelector(this.document.getElementById(Config.mainDivId), "[ng-view]");
                this.onScreenClose({target: element});
            }
        });
        angularApp.scope().$on("$routeChangeSuccess", () => {
            const element = this.domUtils.querySelector(this.document.getElementById(Config.mainDivId), "[ng-view]");
            this.onScreenOpen({ target: element });
        });
    }

    onScreenOpen(event) {
        if (event.target == null) {
            // Unable to get reference to the screen, so exit
            return;
        }

        if (event.target.hasAttribute(Config.screenManagerHandledAttributeName)) {
            // Screen is already being monitored
            return;
        }
        event.target.setAttribute(Config.screenManagerHandledAttributeName, 1);

        this.domUtils.dispatchEvent(this.document, Config.screenOpenEventName, {
            screen: event.target,
            isModal: false,
            isWarningOrConfirmationPopup: event.target?.classList.contains("bootbox"),
        });
        monitorScreenForChanges(event.target);
    }

    onScreenClose(event) {
        if (event.target == null) {
            // Unable to get reference to the screen, so exit
            return;
        }

        event.target.removeAttribute(Config.screenManagerHandledAttributeName, 1);

        this.domUtils.dispatchEvent(this.document, Config.screenCloseEventName, {
            screen: event.target,
            isModal: false,
            isWarningOrConfirmationPopup: event.target?.classList.contains("bootbox"),
        });
        unmonitorScreenForChanges(event.target);
    }
}
