function pentaRemote_show_search(){
    var profile_dropdown = document.getElementById('profile_dropdown');
    if(document.getElementById('searchKey_input')){
        window.location.href = "#top";
        document.getElementById('searchKey_input').autofocus = "autofocus";
    }
    else{
        var profile_master = document.getElementById('profile_master');
        if((profile_master.className.search("in") != -1)
        &&(profile_dropdown.className.search("in") == -1)){ // dropdown open
            profile_master.className = "navbar-collapse bs-navbar-collapse collapse";
        }
        else{
            profile_master.className = "navbar-collapse bs-navbar-collapse in";
        }
    }
    if(parseInt(user_id)){ // not None
        var favorite_master = document.getElementById('favorite_master');
        var favorite_dropdown = document.getElementById('favorite_dropdown');
        favorite_master.className = "navbar-collapse2 bs-navbar-collapse collapse";
        favorite_dropdown.className = "navbar-collapse2 collapse";
    }
    profile_dropdown.className = "navbar-collapse2 collapse";
}

function pentaRemote_show_favorite(){
    var profile_master = document.getElementById('profile_master');
    var profile_dropdown = document.getElementById('profile_dropdown');
    if(parseInt(user_id)){ // not None
        var favorite_master = document.getElementById('favorite_master');
        var favorite_dropdown = document.getElementById('favorite_dropdown');
        if(favorite_master.className.search("in") != -1){ // dropdown open
            favorite_master.className = "navbar-collapse2 bs-navbar-collapse collapse";
            favorite_dropdown.className = "navbar-collapse2 collapse";
        }
        else{
            favorite_master.className = "navbar-collapse2 bs-navbar-collapse in";
            favorite_dropdown.className = "navbar-collapse2 in";
        }
    }
    else{
        alert(login_text);
    }
    profile_master.className = "navbar-collapse bs-navbar-collapse collapse";
    profile_dropdown.className = "navbar-collapse2 collapse";
}

function pentaRemote_show_profile(){
    var favorite_master = document.getElementById('favorite_master');
    var favorite_dropdown = document.getElementById('favorite_dropdown');
    var profile_master = document.getElementById('profile_master');
    var profile_dropdown = document.getElementById('profile_dropdown');
    var dropdown_islogin = document.getElementById('dropdown_islogin');
    var dropdown_unlogin = document.getElementById('dropdown_unlogin');
    if(profile_dropdown.className.search("in") != -1){ // dropdown open
        profile_master.className = "navbar-collapse bs-navbar-collapse collapse";
        profile_dropdown.className = "navbar-collapse2 collapse";
    }
    else{
        profile_master.className = "navbar-collapse bs-navbar-collapse in";
        profile_dropdown.className = "navbar-collapse2 in";
        if(parseInt(user_id)){ // not None
            favorite_master.className = "navbar-collapse2 bs-navbar-collapse collapse";
            favorite_dropdown.className = "navbar-collapse2 collapse";
            dropdown_islogin.className = "dropdown open";
        }
        else{
            dropdown_unlogin.className = "dropdown open";
        }
    }
}

function detectmob() { 
    if( navigator.userAgent.match(/Android/i)
    || navigator.userAgent.match(/webOS/i)
    || navigator.userAgent.match(/iPhone/i)
    || navigator.userAgent.match(/iPad/i)
    || navigator.userAgent.match(/iPod/i)
    || navigator.userAgent.match(/BlackBerry/i)
    || navigator.userAgent.match(/Windows Phone/i)
    ){
        return true;
    }
    else {
        return false;
    }
}

function set_enableBtn(checkbox, deleteBtn) {
    var checkbox = document.getElementsByName(checkbox);
    var deleteBtn = document.getElementById(deleteBtn);
    for (var i=0; i<checkbox.length; i++) {
        if (checkbox[i].checked) {
            deleteBtn.className = 'btn btn-danger';
            break;
        }
        else{
            deleteBtn.className = 'btn btn-danger disabled';
        }
    }
}

function set_checkAll(all, checkone) {
    var all = document.getElementById(all);
    var checkone = document.getElementsByName(checkone);
    if (all.checked) {
        for (var i=0; i<checkone.length; i++) {
            checkone[i].checked = true;
        }
    }
    else {
        for (var i=0; i<checkone.length; i++) {
            checkone[i].checked = false;
        }
    }  
}

function set_spinnerbar(spinbar, btnList){
    var spinbar = document.getElementById(spinbar);
    var spinner = new Spinner().spin();
    spinbar.appendChild(spinner.el);
    for(i=0 ; i<btnList.length ; i++){
        var btn = document.getElementById(btnList[i]);
        btn.setAttribute('disabled','disabled');
        btn.href = "#";
    }
}

function set_spinner(spinbar, sendBtn, cancelBtn){
    var spinbar = document.getElementById(spinbar);
    var sendBtn = document.getElementById(sendBtn);
    var cancelBtn = document.getElementById(cancelBtn);
    var spinner = new Spinner().spin();
    spinbar.appendChild(spinner.el);
    sendBtn.className = 'btn btn-primary disabled';
    cancelBtn.className = 'btn btn-default disabled';
    sendBtn.href = "#";
    cancelBtn.href = "#";
}

