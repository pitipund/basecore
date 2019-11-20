$(document).ready(function(){
    set_first();
});

function set_first(){
    if(action=='create'){
        obj_id = setLink_input('');
    }
    else{
        setLink_update();
    }
    if(isLive=='True'){
        document.getElementById('addBtn_div').className = "span2 hidden";
    }
    var html_obj = '<p class="form-control-static">'+document.getElementById('channel_hid').value+'</p>';
    $("#channel_id").append(html_obj);
}

function setLink_update(){
    var link =JSON.parse(document.getElementById('link_hid').value);
    for(var i=0; i<link.length; i++){
        obj_id = setLink_input(link[i].url);
        set_link_display(link[i].name, link[i].img, obj_id);
    }
}

function setLink_input(url){
    var isTrue = true;
    var i = 1;
    var container = $("#sort");
    while(isTrue){
        var tmp = 'link'+i;
        if(document.getElementById(tmp)){
            i += 1;
        }
        else{
            var html_obj = '<div id="link_div'+i+'" class="col-xs-12 col-sm-12 col-md-12 ui-state-default" style="cursor:move; margin-bottom:10px;">\
                    <div class="row">\
                        <div id="link_div_input'+i+'" style="padding:10px;">\
                            <input id="link'+i+'" class="form-control" type="text" value="'+url+'" onblur="check_url_type(this.value, this.id);"/>\
                            <input id="link'+i+'hid" type="hidden" value="'+url+'"/>\
                        </div>\
                        <div id="link_div_display'+i+'"></div>\
                    </div>\
                </div>';
            container.append(html_obj);
            isTrue = false;
        }
    }
    return i;
}

