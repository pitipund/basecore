import Semantic.Html 1.0

Accordion {
    id:card
    property alias titleRibbon: _ribbonText.text
    property alias title: _headerText.text
    property alias titleContent: gclTitleContent.data
    property alias hideTitleRibbon: gclTitleRibbon.displayNone
    property alias hideTitle: gidTitle.displayNone
    property alias hideTitleText: gclTitle.displayNone
    property alias hideTitleContent: gclTitleContent.displayNone
    property alias content: _content.data
    property bool hideCloseButton  // hide close button and use dropdown icon instead
    property bool hideHeaderIcon  // hide all icon in header
    property string ribbonColor
    property string headerColor
    property bool inModal: false
    property bool toggleCard: true  // allow card to toggle
    property bool hideDivider
    property bool smoothFade: true  // Enable animation when fade
    property var allowClose: true // can be a function
    property var ignoreToggle: []
    property var hideCallback //callback when hide or deleted
    property var showCallback //callback when closed
    property var ribbonTextClassName : "eight wide"
    property var headerTextClassName : "eight wide"
    property var titleContentClassName : "eight wide right aligned"

    property alias readOnly: dimReadOnly.active
    property bool loading

    expanded:true
    eventName:false
    style: "padding: 0px;"
    className: headerColor + " defaultBackground styled fluid raised segment"
    htmlAttr: new Object({
        type: 'card'
    })

    onInModalChanged: {
        if (inModal) {
            toggleCard = false
            allowClose = false
            closeButton.displayNone = true
            arrowIcon.displayNone = true
        } else {
            toggleCard = true
            allowClose = true
            closeButton.displayNone = false
            arrowIcon.displayNone = false
        }
    }

    onReadOnlyChanged: {
        if (readOnly) {
            _content.dom.classList.add('dimmable', 'dimmed')
        }
        else {
            _content.dom.classList.remove('dimmable', 'dimmed')
        }
    }

    onHideCloseButtonChanged:{
        if(hideCloseButton) {
            closeButton.displayNone = true
            arrowIcon.displayNone = false
        }
        else {
            closeButton.displayNone = false
            arrowIcon.displayNone = true
        }
    }

    onHideHeaderIconChanged:{
        if(hideHeaderIcon){
            closeButton.displayNone = true
            arrowIcon.displayNone = true
        }
        else{
            closeButton.displayNone = false
            arrowIcon.displayNone = false
        }
    }

    onOpening:{
        openAnim()
    }

    onClosing:{
        closeAnim()
    }

    //workaround for fixing modal position is not center
    onOpen:{
        $.each($('.ui.modal'), function(index,ele){
            if($.contains(ele, card.dom)) {
                setTimeout(function(){
                    $(ele).modal('refresh')
                })
            }
        })
        //workaround for fixing agenda is not show
        $.each($('div[data-main=fullcalendar]'), function(index,ele){
            if($.contains(card.dom, ele)) {
                setTimeout(function(){
                    $(ele).fullCalendar('render');
                })
            }
        })

    }

    Component.onCompleted: {
        card.completed = true
        if (card.displayNone) {
            card.dom.style.display = 'none'
            transitionComplete()
        } else {
            displayNoneCallBack()
        }
    }

    function displayNoneCallBack() {
        if (!card.completed) {
            return
        }
        if (!card.smoothFade) {
            if (card.displayNone) {
                card.dom.style.display = 'none'
            }else {
                card.dom.style.display = ''
            }
            transitionComplete()
        } else {
            var duration = 150
            if (card.displayNone) {
                card.transition({
                    animation: 'fade out',
                    duration: duration,
                    silent: true,
                    onComplete: card.transitionComplete
                })
            } else {
                card.transition({
                    animation: 'fade in',
                    duration: duration,
                    onComplete: card.transitionComplete
                })
            }
        }
    }

    function transitionComplete() {
        if(card.displayNone) {
            card.hideCallback && card.hideCallback()
        }
        else {
            card.showCallback && card.showCallback()
            document.body.dispatchEvent(
                new CustomEvent("resizeDgrid", {
                    detail: { dom: card.dom }
                })
            );
        }
    }

    function openAnim() {
        divider.displayNone = card.hideDivider ? true : false
        arrowIcon.dom.style.transform = "rotate(-90deg)"
        arrowIcon.dom.style.transition = "transform 0.15s linear"
    }

    function closeAnim() {
        divider.displayNone = true
        arrowIcon.dom.style.transform = "rotate(0deg)"
        arrowIcon.dom.style.transition = "transform 0.15s linear"
    }

    Link{
        id:closeButton
        doc_label: 'ปุ่มปิด'
        href: "javascript:void(0)"
        text: "&#10006"

        style: {
            return{
                position:"absolute",
                right:"5px",
                top:"5px",
                color:"red",
                fontSize:"x-large",
                zIndex:"2"
            };
        }

        onClicked:{
            if (typeof card.allowClose == 'function' && card.allowClose()) {
                 card.displayNone = true
            }
            else if (typeof card.allowClose == 'boolean' && card.allowClose){
                card.displayNone = true
            }
        }
    }

    AccordionTitle {
        doc_label: title
        //filter click event before expand of collapse accordion
        onClicked:{
            var target = event.target
            var expandAcc = true

            ignoreToggle.forEach(function(ele) {
                if(target.isSameNode(ele.dom)) {
                    expandAcc = false
                }
                if($.contains(ele.dom, target)) {
                    expandAcc = false
                }
            })

            toggleCard && expandAcc && card.toggle()
            target = null
        }

        style: {
            return{
                borderTop: "0px !important",
                zIndex:"1"
            }
        }

        Icon{
            doc_skip: "all"
            id:arrowIcon
            doc_label: 'ปุ่มย่อ'
            displayNone:true
            icon:"caret left"
            style: {
                return{
                    position:"absolute",
                    right:"5px",
                    color:"black",
                    fontSize:"x-large"
                }
            }
        }

        Grid {
            id: gidTitle
            Row {
                style: {
                    return {
                        marginRight: "20px"
                    }
                }
                Column {
                    id: gclTitleRibbon
                    className: ribbonTextClassName
                    LabelTag {
                        id: _ribbonText
                        doc_skip: "me"
                        className: ribbonColor + " ribbon label"
                    }
                    displayNone: true
                }
                Column {
                    id: gclTitle
                    className: headerTextClassName
                    Text{
                        id: _headerText
                        className: "header"
                    }
                }
                Column{
                    id: gclTitleContent
                    className: titleContentClassName
                }
            }
            Row {
                style: {
                    return {
                        paddingTop: "0px",
                        paddingBottom: "0px",
                        marginTop: "-10px",
                    }
                }
                Column {
                    id:divider
                    displayNone:true
                    className: "sixteen wide"
                    Dom { tagName: "hr" }
                }
            }
        }
    }
    AccordionContent {
        id: _content
        doc_skip: "me"
        Dimmer {
            id: dimReadOnly
            doc_skip: "me"
            className: "light inverted"
        }
        Dimmer {
            doc_skip: 'me'
            active: loading
            className: 'inverted'
            Loading {
                className: 'large text'
                text: 'Loading'
            }
        }
        style: {
            return {
                paddingBottom: "14px",
            }
        }
    }
}
