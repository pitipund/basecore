$(function() {
    $( "#sdate" ).datepicker();
});

function setAll(sel_sdate){
    if(document.getElementById('action').value=='create'){
        setChannel();
    }
    else{
        content = document.getElementById('tmpJson').value;
        var contentJson =JSON.parse(content);
        var channel_span = document.createElement('span');
        channel_span.innerHTML = contentJson[0].chname;
        channel_div = document.getElementById('channel_div');
        channel_div.appendChild(channel_span);
        setTimeSel();
    }
    document.getElementById('sdate').value = sel_sdate; // date
    
}

function setChannel() {
    channel = document.getElementById('tmpJson').value;
    var channelJson =JSON.parse(channel);
    var channel_select = lib_createObj("channel_select", 'select', "my_select") // select
    channel_select.setAttribute("onChange", "setTimeSel();");
    channel_select.innerHTML = "";
    for(i in channelJson){
        channel_select.innerHTML += "<option value="+channelJson[i].chid+">"+channelJson[i].chname+"</option>";
    }
    channel_div = document.getElementById('channel_div');
    channel_div.appendChild(channel_select);
    setTimeSel();
}

function setTimeSel(){
    time = document.getElementById('tmpJson').value;
    var timeJson =JSON.parse(time);
    if(document.getElementById('action').value == 'create'){
        for(i in timeJson){
            if(timeJson[i].chid==document.getElementById('channel_select').value){ // get time from channel
                result = timeJson[i].chtime.split(',');
                break;
            }
        }
    }
    else{
        result = timeJson[0].chtime.split(',');
    }    
    /*start time*/
    var stime = document.getElementById('stime_div');
    stime.innerHTML = "";
    setHourSelect(stime, 'shour_select', result, document.getElementById('sel_shour_time').value);
    setMinuteLoopSelect(stime, 'smin_select', document.getElementById('sel_sminute_time').value);
}

function createTextOverlay(){
    set_spinner('spinnerbar', 'sendBtn', 'cancelBtn');
    if(document.getElementById('action').value != 'create'){
        channel = document.getElementById('tmpJson').value;
        var channelJson =JSON.parse(channel);
        document.getElementById('channel_id').value = channelJson[0].chid;
    }
    document.forms["textOverlay_create_form"].submit();
}