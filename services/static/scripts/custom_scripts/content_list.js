function enable_btn() { /*not check disable delete button*/
    set_enableBtn('content_check', 'deleteContentBtn')
}

function checkAll() {
    set_checkAll('content_all', 'content_check');
}

function delete_content() {
    set_spinner('spinnerbar', 'deleteContentBtn', 'createContentBtn');
    get_deleteID('Content', 'content_check', delete_link, list_link);
}