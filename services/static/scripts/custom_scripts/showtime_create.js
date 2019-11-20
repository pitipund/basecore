$(function() {
    $( "#sdate" ).datepicker();
});

function setAll(sel_sdate){
    content = document.getElementById('tmpJson').value;
    var contentJson =JSON.parse(content);    
    if(document.getElementById('action').value=='create'){
        setChannel(contentJson);
        document.getElementById('etime_span').innerHTML = "";
    }
    else{
        setUpdateLable(contentJson);
        if(document.getElementById('advt_sel').value != '[]'){
            createUpdateObj();
        }
    }
    setTimeSel();
    document.getElementById('sdate').value = sel_sdate; // date    
}

function setUpdateLable(contentJson){
    /*channel*/
    var channel_span = document.createElement('span');
    channel_span.innerHTML = contentJson[0].chname;
    channel_div = document.getElementById('channel_div');
    channel_div.appendChild(channel_span);
    /*content*/
    var content_span = document.createElement('span');
    content_span.innerHTML = contentJson[0].conname;
    content_div = document.getElementById('content_div');
    content_div.appendChild(content_span);
}

function setChannel(channel) {
    var channel_select = lib_createObj("channel_select", 'select', "my_select") // select
    channel_select.setAttribute("onChange", "setcontent();setTimeSel();");
    channel_select.innerHTML = "";
    for(i in channel){
        channel_select.innerHTML += "<option value="+channel[i].chid+">"+channel[i].chname+"</option>";
    }
    channel_div = document.getElementById('channel_div');
    channel_div.appendChild(channel_select);
    setcontent();
}

function setcontent(){
    selChannel = document.getElementById('channel_select').value;
    content = document.getElementById('tmpJson').value;
    var contentJson =JSON.parse(content);
    var content_select = lib_createObj("content_select", 'select', "my_select") // select
    content_select.innerHTML = "";
    for(i in contentJson){
        if(contentJson[i].chid == selChannel){ // list content from channel
            var contentId = contentJson[i].conid.split('_');
            var contentName = contentJson[i].conname.split('_');            
            for(i in contentId){
                content_select.innerHTML += "<option value="+contentId[i]+">"+contentName[i]+"</option>";
            }
            content_div = document.getElementById('content_div');
            content_div.innerHTML = '';
            content_div.appendChild(content_select);
            break;
        }
    }
}

function setTimeSel(){
    content = document.getElementById('tmpJson').value;
    var contentJson =JSON.parse(content);
    if(document.getElementById('action').value == 'create'){
        for(i in contentJson){
            if(contentJson[i].chid==document.getElementById('channel_select').value){ // get time from channel
                result = contentJson[i].chtime.split(',');
                break;
            }
        }
    }
    else{
        result = contentJson[0].chtime.split(',');
    }
    /*start time*/
    var stime = document.getElementById('stime_div');
    stime.innerHTML = "";
    setHourSelect(stime, 'shour_select', result, document.getElementById('sel_shour_time').value);
    setMinuteLoopSelect(stime, 'smin_select', document.getElementById('sel_sminute_time').value);
}

