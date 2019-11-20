function enable_btn() { /*not check disable delete button*/
    set_enableBtn('showtime_check', 'deleteShowtimeBtn')
}

function checkAll() {
    set_checkAll('showtime_all', 'showtime_check');
}

function delete_showtime() {
    set_spinner('spinnerbar', 'deleteShowtimeBtn', 'createShowtimeBtn');
    get_deleteID('Showtime', 'showtime_check', delete_link, list_link)
}