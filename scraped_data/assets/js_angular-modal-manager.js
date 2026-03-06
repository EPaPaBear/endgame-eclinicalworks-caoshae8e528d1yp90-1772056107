import { Config, monitorScreenForChanges, unmonitorScreenForChanges } from "./screen-utils.js";

export class AngularModalManager {

    constructor(angular, document, domUtils) {
        this.angular = angular;
        this.document = document;
        this.domUtils = domUtils;
    }

    init() {
        this.angular.module(Config.appId).directive("modalWindow", [() => {
            return {
                link: (scope, element) => {
                    this.onScreenOpen({ target: element[0] });
                    scope.$on("$destroy", () => {
                        this.onScreenClose({ target: element[0] });
                    });
                },
            };
        }]);
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
