class CenterScreenHandler{playgroundDoc=document.createDocumentFragment();constructor(){this.getExcludedSelectors().then(excludedSelectors=>this.generateCSS(excludedSelectors.data))}generateCSS(excludedSelectors){const exSelectors=this.getValidatedSelectors(excludedSelectors).map(x=>`:not(${x})`).join("");const modalSelector=`html.app-web .modal:not(.healownow-admin-modal):not(.screen-center-ignore)${exSelectors}`;const css=`
        ${modalSelector} {
            text-align: center;
            white-space: nowrap;
        }
        
        ${modalSelector}:before {
            content: " ";
            display: inline-block;
            height: 100%;
            vertical-align: middle;
        }
        
        ${modalSelector} > div[class^="modal-dialog"],
        ${modalSelector} > div[class*=" modal-dialog"] {
            display: inline-block;
            margin-left: -2px;
            margin-top: 0 !important;
            padding-top: 0 !important;
            vertical-align: middle;
        }
        
        ${modalSelector} > *:not(.modal) {
            text-align: initial;
            white-space: initial;
        }
        `;const style=document.createElement("style");style.type="text/css";style.innerHTML=css;document.getElementsByTagName("head")[0].appendChild(style)}getValidatedSelectors(selectors){return selectors.filter(selector=>{try{this.playgroundDoc.querySelector(selector);return true}catch(e){return false}})}async getExcludedSelectors(){return await $.ajax({url:"/mobiledoc/emr/centerscreen/exclusions",type:"GET"})}}if(typeof exports!=="undefined"){module.exports=CenterScreenHandler}else{new CenterScreenHandler}