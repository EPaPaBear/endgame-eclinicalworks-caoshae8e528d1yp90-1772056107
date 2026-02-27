/*
AI Generate Button Directive

This directive provides a button to be used in any scenario wherein the user triggers an action performed by an AI model.

The intent is to ensure that a consistent UI (icon, theme, loading indicator, etc.) is used for this type of functionality across the application.

Usage:
1. Include the module in your dependencies.
Example: angular.module('myModule', ['ecw.dir.ai-generate-btn'])
2. Add the directive to your view.
Example: <ai-generate-btn is-loading="isInterpretationInProgress" label="Interpret" on-click="interpret()"/>

Attributes:
is-loading | a boolean indicating whether the AI operation associated with the button is currently in progress
label      | the label to display on the button next to the AI icon (optional - defaults to "Generate")
on-click   | the function to be called when a user clicks the button
*/
angular.module('ecw.dir.ai-generate-btn', [])
.directive('aiGenerateBtn', [function() {
  return {
    templateUrl: '/mobiledoc/jsp/webemr/ai/ecw.dir.ai-generate-btn.html',
    restrict: 'E',
    scope: {
      isLoading: '=',
      label: '=?',
      onClick: '&'
    },
    link: function (scope, element) {
      // The value passed to scope.label is initially assumed to be an AngularJS expression.
      // If that expression evaluates to undefined, we handle it as a string instead:
      scope.label ??= element.attr('label') || 'Generate';
    }
  }
}]);