/**
 * 1. Trap focus inside modal
 * 2. Prevent activation of non-clickable elements in background
 */

class TabHandler {

  static FOCUSABLE_ELEMENTS = ["input", "textarea", "button", "select", "a"];

  constructor() {
    this.setupGlobalFocusHandler();
  }

  setupGlobalFocusHandler() {
    document.addEventListener("focus", (evt) => this.onFocus(evt), {
      capture: true
    });
  }

  onFocus(event) {
    const openModals = Array.from(document.getElementsByClassName("modal in"));
    const firstClickableModal = openModals.find(this.isElementClickable);
    if (firstClickableModal == null) {
      // No clickable modal available
      return;
    }
    if (!firstClickableModal.contains(event.target) && $("#ecwassistantcontroller").find(event.target).length == 0) {
      // Focus went outside of the modal, bring it back
      event.preventDefault();
      event.stopImmediatePropagation();
      event.stopPropagation();

      // Find first focusable element
      const firstFocusableElement = this.getFirstFocusableElement();
      if (firstFocusableElement != null) {
        // Found first element that's focusable
        firstFocusableElement.focus();
      }
    }
  }

  getFirstFocusableElement() {
    const elements = Array.from(document.querySelectorAll(TabHandler.FOCUSABLE_ELEMENTS.join(",")));
    return elements.find(this.isElementClickable);
  }

  isElementClickable(element) {
    if (element == null) {
      return false;
    }

    // Get location of element
    const location = element.getBoundingClientRect();

    // Get actual top-most element at coordinates of {location}
    const elementAtLocation = document.elementFromPoint(location.x + (location.width / 2), location.y + (location.height / 2));

    // Return true if element at location is the actual element itself
    return elementAtLocation === element || element.contains(elementAtLocation);
  }

}

// Export for module availability
if (typeof exports !== "undefined") {
  module.exports = { TabHandler };
} else {
  // For vanilla JavaScript includes, initialize instance
  window.tabHandler = new TabHandler();
}
