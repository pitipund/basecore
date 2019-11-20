function create_link_input(){
    var isTrue = true;
    var i = 1;
    var container = $("#link_container");
    while(isTrue){
        var tmp = 'video_link'+i;
        if(document.getElementById(tmp)){
            i += 1;
        }
        else{
            var html_obj = '<div id="link_div'+i+'" class="form-group" style="margin:0px; padding-bottom: 20px;">\
                                <label class="col-xs-4 col-sm-3 col-md-2 control-label">ลิงค์:</label>\
                                <div class="col-xs-8 col-sm-9 col-md-10" style="padding:0px;">\
                                    <input id="video_link'+i+'" name="video_link'+i+'" onblur="validate_link('+i+');" class="form-control" style="margin-bottom:5px;"/>\
                                </div>\
                            </div>';
            container.append(html_obj);
            isTrue = false;
        }
    }
}

function toggleEditMode(sender){
    var trashbtn = $('.editmodebtn')
    var a = trashbtn.css("visibility");
    if(a=="visible"){
        trashbtn.fadeTo(300,0.0, function(){
            trashbtn.css("visibility","hidden");
        });
        if(sender!=undefined){
            $(sender).html("<span class='glyphicon glyphicon-pencil'>Edit</span>");
        }
    }
    else{
        trashbtn.css("visibility","visible");
        trashbtn.fadeTo(300,1.0);
        if(sender!=undefined){
            $(sender).html("Done");
        }
    }
}

function showPopUp(){
    var dlg = document.getElementById('create_video_dialog');
    dlg.style.display = "block";
}

function closePopUp(){
    var dlg = document.getElementById('create_video_dialog');
    dlg.style.display = "none";
    document.body.style.overflowY = "scroll";
    var isTrue = true;
    var i = 2;
    document.getElementById('link_div1').className = 'form-group';
    document.getElementById('video_link1').value = '';
    document.getElementById('video_link1').placeholder = '';
    if(document.getElementById('video_name1')){
        document.getElementById('video_label1').remove();
        document.getElementById('video_name1').remove();
    }
    while(isTrue){
        var tmp = 'link_div'+i;
        if(document.getElementById(tmp)){
            document.getElementById(tmp).remove();
            i += 1;
        }
        else{
            isTrue = false;
        }
    }
}

function validate_link(id){
    var master = document.getElementById('link_div'+id);
    var textInput = document.getElementById('video_link'+id);
    if(textInput.value!=''){
        var y = /^(?:https?:\/\/)?(?:www\.)?youtube\.com\/watch\?(?=.*v=((\w|-){11}))(?:\S+)?$/;
        isYoutube = (textInput.value.match(y)) ? RegExp.$1 : false;
        var d = /^(?:https?:\/\/)?(?:www\.)?dailymotion\.com\/(embed\/video|video|hub)\/([^_]+)[^#]*(#video=([^_&]+))?/;
        isDailymotion = (textInput.value.match(d)) ? RegExp.$1 : false;
        master.className = master.className.replace("has-error", "");
        if(isYoutube == false && isDailymotion == false){
            if(channel_isLive=='False'){
                master.className = master.className+" has-error";
                textInput.placeholder = textInput.value;
                textInput.value = "";
            }
            else if(channel_isLive=='True'){
                var r = /(rtmp?:\/\/)?([^]*)/;
                isRtmp = (textInput.value.match(r)) ? RegExp.$1 : false;
                var m = /^(?:https?:\/\/)?([^]*)?.m3u8/;
                isM3u8 = (textInput.value.match(m)) ? RegExp.$1 : false;
                var t = /(rtsp?:\/\/)?([^]*)/;
                isRtsp = (textInput.value.match(t)) ? RegExp.$1 : false;
                if((isM3u8 == false) && (isRtmp == false) && (isRtsp == false)){
                    master.className = master.className+" has-error";
                    textInput.placeholder = textInput.value;
                    textInput.value = "";
                }
                else{
                    if(!document.getElementById('video_name'+id)){
                        var html_obj = '<label id="video_label'+id+'" class="col-xs-4 col-sm-3 col-md-2 control-label">ชื่อ:</label>\
                                <div class="col-xs-8 col-sm-9 col-md-10" style="padding:0px;">\
                                    <input id="video_name'+id+'" name="video_name'+id+'" class="form-control" style="margin-bottom:5px;"/>\
                                </div>';
                        $('#link_div'+id).append(html_obj);
                    }
                }
            }
        }
        else{
            if(document.getElementById('video_name'+id)){
                document.getElementById('video_name'+id).remove();
                document.getElementById('video_label'+id).remove();
            }
        }
    }
}

function post_create_video(){
    var spinbar = document.getElementById('create_spinnerbar');
    var spinner = new Spinner().spin();
    spinbar.appendChild(spinner.el);
    var postData = $("#create_video_form").serializeArray();
    var formURL =  $("#create_video_form").attr("action");
    var channel_id = $("#channelId_hid").attr("value");
    $.ajax({
        url : formURL,
        type: "POST",
        data : postData,
        success:function(data){
            alert(data.message);
            spinner.stop();
            closePopUp();
            $.event.trigger({type: "videoChanged",channel_id:channel_id});
        }
    });
}

function delete_video(id,channel_id){
    confirmMsg = confirm(confirm_delete_video_text);
    if(confirmMsg){
        var spinbar = document.getElementById('del_spinnerbar');
        var spinner = new Spinner().spin();
        spinbar.appendChild(spinner.el);
        var del_video = DELETE_VIDEO_URL.replace('videoId', id);
        $.get(del_video, function(data) {
            alert(data.message);
            $.event.trigger({type: "videoChanged",channel_id:channel_id});
            spinner.stop();
        });
    }
}

function edit_video(pid, uid){
    var edit_playlist = EDIT_PLAYLIST_URL.replace('user_id', uid);
    edit_playlist = EDIT_PLAYLIST_URL.replace('playlist_id', pid);
    location.href = edit_playlist;
}

// function playOrQueue(btn, id, action){ //id:playlist id  //play on Penta, add to queue
//     if(detectmob()){
//         var currentvid = '';
//         $.get("/curatorPlayOrQueue/"+id+"/", function(data) {
//             if(data.status == 'true'){
//                 var linkType = "";
//                 for(i=0;i<data.resultType.length;i++){
//                     if(i==0){
//                         if(data.resultType[i] == 'Y'){
//                             var url = "penta://youtube?1="+data.resultId[i];
//                             linkType = "Y";
//                         }
//                         else if(data.resultType[i] == 'D'){
//                             var url = "penta://dailymotion?1="+data.resultId[i];
//                             linkType = "D";
//                         }
//                     }
//                     else{
//                         if(data.resultType[i] == linkType){
//                             url += "&"+(i+1)+"="+data.resultId[i];
//                         }
//                         else{
//                             break;
//                         }
//                     }
//                     if(data.resultId[i]==currentvid_videoid){
//                         currentvid = data.resultId[i];
//                     }
//                 }
//                 if(action == 'play'){
//                     if(currentvid!=''){
//                         url += "&current="+currentvid;
//                     }
//                     else{
//                         url += "&current="+data.resultId[0];//+"&title="+data.ptitle;// $('#timelineModal').modal('hide');
//                     }
//                 }
//                 location.href = url;
//                 btn.innerHTML = added_text;
//                 btn.className = btn.className+" disabled";
//             }
//             else{
//                 if(action == "add to queue"){
//                     action_text = queue_text;
//                 }
//                 else{
//                     action_text = play_text;
//                 }
//                 alert(cant_text+action_text);
//             }
//         });
//     }
// }
