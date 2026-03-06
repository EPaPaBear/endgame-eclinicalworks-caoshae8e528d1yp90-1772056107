export const DomUtils = {

    querySelector: (element, selector) => {
        try {
            return element.querySelector(selector);
        } catch (error) {
            return null;
        }
    },

    dispatchEvent: (element, eventName, detail = {}) => {
        try {
            const event = new CustomEvent(eventName, { detail });
            element.dispatchEvent(event);
        } catch (error) {
            // Now what?
        }
    },
};

export const Config = {
    appId: "webemrApp",
    mainDivId: "ten-e-main-div",
    screenOpenEventName: "screenOpen",
    screenCloseEventName: "screenClose",
    screenChangeEventName: "screenChange",
    screenManagerHandledAttributeName: "screen-manager-handled"
};

export const debounce = (func, wait) => {
    let timeout;
    return (...args) => {
        clearTimeout(timeout);
        timeout = setTimeout(() => {
            func(...args);
        }, wait);
    };
};

export const monitorScreenForChanges = (screenElement) => {
    if (screenElement?.__screenObserver != null) {
        return;
    }

    const onChange = debounce((mutations) => {
        DomUtils.dispatchEvent(screenElement, Config.screenChangeEventName, {
            mutations
        });
    }, 100);
    screenElement.__screenObserver = new MutationObserver(onChange);
    screenElement.__screenObserver.observe(screenElement, { childList: true, subtree: true });
};

export const unmonitorScreenForChanges = (screenElement) => {
    if (screenElement?.__screenObserver != null) {
        screenElement.__screenObserver.disconnect();
        delete screenElement.__screenObserver;
    }
};