function checkShowtime() {
    var dup = -1; /*-1 is True else is error*/
    if(document.getElementById('action').value == 'create'){
        var ch = document.getElementById('channel_select').value;
        var con = document.getElementById('content_select').value;        
    }
    else{
        content = document.getElementById('tmpJson').value;
        var contentJson =JSON.parse(content);
        var ch = contentJson[0].chid;
        var con = contentJson[0].conid;
    }
    var sd = new Date(document.getElementById('sdate').value);
    var sh = document.getElementById('shour_select').value;
    var sm = document.getElementById('smin_select').value;
    var s = sd.getFullYear()+'_'+(sd.getMonth()+1)+'_'+sd.getDate()+'_'+sh+'_'+sm;
    if(document.getElementById('conrow_div1')){
        et = (document.getElementById('etime').value).split(":");
        if(et[3]<10){ // et[3] is end hour, if 00-09 remove 0
            et[3] = parseInt(et[3]);
        }
        if(sm<10){ // sm is start minute, if 0-9 add 0_
            sm = "0"+sm;
        }        
        list = [sh+"."+sm, et[3]+"."+et[4]]; // [start, end]
        var isTrue = true;
        var i = 1;
        var advtTmp = "";
        while(isTrue){        
            var tmp = 'conrow_div'+i;
            if(document.getElementById(tmp)){
                var h = document.getElementById('advtHour_select'+i).value;
                var m = document.getElementById('advtMin_select'+i).value;                
                if(parseInt(m)<10){ // m is minute seleceted, if 0-9 add 0_
                    m = "0"+m;
                }
                dup = list.indexOf(h+"."+m);
                if(dup != -1){
                    alert("Time duplicate.");
                    break;
                }
                if((sh+"."+sm<h+"."+m) && (h+"."+m<et[3]+"."+et[4])){ // start < hour.min < end
                    list.push(h+"."+m);
                    var tmp = document.getElementById(tmp).value+'_'
                    advtTmp += tmp;
                    i += 1;
                }
                else{
                    alert("Time out of range.");
                    dup = -2;
                    break;
                }
            }
            else{
                isTrue = false;
            }
        }
        var advt = advtTmp;
    }
    else{
        var advt = 'no';
    }
    if(dup == -1){
        $.get("/showtime_check/"+ch+"/"+con+"/"+s+"/"+advt+"/", function(data) {
            if (data.result=="T" && data.msg=='T') {
                document.getElementById('advt').value = data.advt;
                document.getElementById('etime').value = data.end_time;
                set_createBtn();
                document.getElementById('etime_span').innerHTML = 'End time : '+data.end_time+' duration : '+data.duration;
                document.getElementById("noSendBtn").className = "btn btn-primary hidden";
                document.getElementById("sendBtn").className = "btn btn-primary"
            }
            else {
                alert(data.msg);
            }
        });
    }
}

function createShowtime(action) {
    set_spinner('spinnerbar', 'sendBtn', 'cancelBtn');
    /*start time*/
    var sd = new Date(document.getElementById('sdate').value);
    var sh = document.getElementById('shour_select').value;
    var sm = document.getElementById('smin_select').value;
    var s = sd.getFullYear()+':'+(sd.getMonth()+1)+':'+sd.getDate()+':'+sh+':'+sm;
    document.getElementById('start_time').value = s;
    if(action=='create'){        
        document.getElementById('content_id').value = document.getElementById('content_select').value;
    }
    else{
        content = document.getElementById('tmpJson').value;
        var contentJson =JSON.parse(content);
        document.getElementById('content_id').value = contentJson[0].conid;
    }
    document.forms["showtime_create_form"].submit();
}

function delAShowtime(a_del){
    set_spinner('spinnerbar', 'sendBtn', 'cancelBtn');
    advt = document.getElementById('conrow_div'+a_del.id).value;
    var sd = new Date(document.getElementById('sdate').value);
    var sh = document.getElementById('advtHour_select'+a_del.id).value;
    var sm = document.getElementById('advtMin_select'+a_del.id).value;
    var s = sd.getFullYear()+'_'+(sd.getMonth()+1)+'_'+sd.getDate()+'_'+sh+'_'+sm;
    confirmMsg = confirm('Are you sure you want to delete this Advertising?');
    if(confirmMsg){
        delete_link = delete_link.replace('ling', s+'_'+advt);
        location.href = delete_link;
    }
    else{
        location.href = list_link;
    }
}

