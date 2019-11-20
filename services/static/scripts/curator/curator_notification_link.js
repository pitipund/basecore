function check_url_type(url, obj_id){
    if(document.getElementById('url_hid'+obj_id).value != url){
        var url = url.replace(/ /g, '');
        if(url!=''){
            var spinbar = document.getElementById('spinnerbar');
            var spinner = new Spinner().spin();
            spinbar.appendChild(spinner.el);
            var master = document.getElementById('div_url_'+obj_id);
            var y = /^(?:https?:\/\/)?(?:www\.)?youtube\.com\/watch\?(?=.*v=((\w|-){11}))(?:\S+)?$/;
            isYoutube = (url.match(y)) ? RegExp.$1 : false;
            var d = /^(?:https?:\/\/)?(?:www\.)?dailymotion\.com\/(embed\/video|video|hub)\/([^_]+)[^#]*(#video=([^_&]+))?/;
            isDailymotion = (url.match(d)) ? RegExp.$1 : false;
            master.className = master.className.replace("has-error", "");
            if(isYoutube != false){
                get_youtube(url, obj_id);
                document.getElementById('url_hid'+obj_id).value = url;
            }
            else if(isDailymotion != false){
                get_dailymotion(url, obj_id);
                document.getElementById('url_hid'+obj_id).value = url;
            }
            else{
                alert(warning_support_text);
                linkElement = document.getElementById('url_'+obj_id);
                master.className = master.className+" has-error";
                linkElement.placeholder = document.getElementById('url_'+obj_id).value;
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

function set_link_display(title, img, obj_id){
    document.getElementById('img_'+obj_id).src = img;
    document.getElementById('name_'+obj_id).value = title;
}

function submit_link(){
    var spinbar = document.getElementById('spinnerbar');
    var sendBtn = document.getElementById('submitBtn');
    var cancelBtn = document.getElementById('cancelBtn');
    var spinner = new Spinner().spin();
    spinbar.appendChild(spinner.el);
    sendBtn.style.visibility = 'hidden';
    cancelBtn.style.visibility = 'hidden';
    var elements = document.getElementById("master").children;
    var list = [];
    var isSubmit = true;
    for(var i=0; i<elements.length; i++){
        index = String(elements[i].id).replace( /^\D+/g, '');
        if(document.getElementById('url_'+index)){
            if(document.getElementById('url_'+index).value!=''){
                if((document.getElementById('name_'+index)) && (document.getElementById('name_'+index).value!='')){
                    var obj = document.createElement("input");
                    obj.type= "hidden";
                    obj.name = "result"+index;
                    obj.value = '[{'
                       +'"url": "'+document.getElementById('url_'+index).value+'",'
                       +'"name": "'+document.getElementById('name_'+index).value.replace(/["]/g, "'")+'",'
                       +'"id": "'+document.getElementById('id_hid'+index).value
                       +'"}]';
                    document.getElementById('result').appendChild(obj);
                }
                else{
                    isSubmit = false;
                    break;
                }
            }
        }
    }
    if(isSubmit){
        document.forms['notification_edit_form'].submit();
    }
    else{
        alert(dead_link_text);
        var master = document.getElementById('div_url_'+index);
        linkElement = document.getElementById('url_'+index);
        master.className = master.className+" has-error";
        linkElement.placeholder = document.getElementById('url_'+index).value;
        linkElement.value = "";
        sendBtn.style.visibility = '';
        cancelBtn.style.visibility = '';
        spinner.stop();
    }
}