function enable_btn() { /*not check disable delete button*/
    set_enableBtn('stream_check', 'deleteStreamBtn')
}

function checkAll() {
    set_checkAll('stream_all', 'stream_check');
}

function delete_stream(){
    set_spinner('spinnerbar', 'deleteStreamBtn', 'createStreamBtn');
    get_deleteID('Stream Server', 'stream_check', delete_link, list_link);
}