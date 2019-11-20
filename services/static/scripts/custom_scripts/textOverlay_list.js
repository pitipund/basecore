function enable_btn() { /*not check disable delete button*/
    set_enableBtn('textOverlay_check', 'deleteTextOverlayBtn')
}

function checkAll() {
    set_checkAll('textOverlay_all', 'textOverlay_check');
}

function delete_textOverlay(){
    set_spinner('spinnerbar', 'deleteTextOverlayBtn', 'createTextOverlayBtn');
    get_deleteID('Text Overlay', 'textOverlay_check', delete_link, list_link);
}