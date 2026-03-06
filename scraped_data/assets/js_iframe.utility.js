var WebEditor_IFrameUtility = {};
(function (a) {
	a.PDFViewerUtility = {
		loadViewerInIFrameUsingTarget: function (iframeSelector, jsonPostData) {
			jsonPostData.Stream = window.getItemKeyValue("EnableWebEditorStreaming", false);
			return WebEditor_IFrameUtility.PDFViewerUtility.loadIFrameUsingTarget(window.makeURL("/mobiledoc/jsp/webemr/webEditor/pdfViewer.jsp"), jsonPostData, iframeSelector);
		}, loadIFrameUsingTarget: function (url, jsonPostData, iframeSelector) {
			return $.Deferred(function (dfd) {
				try {
					if (!iframeSelector) {
						dfd.reject('Selector is not valid');
						return;
					}
					if (!jsonPostData || Object.keys(jsonPostData).length <= 0) {
						dfd.reject('Request data is empty');
						return;
					}
					iframeSelector = $(iframeSelector)[0];
					var iframeName = iframeSelector.getAttribute("name");
					if (!iframeName) {
						dfd.reject('iframe name attribute is required, as target will be iframe name.');
						return;
					}

					function successCallBack() {
						dfd.resolve();
					}

					function errorCallBack() {
						dfd.reject();
					}

					$(iframeSelector).one('load',successCallBack);
					$(iframeSelector).one('error',errorCallBack);
					let iframePostRequestDisabled = window.getItemKeyValue("IFramePostRequestDisabled", false);
					if (iframePostRequestDisabled?.toLowerCase() === 'yes') {
						WebEditor_IFrameUtility.PDFViewerUtility.loadIFrameUsingGet(url, jsonPostData, iframeSelector, dfd);
					} else {
						WebEditor_IFrameUtility.PDFViewerUtility.loadIFrameUsingPost(url, jsonPostData, iframeSelector, dfd);
					}
				} catch (e) {
					console.error(e);
					dfd.reject("Fail to load url in iframe.");
				}
			});
		}, loadIFrameUsingGet: function (url, jsonPostData, iframeSelector) {
			iframeSelector.src = url + "&" + $.param(jsonPostData);
		}, loadIFrameUsingPost: function (url, jsonPostData, iframeSelector) {
			var iframeForm = document.createElement("form");
			var iframeName = iframeSelector.getAttribute("name");
			iframeForm.method = "POST";
			iframeForm.action = url;
			iframeForm.name = "dynamicFormName" + new Date().getTime();
			$(iframeForm).insertBefore(iframeSelector)
			iframeForm.setAttribute("target", iframeName);
			var defaultRequestData = {
				token: window.csrfToken,
				"_csrf": window.csrfToken
			};
			$.each(Object.assign(jsonPostData, defaultRequestData), function (n, v) {
				var hiddenElement = document.createElement("input");
				hiddenElement.setAttribute("type", "hidden");
				hiddenElement.setAttribute("name", n);
				hiddenElement.setAttribute("value", v);
				iframeForm.append(hiddenElement);
			});
			setTimeout(function () {
				$(iframeForm).submit();
			},200);
			setTimeout(function () {
				$(iframeForm).remove();
			}, 1000);
		}
	};
})(WebEditor_IFrameUtility)
