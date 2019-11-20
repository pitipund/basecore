function dismissChangeRelatedObjectPopup(win) {
    var initData = JSON.parse(win.document.getElementById('django-admin-popup-response-constants').dataset.popupResponse);
    var domId = 'change_' + windowname_to_id(win.name).replace(/^edit_/, '');
    document.getElementById(domId).innerHTML = initData.obj
    win.close();
}
