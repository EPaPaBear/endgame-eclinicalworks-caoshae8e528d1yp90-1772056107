import { BootstrapModalManager } from "./bootstrap-modal-manager.js";
import { AngularModalManager } from "./angular-modal-manager.js";
import { AngularRouteManager } from "./angular-route-manager.js";
import { IframeManager } from "./iframe-manager.js";
import { DomUtils } from "./screen-utils.js";

export const init = () => {
    new BootstrapModalManager(document, DomUtils).init();
    new AngularModalManager(angular, document, DomUtils).init();
    new AngularRouteManager(angular, document, DomUtils).init();
    new IframeManager(document, DomUtils).init();
};
