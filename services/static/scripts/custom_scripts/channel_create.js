function createChannel(){
    set_spinner('spinnerbar', 'sendBtn', 'cancelBtn');
    document.getElementById('start_time').value = document.getElementById('shour_select').value+':'+document.getElementById('smin_select').value;
    document.getElementById('end_time').value = document.getElementById('ehour_select').value+':'+document.getElementById('emin_select').value;
    document.forms['channel_create_form'].submit();
}

function setTime(sh, sm, eh, em){
    /*start time*/
    var stime = document.getElementById('stime_div');
    stime.innerHTML = "";
    setHourLoopSelect(stime, 'shour_select', sh)
    setMinuteLoopSelect(stime, 'smin_select', sm);
    /*end time*/  
    var etime = document.getElementById('etime_div');
    etime.innerHTML = "";
    setHourLoopSelect(etime, 'ehour_select', eh)
    setMinuteLoopSelect(etime, 'emin_select', em);
}