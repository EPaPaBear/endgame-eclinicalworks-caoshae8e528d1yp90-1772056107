/**
 * Allow undo only on elements in active modal otherwise immediately fire a redo to avoid undo to make changes on elements not on active modal
 */

class UndoHandler {

  constructor() {
    this.setupGlobalUndoHandler();
  }

  setupGlobalUndoHandler() {
    addEventListener("input", (evt) => this.onInput(evt), {
      capture: true
    });
  }

  eliminateParent(openModals) {
    if (openModals && openModals.length > 1) {
      let eliminatedElements = new Map();
      for (let i = 0; i < openModals.length; i++) {
        for (let j = 0; j < openModals.length; j++) {
          if (i !== j && openModals[i].contains(openModals[j])) {
            eliminatedElements.set(openModals[i], 1);
            break;
          }
        }
      }
      for (let all = 0; all < openModals.length; all++) {
        if (eliminatedElements.get(openModals[all])){
          openModals.splice(all, 1);
        }
      }
    }
    return openModals;
  }

  onInput(event){
    if (event.inputType === 'historyUndo' && event.target) {
      const openModals = Array.from(document.getElementsByClassName("modal in"));
      const activeTopModals = this.eliminateParent(openModals);
      const firstClickableModal = activeTopModals.find(this.isElementClickable);
      if (firstClickableModal == null) {
        // No clickable modal available
        return;
      }
      if(!firstClickableModal.contains(event.target)){
        document.execCommand('redo', false, null);
      }
    }
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
  module.exports = { UndoHandler };
} else {
  // For vanilla JavaScript includes, initialize instance
  window.undoHandler = new UndoHandler();
}
