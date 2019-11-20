function enable_btn() { /*not check disable delete button*/
    set_enableBtn('channel_check', 'deleteChannelBtn')
}

function checkAll() {
    set_checkAll('channel_all', 'channel_check');
}

function delete_channel() {
    set_spinner('spinnerbar', 'deleteChannelBtn', 'createChannelBtn');
    get_deleteID('Channel', 'channel_check', delete_link, list_link);
}