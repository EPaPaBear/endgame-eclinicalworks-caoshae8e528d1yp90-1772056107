import * as ScreenManager from "./screenManager/screen.js";
import { GlobalMentionsHandler, MentionsUtility } from "./mentions/mentions.js";
import { GlobalSmartFieldsHandler, SmartFieldsUtility } from "./smartfields/smartfields.js";
import { GCHandler, GCUtility } from "./concurrency/concurrency.js";
import { GlobalMacroHandler, GlobalMacroKeywordHandler, InlineSmartNotesHandler, MacroHandler } from "./macro/macro.js";
import { GlobalHotkeysHandler, HotkeysUtility } from "./hotkeys/hotkey.js";
import { GlobalTextareaExpander } from "./textareaExpander/textareaExpander.js";

// Set up global screen manager
ScreenManager.init();

// Set up Mentions
window.globalMentionsHandler = new GlobalMentionsHandler();
window.MentionsUtility = MentionsUtility;

// Set up Smart Fields
window.globalSmartFieldsHandler = new GlobalSmartFieldsHandler();
window.SmartFieldsUtility = SmartFieldsUtility;

// Set up Global Concurrency
window.gcHandler = new GCHandler();
//TODO: Added to retain state of code which was broken. Review if the methods shared should be defined independently or extract to common utility
window.GCUtility = GCUtility;

// Set up global Macro
window.macroHandler = new MacroHandler();
window.globalMacroHandler = new GlobalMacroHandler();
window.inlineSmartNotesHandler = new InlineSmartNotesHandler();
window.globalMacroKeywordHandler = new GlobalMacroKeywordHandler();

// Set up Keyboard Shortcuts
window.globalHotkeysHandler = new GlobalHotkeysHandler();
window.HotkeysUtility = HotkeysUtility;

// Set up Textarea Expander
if (isItemKeyEnabled('EnableNoteExpander')) {
  window.globalTextareaExpander = new GlobalTextareaExpander();
}