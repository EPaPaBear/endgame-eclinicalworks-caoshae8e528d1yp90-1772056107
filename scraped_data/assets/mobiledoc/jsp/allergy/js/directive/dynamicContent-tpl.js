angular.module('ecw.dir.dynamicContent', []).
        directive('dynamic',function( $compile ) {
	var directive = {
			restrict: 'A',
			replace: true,
			link: function(scope, ele, attrs) {
				scope.$watch(attrs.dynamic, function(html) {
					ele.html(html);
					$compile(ele.contents())(scope);
				});
			}
	}
	return directive;
});

/*
 add this line in your html to use this directive
 <div rich-text-editor="" ng-model='content'></div>
 */