function get_deleteID(title, checkboxes, delete_link, list_link){
    var checkboxes = document.getElementsByName(checkboxes);
    var isFirst = true;
    for (var i=0; i<checkboxes.length; i++) {
        if (checkboxes[i].checked) {
            if(isFirst){
                isCheck = checkboxes[i].value;
                isFirst = false;
            }
            else{
                isCheck += '_'+checkboxes[i].value;
            }
        }
    }
    if(isFirst){
        alert('Please select the '+title+' first.');
    }
    else{
        confirmMsg = confirm('Are you sure you want to delete '+title+'?');
        if(confirmMsg){
            delete_link = delete_link.replace('ling', isCheck);
            location.href = delete_link;
        }
        else{
            location.href = list_link;
        }
    }
}

function lib_createObj(idobj, typeobj, classobj){
    var obj = document.createElement(typeobj);    
    if(idobj!=null){
        obj.id = idobj;
        obj.name = idobj;
    }
    if(classobj!=null){
        obj.className = classobj;
    }
    return obj;
}

function set_detail_slice(id){
    isHidden = id.className.split('hidden');
    if(isHidden.length == 1){
        id.className = isHidden[0]+" hidden";
        document.getElementById(id.id+"More").className = "col-xs-12 col-sm-12 col-md-12";
    }
    else{
        id.className = isHidden[0];
        document.getElementById(id.id+"More").className = "col-xs-12 col-sm-12 col-md-12 hidden";
    }
}

function set_detail(id){
    isHidden = id.className.split('hidden');
    if(isHidden.length == 1){
        id.className = isHidden[0]+" hidden";
        document.getElementById(id.id+"Btn").innerHTML = "<span class='glyphicon glyphicon-resize-full'></span>"+more_text;
    }
    else{
        id.className = isHidden[0];
        document.getElementById(id.id+"Btn").innerHTML = "<span class='glyphicon glyphicon-resize-small'></span>"+hide_text;
    }
}

function set_createBtn(){
    var btn_div = document.getElementById('add_btn_master'); // master
    btn_div.className = "";
    btn_div.innerHTML = "";
    var a_href = lib_createObj(null, 'a', "btn btn-warning"); // a href
    a_href.setAttribute("onClick", "createAdvertisingObj();");
    var i_icon = lib_createObj(null, 'i', "icon-white icon-plus"); // i icon
    var btn_span = lib_createObj(null, 'span', null); // label
    btn_span.innerHTML = 'Add advertising';
    btn_div.appendChild(a_href); // <div><a>
    a_href.appendChild(i_icon);  //   <i></i>
    a_href.appendChild(btn_span); //    <span></span></a></div>
}

function set_urlName(url, event, pType){
    document.getElementById('urlName_p').innerHTML = "http://pentachannel.com/"+url.value + String.fromCharCode(event.keyCode)+"/"+pType+"/" ;
}

function set_channelUrlName(url, event){
    document.getElementById('urlName_p').innerHTML = "http://pentachannel.com/"+url.value;
}

function createAdvertisingObj() {
    document.getElementById("noSendBtn").className = "btn btn-primary disabled";
    document.getElementById("sendBtn").className = "btn btn-primary hidden";
    document.getElementById('add_btn_master').className = "hidden";
    /*---find id for advt select and time select---*/
    var isTrue = true;
    var i = 1;
    while(isTrue){
        var tmp = 'row_div'+i;
        if(document.getElementById(tmp)){
            i += 1;
        }
        else{
            isTrue = false;
        }
    }
    /*---create advt master obj---*/
    row_div = lib_createObj('row_div'+i, 'div', "row-fluid") // row-fluid
    row_div_master = document.getElementById('row_div_master'); // master
    row_div_master.appendChild(row_div);
    /*---create advt select obj---*/
    var span5_div = lib_createObj(null, 'div', "span5") // span5
    var group_div = lib_createObj(null, 'div', "control-group") // control-group
    var control_div = lib_createObj(null, 'div', "controls") // controls
    var advt_label = lib_createObj(null, 'label', "control-label") // control-label
    advt_label.innerHTML = 'Advertising';
    var advt_select = lib_createObj('con'+tmp, 'select', "my_select") // select
    advt_select.innerHTML = "";
    /*---add data to advt select obj---*/
    advt = document.getElementById('advt').value;
    var advtJson = JSON.parse(advt);
    var contentId = advtJson[0].conid.split('_');
    var contentName = advtJson[0].conname.split('_');
    for(j in contentId){
        advt_select.innerHTML += "<option value="+contentId[j]+">"+contentName[j]+"</option>";
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
    row_div.appendChild(span5_div); //                                            <div class="row-fluid"><div class="span5">
    span5_div.appendChild(group_div); //                                            <div class="control-group">
    group_div.appendChild(advt_label);  //                                            <label></label>
    group_div.appendChild(control_div); //                                              <div class="controls">
    control_div.appendChild(advtTime_div); //                                             <div>
    advtTime_div.innerHTML = "";
    setHourSelect(advtTime_div, 'advtHour_select'+i, advtJson[0].chtime.split(','), ''); // <select></select>
    setMinuteLoopSelect(advtTime_div, 'advtMin_select'+i, '');                           // <select></select>   </div></div></div></div></div>
    /*---create check button obj---*/
    var span2_div = lib_createObj(null, 'div', "span2") // span2
    var a_href = lib_createObj(null, 'a', "btn btn-info") // a href
    a_href.setAttribute("onClick", "checkShowtime();");
    var i_icon = lib_createObj(null, 'i', "icon-search icon-white") // i icon
    var btn_span = lib_createObj(null, 'span', null) // label
    btn_span.innerHTML = 'Check';
    row_div.appendChild(span2_div); // <div class="row-fluid"><div class="span2">
    span2_div.appendChild(a_href); //    <a>
    a_href.appendChild(i_icon); //         <i></i>
    a_href.appendChild(btn_span); //         <span></span>  </a></div></div>
}
