function getAge (birthdate) {
    var today = new Date();

    let [bday, bmonth, byear] = birthdate.split("/");
    byear = (byear - 543 >= 0)? (byear - 543) : byear;
    var age = diffDate(today, new Date([byear, bmonth, bday].join("-")));

    return age["years"] + " ปี " + age["months"] + " เดือน " + age["days"] + " วัน";
}

function diffDate (date1, date2) {
    var m = moment(date1);
    var years = m.diff(date2, 'years');
    m.add(-years, 'years');
    var months = m.diff(date2, 'months');
    m.add(-months, 'months');
    var days = m.diff(date2, 'days');

    return {years: years, months: months, days: days};
}

function setCookie (cname, cvalue, exdays) {
    var d = new Date();
    d.setTime(d.getTime() + (exdays*24*60*60*1000));
    var expires = "expires="+ d.toUTCString();
    document.cookie = cname + "=" + cvalue + ";" + expires + ";path=/";
}

function getCookie (cname) {
    var name = cname + "=";
    var decodedCookie = decodeURIComponent(document.cookie);
    var ca = decodedCookie.split(';');
    for(var i = 0; i < ca.length; i++) {
        var c = ca[i];
        while (c.charAt(0) == ' ') {
            c = c.substring(1);
        }
        if (c.indexOf(name) == 0) {
            return c.substring(name.length, c.length);
        }
    }
    return "";
}
function formatPrice(val) {
    var value = formatComma(val);
    return '<div style="text-align: right; ">' + value + '</div>';
}
function formatComma(val){
    return !isNaN(parseFloat(val)) ? parseFloat(val).toFixed(2).toString().replace(/\B(?=(?:\d{3})+(?!\d))/g, ",") : val;
}

/**
 *
 * Normal:
 *  Util.alert('test', 'black', 'ok', null, function() {console.log('hide')}, 'text in content')
 * Toast:
 *  Util.alert('test', 'red', 'ok', 2000, function() {console.log('toast')})
 * Object at the first argument
 *  Util.alert({
 *      titleName: 'test object',
 *      buttonText: 'OK'
 *  })
 * @param {string | object} titleName
 * @param {string} titleColor
 * @param {string} buttonText
 * @param {integer} duration
 * @param {function} onHide
 * @param {string} textContent
 */
function alert(titleName, titleColor, buttonText, duration, onHide, textContent) {
    if (typeof titleName === 'object') {
        titleColor = titleName.titleColor
        buttonText = titleName.buttonText
        duration = titleName.duration
        onHide = titleName.onHide
        textContent = titleName.textContent
        titleName = titleName.titleName
    }

    function __callOnCompleted(child) {
        child.Component.completed()
        const QMLBaseObject = QmlWeb.getConstructor("QtQml", "2.0", "QtObject")
        for (var i = 0; i < child.$tidyupList.length; i++) {
            if (child.$tidyupList[i] instanceof QMLBaseObject) {
                __callOnCompleted(child.$tidyupList[i])
            }
        }
    }
    function __removeChildProperties(child) {
        var signals = QmlWeb.engine.completedSignals
        signals.splice(signals.indexOf(child.Component.completed), 1)
        for (var i = 0; i < child.children.length; i++) {
            this.__removeChildProperties(child.children[i])
        }
    }
    if (typeof onHide !== 'function') {
        onHide = function() {}
    }
    $(function(){
        var modal = Qt.createComponent("../Common/ModInfo.qml")
        modal = modal.$createObject()
        if (QmlWeb.engine.firstCallCompleted) {
            __callOnCompleted(modal)
        }
        if (QmlWeb.engine.operationState !== QMLOperationState.Init) {
            QmlWeb.engine.$initializePropertyBindings()
        }
        modal.titleName = titleName || modal.titleName
        modal.textContent = textContent || modal.textContent
        modal.titleColor = titleColor || modal.titleColor
        modal.buttonText = buttonText || modal.buttonText
        modal.approved.connect(modal, function() {
            modal.hide()
        })
        modal.hidden.connect(modal, function () {
            modal.$delete()
            __removeChildProperties(modal)
            onHide()
        })
        if (duration > 0) {
            setTimeout(modal.toast.bind(modal, duration))
        } else {
            setTimeout(modal.show.bind(modal))
        }
    })
}


/**
 * Util.confirm('test', 'orange', 'text content', function() {console.log('approve')}, function() {console.log('deny')})
 *
 * Object at the first argument
 *
 * Util.confirm({
 *     titleName: 'test object',
 *     buttonText: 'OK'
 * })
 * @param {string | object} titleName
 * @param {string} titleColor
 * @param {string} textContent
 * @param {function} onApprove
 * @param {function} onDeny
 * @param {string} approveButtonText
 * @param {string} denyButtonText
 * @param {string} approveButtonColor
 * @param {string} denyButtonColor
 */
function confirm(
    titleName,
    titleColor,
    textContent,
    onApprove,
    onDeny,
    approveButtonText,
    denyButtonText,
    approveButtonColor,
    denyButtonColor) {

    if (typeof titleName === 'object') {
        titleColor = titleName.titleColor
        textContent = titleName.textContent
        onApprove = titleName.onApprove
        onDeny = titleName.onDeny
        approveButtonText = titleName.approveButtonText
        denyButtonText = titleName.denyButtonText
        approveButtonColor = titleName.approveButtonColor
        denyButtonColor = titleName.denyButtonColor
        titleName = titleName.titleName
    }

    function __callOnCompleted(child) {
        child.Component.completed()
        const QMLBaseObject = QmlWeb.getConstructor("QtQml", "2.0", "QtObject")
        for (var i = 0; i < child.$tidyupList.length; i++) {
            if (child.$tidyupList[i] instanceof QMLBaseObject) {
                __callOnCompleted(child.$tidyupList[i])
            }
        }
    }
    function __removeChildProperties(child) {
        var signals = QmlWeb.engine.completedSignals
        signals.splice(signals.indexOf(child.Component.completed), 1)
        for (var i = 0; i < child.children.length; i++) {
            this.__removeChildProperties(child.children[i])
        }
    }

    if (typeof onApprove !== 'function') {
        onApprove = function () { }
    }
    if (typeof onDeny !== 'function') {
        onDeny = function () { }
    }

    $(function () {
        var modal = Qt.createComponent("../Common/ModConfirm.qml")
        modal = modal.$createObject()
        if (QmlWeb.engine.firstCallCompleted) {
            __callOnCompleted(modal)
        }
        if (QmlWeb.engine.operationState !== QMLOperationState.Init) {
            QmlWeb.engine.$initializePropertyBindings()
        }

        modal.titleName = titleName || modal.titleName
        modal.titleColor = titleColor || modal.titleColor
        modal.textContent = textContent || modal.textContent
        modal.approveButtonText = approveButtonText || modal.approveButtonText
        modal.denyButtonText = denyButtonText || modal.denyButtonText
        modal.approveButtonColor = approveButtonColor || modal.approveButtonColor
        modal.denyButtonColor = denyButtonColor || modal.denyButtonColor

        modal.approve.connect(modal, function () {
            modal.hide()
            onApprove()
        })
        modal.deny.connect(modal, function () {
            modal.hide()
        })

        modal.hidden.connect(modal, function () {
            modal.$delete()
            __removeChildProperties(modal)
            onDeny()
        })

        setTimeout(modal.show.bind(modal))
    })
}