function check_url_type(url, obj_id){
    if(document.getElementById(obj_id+'hid').value != url){
        var url = url.replace(/ /g, '');
        if(url!=''){
            var spinbar = document.getElementById('spinnerbar');
            var spinner = new Spinner().spin();
            spinbar.appendChild(spinner.el);
            var id = String(obj_id).replace( /^\D+/g, '');
            document.getElementById('link'+id).value = url;
            var master = document.getElementById('link_div_input'+id);
            var y = /^(?:https?:\/\/)?(?:www\.)?youtube\.com\/watch\?(?=.*v=((\w|-){11}))(?:\S+)?$/;
            isYoutube = (url.match(y)) ? RegExp.$1 : false;
            var d = /^(?:https?:\/\/)?(?:www\.)?dailymotion\.com\/(embed\/video|video|hub)\/([^_]+)[^#]*(#video=([^_&]+))?/;
            isDailymotion = (url.match(d)) ? RegExp.$1 : false;
            var r = /(rtmp?:\/\/)?([^]*)/;
            isRtmp = (url.match(r)) ? RegExp.$1 : false;
            var m = /^(?:https?:\/\/)?([^]*)?.m3u8/;
            isM3u8 = (url.match(m)) ? RegExp.$1 : false;
            var t = /(rtsp?:\/\/)?([^]*)/;
            isRtsp = (url.match(t)) ? RegExp.$1 : false;
            master.className = master.className.replace("has-error", "");
            if(isYoutube != false){
                get_youtube(url, obj_id);
                document.getElementById(obj_id+'hid').value = url;
            }
            else if(isDailymotion != false){
                get_dailymotion(url, obj_id);
                document.getElementById(obj_id+'hid').value = url;
            }
            else if(isRtmp != false){
                set_link_display('', '', obj_id)
                document.getElementById(obj_id+'hid').value = url;
            }
            else if(isM3u8 != false){
                set_link_display('', '', obj_id)
                document.getElementById(obj_id+'hid').value = url;
            }
            else if(isRtsp != false){
                set_link_display('', '', obj_id)
                document.getElementById(obj_id+'hid').value = url;
            }
            else{
                alert(warning_support_text);
                linkElement = document.getElementById('link'+id);
                master.className = master.className+" has-error";
                linkElement.placeholder = document.getElementById('link'+id).value;
                linkElement.value = "";
            }
            spinner.stop();
        }
    }
}

function get_youtube(url, obj_id){
    var video_id = url.replace(/^[^v]+v.(.{11}).*/,"$1");
    $.ajax({
        url: 'http://gdata.youtube.com/feeds/api/videos/'+video_id+'?v=2&alt=json',
        dataType: "jsonp",
        cache: true,
        success: function(data){
            set_link_display(data.entry.title.$t, "http://img.youtube.com/vi/"+video_id+"/1.jpg", obj_id);
        }
    });
}

function get_dailymotion(url, obj_id){
    var video_id = url.split('/').pop();
    $.ajax({
        type: "GET",
        url:"https://api.dailymotion.com/video/" + encodeURIComponent(video_id) + "?fields=title,duration,user",
        dataType: "jsonp",
        cache: true,
        success: function(data){
            set_link_display(data.title, "http://www.dailymotion.com/thumbnail/video/"+video_id, obj_id);
        }
    });
}

function set_link_display(title, img, id){
    title = title.replace('"', "");
    var id = String(id).replace( /^\D+/g, '');
    container = $("#link_div_display"+id);
    if(document.getElementById('img'+id)){
        document.getElementById('img'+id).remove();
    }
    if(document.getElementById('label'+id)){
        document.getElementById('label'+id).remove();
    }
    var html_obj = '<div class="col-xs-12 col-sm-3 col-md-2" id="img'+id+'" style="padding-bottom:10px;padding-left:10px;margin-right:-5px;">\
                    <image src="'+img+'" style="width:100%"/>\
                </div>\
                <div class="col-xs-12 col-sm-9 col-md-10" id="label'+id+'" style="padding:0px;">\
                    <div class="form-group">\
                        <label class="col-xs-2 col-sm-2 col-md-1 control-label" style="padding-right:0px; padding-left:0px;">Title:</label>\
                        <div class="col-xs-10 col-sm-10 col-md-11" style="padding-right:20px;">\
                            <input id="name'+id+'" value="'+title+'" type="text" class="form-control"/>\
                        </div>\
                    </div>\
                </div>';
    container.append(html_obj);
}

function setTag_input(tagname){
    isTrue = true;
    i = 1;
    var master = document.getElementById('tag_div');
    while(isTrue){
        var tmp = 'tag'+i;
        if(document.getElementById(tmp)){
            i += 1;
        }
        else {
            var div = lib_createObj('div'+i, 'div', "input-group");
            div.style.paddingBottom = "5px";
            var tag = lib_createObj('tag'+i, 'input', 'form-control');
            tag.type = "text";
            tag.value = tagname;
            var btn = lib_createObj('remove'+i, 'a', 'input-group-btn btn btn-danger btn-sm');
            btn.innerHTML = remove_text;
            btn.setAttribute('onclick', 'setTag_remove('+i+')');
            master.appendChild(div);
            div.appendChild(tag);
            div.appendChild(btn);
            isTrue = false;
            $( "#tag"+i ).autocomplete({
                source: availableTags
            });
        }
    }
}

function setTag_remove(id){
    $('#tag'+id).remove();
    $('#remove'+id).remove();
    i=0;
    do{
        i++;
        target_id = id+i;
        nextelement = document.getElementById('tag'+target_id);
        nextremovebtn = document.getElementById('remove'+target_id);
        if(!nextelement)return;
        //update the rest of inputs
        nextelement.name = 'tag'+(target_id-1);
        nextelement.id = 'tag'+(target_id-1);
        nextremovebtn.setAttribute('onclick', 'setTag_remove('+(target_id-1)+")");
        nextremovebtn.id = 'remove'+(target_id-1);
    }while(nextelement)
}

function submit_playlist(){
    var spinbar = document.getElementById('spinnerbar');
    var sendBtn = document.getElementById('sendBtn');
    var cancelBtn = document.getElementById('cancelBtn');
    var spinner = new Spinner().spin();
    spinbar.appendChild(spinner.el);
    sendBtn.style.visibility = 'hidden';
    cancelBtn.style.visibility = 'hidden';
    var isSubmit = false;
    var elements = document.getElementById("sort").children;
    var list = [];
    var msg = dead_link_text;
    for(var i=0; i<elements.length; i++){
        index = String(elements[i].id).replace( /^\D+/g, '');
        if(document.getElementById('link'+index).value!=''){
            if((document.getElementById('name'+index)) && (document.getElementById('name'+index).value!='')){
                var obj = document.createElement("input");
                obj.type= "hidden";
                obj.name = "result"+i;
                obj.value = '[{'
                   +'"url": "'+document.getElementById('link'+index).value+'",'
                   +'"name": "'+document.getElementById('name'+index).value
                   +'"}]';
                document.getElementById('link_hid').appendChild(obj);
                isSubmit = true;
            }
            else{
                isSubmit = false;
                msg = insert_text;
                break;
            }
        }
    }
    if(isSubmit){
        document.forms['playlist_create_form'].submit();
    }
    else{
        alert(msg);
        var master = document.getElementById('link_div_input'+index);
        linkElement = document.getElementById('link'+index);
        master.className = master.className+" has-error";
        linkElement.placeholder = document.getElementById('link'+index).value;
        linkElement.value = "";
        sendBtn.style.visibility = '';
        cancelBtn.style.visibility = '';
        spinner.stop();
    }
}
