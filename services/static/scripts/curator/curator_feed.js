function post_playlist(){
    var post_text = document.getElementById('post_text').value;
    var exp = /(\b(https?|ftp|file):\/\/[-A-Z0-9+&@#\/%?=~_|!:,.;]*[-A-Z0-9+&@#\/%=~_|])/ig;
    var link = post_text.match(exp);
    if(link == null){
        alert(nolink_text);
    }
    else{
        linkList = []
        for(var i=0; i<link.length; i++){
            if((link[i].match(/youtube.com/gi) != null) || (link[i].match(/dailymotion.com/gi) != null)){ //|| (link[i].match(/vimeo.com/gi) != null)){
                linkList.push(link[i]);
            }
        }
        if(linkList.length > 0){
            var detail = post_text;
            for(i=0; i<linkList.length; i++){
                detail = detail.replace(linkList[i], '');
            }
            document.getElementById('detail_hidden').value = detail;
            document.getElementById('link_hidden').value = linkList;
            set_spinnerbar('spinnerbar', ['post_playlistBtn']);
            document.forms['post_playlist_form'].submit();
        }
        else{
            alert(warning_text);
        }
    }
}

var stop_running = false;

$(document).ready(function(){
    showload(true);
    setTimeout(function(){ 
        updateBox(); 
    }, 0);
});

$(window).scroll(function(){
    if($(window).scrollTop() + $(window).height() == $(document).height()) {
        if(!stop_running){
            updateBox();
        }
    }
});

function isScrollable(){
    var hContent = $("body").height(); // get the height of your content
    var hWindow = $(window).height();  // get the height of the visitor's browser window
    if(hContent>hWindow){ 
        return true;    
    }
    return false;
}

function showload(isshow){
    element = $('#loadingmsg');
    if(isshow){
        element.show();
    }
    else{
        element.hide();
    }
}

function showNomore(isshow){
    element = $('#nomoremsg');
    if(isshow){
        element.show();
    }
    else{
        element.hide();
    }
}

function updateBox(){
    stop_running = true;
    if(next_page<max_page){
        showload(true);
        var jqxhr = $.get(getIndex_url+"?page="+next_page, function(data){
            showload(false);
            if(data.status==1){
                next_page = data.pagenumber;
                createBox(data.data, data.myChannel);
                stop_running = false;
                if(data.data.length==0){//no more data
                    showNomore(true);
                    return;
                }
            }
        });
    }
}

var current_index=0;
function createBox(data, myChannel){
    var container = $("#container");
    for(i=0;i<data.length;i++){
        var playlistImg = "";
        for(pImg in data[i]['playlist']){
            if(pImg==0)
                continue;
            playlistImg += '<a onclick="play_video('+"'"+data[i]['id']+"', "+"'"+data[i]['playlist'][pImg]['video_id']+"', "+"'"+data[i]['playlist'][pImg]['video_type']+"'"+')">\
                <image src="'+data[i]['playlist'][pImg]['thumbnail']+'" style="width:20%; height:90%; margin-top:5px;" title="'+data[i]['playlist'][pImg]['name']+'"/></a>';
        }
        var favoriteImg = "";
        var channelBtn = "";
        var favoriteTitle = "";
        for(favorite in data[i]['favorite']){
            var favoriteUrl = favorite_url.replace("favoriteUrl", data[i]['favorite'][favorite]['url']);
            favoriteImg += '<a href="'+favoriteUrl+'"><image src="'+data[i]['favorite'][favorite]['img']+'" class="img-rounded" style="width:50%; margin:5px 0px 0px 10px; padding-left:0px;" title="'+data[i]['favorite'][favorite]['name']+'"/></a>';
        }

        if(data[i]['favorite'].length>0)
        {
            favoriteTitle = '<p class="text-info" style="margin-left:10px;">People who also shared this:</p>';
        }

        if(myChannel.length>0){
            myChannelBtn = '<div class="btn-group pull-right" style="margin-left:10px;">\
                                    <a class="btn btn-sm btn-info dropdown-toggle " data-toggle="dropdown">\
                                        <span class="glyphicon glyphicon-floppy-disk"></span> '+save_channel_text+'<span class="caret"></span>\
                                    </a>\
                                    <ul class="dropdown-menu" role="menu">';
            if(data[i]['id'].toString().indexOf("facebook_")>-1){
                for(j=0;j<myChannel.length;j++){
                    var saveChannelUrl = saveFacebook_url.replace("channelid", myChannel[j]['id'])+"?videotype="+data[i]["playlist"][0]["video_type"]+"&videoid="+data[i]["playlist"][0]["video_id"];
                    myChannelBtn += '<li><a href="'+saveChannelUrl+'">'+myChannel[j]['name']+'</a></li>';
                }
            }
            else{
                for(j=0;j<myChannel.length;j++){
                    var saveChannelUrl = saveChannel_url.replace("channelid", myChannel[j]['id']);
                    var saveChannelUrl = saveChannelUrl.replace("playlistid", data[i]['id']);
                    myChannelBtn += '<li><a href="'+saveChannelUrl+'">'+myChannel[j]['name']+'</a></li>';
                }
            }
            myChannelBtn += '</ul></div>';
        }
        else{
            myChannelBtn = "";
        }
        var ownerUrl = owner_url.replace("ownerUrl", data[i]['owner'][0]['url']);
        var html_object = '<div class="col-xs-12 col-sm-12 col-md-12" style="margin-bottom:0px; padding:10px 0px 0px 0px;">\
                <div class="alert alert-result" style="padding:10px;">\
                    <div class="row" style="margin-left:0px; margin-right:0px;">\
                        <div class="col-sm-9 col-md-9 col-lg-9" style="margin:0px; padding:0px;">\
                            <h4>'+data[i]['name']+'</h4>\
                        </div>\
                        <div class="col-md-3 col-lg-3" style="margin:0px; padding:0px;">\
                            '+myChannelBtn+'\
                        </div>\
                    </div>\
                    <div class="row" style="margin-left:0px; margin-right:0px;">\
                        <div class="col-sm-9 col-md-9 col-lg-9" style="margin:0px; padding:0px;">\
                            <div id="video-container" class="video-container" style="background-color:#000; background-image:url('+data[i]['thumbnail']['thumbnail']+'); background-repeat:no-repeat; background-size:cover" title="'+data[i]['thumbnail']['name']+'">\
                                <div id="div'+data[i]['id']+'"></div>\
                                <a id="play_btn'+data[i]['id']+'" class="btn btn-danger btn-lg" onclick="play_video('+"'"+data[i]['id']+"', "+"'"+data[i]['thumbnail']['video_id']+"', "+"'"+data[i]['thumbnail']['video_type']+"'"+')" style="position:absolute; top:45%; left:45%;">\
                                    <span class="glyphicon glyphicon-play"></span>\
                                </a>\
                            </div>\
                            <div style="height:100px; overflow:auto; white-space:nowrap;">\
                                '+playlistImg+'\
                            </div>\
                        </div>\
                        <div class="col-md-3 col-lg-3" style="margin:0px; padding:0px; background-color:#dff5ff;">\
                            <div class="row" style="margin:0px; padding:0px;">\
                                <div class="col-md-12 col-lg-12">\
                                    <a href="'+ownerUrl+'">\
                                        <image src="'+data[i]['owner'][0]['img']+'" class="img-circle" style="width:90%; margin:10px 10px 10px; padding-left:0px;" title="'+data[i]['owner'][0]['name']+'"/>\
                                    </a>\
                                </div>\
                            </div>\
                            <div class="row" style="margin:0px; padding:0px;">\
                                '+favoriteTitle+'\
                                <div class="col-md-12 col-lg-12" style="margin:0px; padding:0px; height:300px; overflow-y:auto;">\
                                    '+favoriteImg+'\
                                </div>\
                            </div>\
                        </div>\
                    </div>\
                    <div class="row">\
                        <div class="col-xs-12 col-sm-12 col-md-12">\
                        </div>\
                    </div>\
                </div>\
            </div><!-- end col-xs-12 col-sm-12 col-md-12 -->';
        container.append(html_object);
    }
}

function play_video(id, video_id, video_type){
    if(document.getElementById('iframe_div'+id)){
        var elem = document.getElementById('iframe_div'+id);
        elem.parentNode.removeChild(elem)
    }
    var container = $("#div"+id);
    container.append('<div id="iframe_div'+id+'"></div>');
    if(video_type=='Y'){
        player = new YT.Player('iframe_div'+id, {
            videoId: video_id,
            events: {
                'onReady': onPlayerReady
            }
        });
        function onPlayerReady(event) {
            event.target.playVideo();
        }
    }
    else if(video_type=='D'){
        var params = { allowScriptAccess: "always" };
        (function(){
            var e = document.createElement('script'); e.async = true;
            e.src =  'http://api.dmcdn.net/all.js';
            var s = document.getElementsByTagName('script')[0]; s.parentNode.insertBefore(e, s);
        }());
        window.dmAsyncInit = function(){
            var player = DM.player('iframe_div'+id, {video: video_id,  params: params});
            player.addEventListener("apiready", function(e){
                player_dailymotion = e.target;
                e.target.play();
            });
        };
    }
    else if(video_type=='F'){
        ifrm = document.createElement("IFRAME");
        ifrm.setAttribute("src", "https://www.facebook.com/video/embed?video_id="+video_id);
        ifrm.style.width = "100%";
        document.getElementById('iframe_div'+id).appendChild(ifrm);
    }
    document.getElementById('play_btn'+id).style.visibility = 'hidden';
}