function createUpdateObj(){
    document.getElementById("noSendBtn").className = "btn btn-primary disabled";
    document.getElementById("sendBtn").className = "btn btn-primary hidden";
    document.getElementById('add_btn_master').className = "hidden";
    /*---Prepare variable---*/
    advt = document.getElementById('advt').value;
    var advtJson = JSON.parse(advt);
    var contentId = advtJson[0].conid.split('_');
    var contentName = advtJson[0].conname.split('_');    
    advt_sel = document.getElementById('advt_sel').value;
    var advtJson_sel = JSON.parse(advt_sel);
    var selId = advtJson_sel[0].conid.split('_');
    var selName = advtJson_sel[0].conname.split('_');
    var selHour = advtJson_sel[0].conhour.split(',');
    var selMinute = advtJson_sel[0].conminute.split(',');
    var selAdvt = advtJson_sel[0].advtid.split('_');
    for(l in selId){
        /*---create advt master obj---*/
        row_div = lib_createObj('row_div'+(parseInt(l)+1), 'div', "row-fluid") // row-fluid
        row_div_master = document.getElementById('row_div_master'); // master
        row_div_master.appendChild(row_div);
        /*---create advt select obj---*/
        var span5_div = lib_createObj(null, 'div', "span5") // span5
        var group_div = lib_createObj(null, 'div', "control-group") // control-group
        var control_div = lib_createObj(null, 'div', "controls") // controls
        var advt_label = lib_createObj(null, 'label', "control-label") // control-label
        advt_label.innerHTML = 'Advertising';
        var tmp = 'row_div'+(parseInt(l)+1);
        var advt_select = lib_createObj('con'+tmp, 'select', "my_select") // select
        advt_select.innerHTML = "";
        for(k in contentId){
            if(contentId[k]==selId[l]){
                advt_select.innerHTML += "<option value="+selId[l]+" selected>"+contentName[k]+"</option>";
            }
        }
        row_div.innerHTML = '';
        row_div.appendChild(span5_div); // <div class="row-fluid"><div class="span5">
        span5_div.appendChild(group_div); // <div class="control-group">
        group_div.appendChild(advt_label);  // <label></label>
        group_div.appendChild(control_div); //   <div class="controls">
        control_div.appendChild(advt_select); //   <select> </div></div></div></div>    
        /*---create time select obj---*/
        var span5_div = lib_createObj(null, 'div', "span5") // span5
        var group_div = lib_createObj(null, 'div', "control-group") // control-group
        var control_div = lib_createObj(null, 'div', "controls") // control_div
        var advt_label = lib_createObj(null, 'label', "control-label") // control-label
        advt_label.innerHTML = 'Start Time';
        var advtTime_div = lib_createObj('time'+tmp, 'div', null) // span5
        advtTime_div.style.marginLeft = "-8px";
        /*---add data to time select obj---*/
        row_div.appendChild(span5_div); //           <div class="row-fluid"><div class="span5">
        span5_div.appendChild(group_div); //           <div class="control-group">
        group_div.appendChild(advt_label);  //           <label></label>
        group_div.appendChild(control_div); //             <div class="controls">
        control_div.appendChild(advtTime_div); //            <div>
        advtTime_div.innerHTML = "";
        setHourSelect(advtTime_div, 'advtHour_select'+(parseInt(l)+1), advtJson[0].chtime.split(','), selHour[l]); // <select></select>
        setMinuteLoopSelect(advtTime_div, 'advtMin_select'+(parseInt(l)+1), selMinute[l]);                         // <select></select>   </div></div></div></div></div>
        /*---create check button obj---*/
        var span2_div = lib_createObj(null, 'div', "span2"); // span2
        var a_href = lib_createObj(null, 'a', "btn btn-info"); // a href
        a_href.setAttribute("onClick", "checkShowtime();");
        var i_icon = lib_createObj(null, 'i', "icon-search icon-white"); // i icon
        var btn_span = lib_createObj(null, 'span', null); // label
        btn_span.innerHTML = 'Check';

        var span = lib_createObj(null, 'span', null);
        span.innerHTML = '&nbsp';

        var a_del = lib_createObj((parseInt(l)+1), 'a', "btn btn-danger"); // a href
        a_del.setAttribute("onClick", "delAShowtime(this);");
        var i_del = lib_createObj(null, 'i', "icon-trash icon-white"); // i icon
        var btn_del = lib_createObj(null, 'span', null); // label

        row_div.appendChild(span2_div); // <div class="row-fluid"><div class="span2">
        span2_div.appendChild(a_href); //    <a>
        a_href.appendChild(i_icon); //         <i></i>
        a_href.appendChild(btn_span); //         <span></span>  </a></div></div>
        span2_div.appendChild(span);
        span2_div.appendChild(a_del);
        a_del.appendChild(i_del);
        a_del.appendChild(btn_del);
    }
}