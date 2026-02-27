(function() {

    var homunculusHelper = angular.module("ecw.ser.homunculusHelper", []);
    homunculusHelper.service('homunculusHelperService', function($http, $rootScope) {

        this.postRequest = function (url, data, async, cache) {
            return $http({
                method: 'POST',
                contentType : 'application/json',
                url : makeURL(url),
                data: data,
                cache : cache ? cache : false,
                async : (async !== 1)
            });
        };

        this.getRequest = function (url, data, async, cache) {
            return $http({
                method: 'GET',
                contentType : 'application/json',
                url : makeURL(url),
                data: data,
                cache : cache ? cache : false,
                async : (async !== 1)
            });
        };

    });

    homunculusHelper.service('svgToBase64Png', function () {
        const createStyleElementFromCSS = (useStyleSheet) => {
            const style = document.createElement('style');
            if (useStyleSheet) {
                let sheet = null;
                for (var value of document.styleSheets) {
                    if((value.href || '').includes(useStyleSheet)) {
                        sheet = value;
                        break;
                    }
                }
                if (sheet) {
                    const styleRules = [];
                    for (let i = 0; i < sheet.cssRules.length; i++) {
                        styleRules.push(sheet.cssRules.item(i).cssText);
                    }
                    style.appendChild(document.createTextNode(styleRules.join(' ')))
                }
            }
            return style;
        };

        const drawSVGToCanvas = (svg, tempClassToAddToSVG, style, width, height, margin = 0) => {
            const boundingRect = svg.getBoundingClientRect();
            const svgWidth = width ? width : boundingRect.width;
            const svgHeight = height ? height : boundingRect.height;

            const serializer = new XMLSerializer();
            const copy = svg.cloneNode(true);
            if (tempClassToAddToSVG) {
                copy.classList.add(tempClassToAddToSVG);
            }
            copy.insertBefore(style, copy.firstChild); // CSS must be explicitly embedded
            const data = serializer.serializeToString(copy);
            const image = new Image();
            const blob = new Blob([data], {
                type: 'image/svg+xml;charset=utf-8'
            });
            style.remove(); // remove temporarily injected CSS
            if (tempClassToAddToSVG) {
                svg.classList.remove(tempClassToAddToSVG);
            }
            const url = URL.createObjectURL(blob);
            return new Promise(resolve => {
                const canvas = document.createElement('canvas');
                const ctx = canvas.getContext('2d');
                canvas.width = svgWidth + (margin * 2);
                canvas.height = svgHeight + (margin * 2);
                image.addEventListener('load', () => {
                    ctx.drawImage(image, margin, margin, svgWidth, svgHeight);
                    URL.revokeObjectURL(url);
                    resolve(canvas);
                }, { once: true });
                image.src = url;
            })
        }

        this.convert = async function(params, format = 'image/png') {
            let canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');
            const style = createStyleElementFromCSS(params.useStyleSheet);
            const drawSVGs = Array.from(params.svgElements)
                .map(svg => drawSVGToCanvas(svg, params.tempClassToAddToSVG, style, params.width, params.height, params.margin));
            const renders = await Promise.all(drawSVGs);
            canvas.width = Math.max(...renders.map(render => render.width));
            canvas.height = Math.max(...renders.map(render => render.height));
            renders.forEach(render => ctx.drawImage(render, 0, 0, render.width, render.height));
            return canvas.toDataURL(format);
        }
    });

})();














