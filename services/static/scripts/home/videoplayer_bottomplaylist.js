var IS_INIT = false;
var currentChannelURL = "";
var videoPlayerAutoPlay = false;

function autoResizeDiv(){
    var screenHeight = window.innerHeight;
    var screenWidth = window.innerWidth;
    var playlistHeight = document.getElementById('bottom_playlist').style.height;
    if(screenWidth>screenHeight){ // Landscape
        document.getElementById('bottom_playlist').style.height = (screenHeight*0.15) +'px';
        document.getElementById('video-container').style.height = (screenHeight*0.7)-80 +'px';
    }
    else{ // Portrait
        document.getElementById('bottom_playlist').style.height = (screenHeight*0.2) +'px';
        document.getElementById('video-container').style.height = (screenHeight*0.5)-80 +'px';
    }
}

function Model(GET_TAGS_URL){
    this.GET_TAGS_URL = GET_TAGS_URL;
    this.getTags = function(callback){
        $.get(GET_TAGS_URL, function(result){
            callback(result);
        });
    }
}

function select_channel(url){
    var a = new Model(url);
    a.getTags(restsuccess);
}

function select_channel_id(channel_id){
    var url = REST_ALL_VIDEO_URL+channel_id;
    if(current != ''){
        url += '?current='+current;
    }
    select_channel(url);
}

function restsuccess(result){
    document.getElementById('create_h4').innerHTML = create_video_for_text+" "+channel_name;
    document.getElementById('channelId_hid').value = result.channel_id;
    updateOwnerTitle(result.owner_name, result.owner_id);

    $("li.mychannel > a.mychannel_item").each(function(){
        $(this).children("span").each(function(index){
            $(this).css("visibility","hidden");
        });
    });

   if(result.isOwner == true){
        $("li.mychannel.active > a.mychannel_item").each(function(){
            $(this).children("span").each(function(index){
                $(this).css("visibility","visible");
            });
        });
    }

    if(result.videos.length==0){
        if(document.getElementById('iframe_div')){
            var elem = document.getElementById('iframe_div');
            elem.parentNode.removeChild(elem)
        }
        //////
        $("#video-container").hide();
        $("#bottom_playlist").hide();
        $("#video_message").show();
        return;
    }
    else{
        $("#video-container").show();
        $("#bottom_playlist").show();
        $("#video_message").hide();
    }
    var first_video;
    var pinned_index = 0;
    for(index in result.videos){
        if(result.videos[index].isPinned==true){
            first_video = result.videos[index]; // find Pinned Index
            pinned_index = index;
            break;
        }
    }
    if(first_video==undefined){
        first_video = result.videos[0]; // Pinned index not found
    }
    if(!IS_INIT){
        videoPlayer = new VideoPlayer(first_video.video_id, first_video.video_type,first_video.thumbnail_url, pinned_index);
        videoPlayer.updatePlaylist(result, pinned_index);
        IS_INIT = true;
        if(videoPlayerAutoPlay)
            videoPlayer.autoPlay(500,pinned_index);
    }
    else{
       videoPlayer.updatePlaylist(result, pinned_index);
       videoPlayer._playVideo(first_video);
       $("a#pl_"+first_video.id).children("img").attr('id', 'selectItem');
    }
}

function updateVideoPlayerTitle(newtitle){
    if($("#videoplayer_title")!=undefined){
        $("#videoplayer_title").text(newtitle);
    }
}

function updateOwnerTitle(name, url){
    $("#owner_title").text('');
    var profile_url = PROFILE_URL.replace('user_url', url);
    var htmlObj = '<a href="'+profile_url+'" '+url+' %}">'+by_text+' '+name+'</a>';
    $("#owner_title").append(htmlObj);
}

function getRTSPPlayer(url, width, height) {
    // this should work on OSX
    var player = '<embed ';
    player += ' type="application/x-mplayer2"';
    player += ' pluginspage="http://www.microsoft.com/Windows/MediaPlayer/"';
    player += ' name="mediaplayer1"';
    player += ' ShowStatusBar="true"';
    player += ' EnableContextMenu="false"';
    player += ' autostart="true"';
    player += ' loop="false"';
    player += ' src="' + url + '"';
    player += ' width="' + width + 'px"';
    player += ' height="' + height + 'px">';
    player += '<font color="white">Could not find plugin to play this type of video.</font></embed>';
    return player;
}

function VideoPlayer(video_id, video_type, thumbnail_url, pinned_index){
    var self = this;
    self.currentPlaylist = [];
    self.playingIndex = 0;
    this.initPlayer = function (id, type, url, pin){
        $("#play_btn").click(function(){
            if(pin)
                self._playOnSelectIndex(pin);
            else
                self._playOnSelectIndex(0);
        });
    }
    this.initPlayer(video_id,video_type, thumbnail_url, pinned_index);
    this.updateVideoThumbnail = function (imageURL){
        $("#video-container").css("backgroundImage", "url('"+imageURL+"')");
    }
    self.updateVideoThumbnail(thumbnail_url);
    this.updatePlaylist = function (result,pinned_index){
        channel_id = result.channel_id;
        var playlistWidth = (165.0*result.videos.length)+"px";
        $('#bottom_playlist').width(playlistWidth);
        videos = result.videos;
        self.currentPlaylist = videos;
        self.playingIndex = pinned_index;
        var container = $("#bottom_playlist");
        container.empty();
        var del_btn = '';
        if(result.isOwner == true){
            del_btn = '\
            <p class="pull-right" style="position:absolute; top:0px; right:0px; padding-top:5px;">\
                <a onclick="edit_video('+"'{{playlist_id}}'"+",'"+user_id+"'"+')" class="btn btn-warning editmodebtn" style="padding:5px;">\
                    <span class="glyphicon glyphicon-pencil"></span>\
                </a>\
                <a onclick="delete_video('+"'{{id}}'"+','+channel_id+')" class="btn btn-danger editmodebtn" style="padding:5px;">\
                    <span class="glyphicon glyphicon-trash"></span>\
                </a>\
            </p>';
        }
        var template = '{{#videos}}\
                <div style="position:relative; height:100%; width:160px; margin-right:5px; float:left;">\
                    <a id="pl_{{id}}">\
                        <image class="playlist_image" src="{{thumbnail_url}}" style="width:100%; height:90%; margin-top:5px;" title="{{name}}" name="{{id}}"/>\
                        <input type="hidden" value="{{playlist_id}}"/>\
                    </a>\
                    <div class="text_box">{{name}}</div>\
                    '+del_btn+'\
                </div>\
            {{/videos}}'
        var context = {videos:videos};
        var html = Mustache.render(template, context);
        container.html(html);
        container.children("div").each(function(index){
            var video = videos[index];
            $(this).click(function(){
                $("a > img#selectItem").removeAttr("id");
                videoPlayer._playOnSelectIndex(index);
            });
        });
    }
    this._playVideo = function (video){
        var id = video.id;
        var video_id = video.video_id;
        var video_type = video.video_type;
        var thumbnail_url = video.thumbnail_url;
        updateVideoPlayerTitle(video.name);
        var url = SAVE_LINK_LOG_URL.replace('link_id', id);
        $.get(url, function(data){
            console.log(data);
        });
        self.highlightPlayingItem(id);
        if(thumbnail_url!=undefined){
            this.updateVideoThumbnail(thumbnail_url);
        }
        if(document.getElementById('iframe_div')){
            var elem = document.getElementById('iframe_div');
            elem.parentNode.removeChild(elem)
        }
        history.pushState('', '', '?current='+$('#selectItem').parent().children('input')[0].value);
        document.title = channel_name+' -- '+document.getElementById('selectItem').title+' | ดูรายการโปรดตอนล่าสุด ง่ายๆแค่คลิกเดียว | Penta Channel';
        var container = $("#div_container");
        container.append('<div id="iframe_div"></div>');
        if(video_type=='Y'){
            function onPlayerReady(event){
                userAgent = window.navigator.userAgent;
                if(/iP(hone|od|ad)/.test(userAgent)==false&&/Android/.test(userAgent)==false) {
                  event.target.playVideo();
                }
            }
            function onPlayerStateChange(event){ //Handle when the video ends
                if(event.data === 0){
                    self._goNext();
                }
                else if(event.data === 1){ //video has been started successfully
                    success = true;
                }
            }
            player = new YT.Player('iframe_div',{
                videoId: video_id,
                events:{
                    'onReady': onPlayerReady,
                    'onStateChange': onPlayerStateChange
                }
            });
        }
        else if(video_type=='D'){
            var params = { allowScriptAccess: "always" };
            (function(){
                var e = document.createElement('script'); e.async = true;
                e.src =  'http://api.dmcdn.net/all.js';
                var s = document.getElementsByTagName('script')[0]; s.parentNode.insertBefore(e, s);
            }());
            window.dmAsyncInit = function(){
                var player = DM.player('iframe_div', {video: video_id,  params: params});
                player.addEventListener("apiready", function(e){
                    player_dailymotion = e.target;
                    e.target.play();
                });
                player.addEventListener("ended", function(e){
                    self._goNext();
                });
            };
        }
        else if(video_type=='F'){
            ifrm = document.createElement("IFRAME");
            ifrm.setAttribute("src", "https://www.facebook.com/video/embed?video_id="+video_id);
            ifrm.style.width = "100%";
            document.getElementById('iframe_div').appendChild(ifrm);
        }
        else if(video_type=='S'){
            var h = document.getElementById("video-container").offsetHeight;
            var w = document.getElementById("video-container").offsetWidth;
            $("#video-container").css("backgroundImage", "url('')");
            $("#video-container").css("paddingTop", "0");
            html_object = '<video controls id="stream_player" width="'+w+'" height="'+h+'" x-webkit-airplay="allow" src="'+video_id+'"> </video>';
            $("#iframe_div").append(html_object);
            document.getElementById('stream_player').play();
        }
        else if(video_type=='R'){
            var h = document.getElementById("video-container").offsetHeight;
            var w = document.getElementById("video-container").offsetWidth;
            $("#video-container").css("backgroundImage", "url('')");
            $("#video-container").css("paddingTop", "0");
            jwplayer("iframe_div").setup({
                file: video_id,
                // image: thumbnail_url,
                autostart: 'true',
                height: h,
                width: w
            });
        }
        else if(video_type=='M'){
            var h = document.getElementById("video-container").offsetHeight;
            var w = document.getElementById("video-container").offsetWidth;
            $("#video-container").css("backgroundImage", "url('')");
            $("#video-container").css("paddingTop", "0");
            jwplayer("iframe_div").setup({
                playlist: [{
                    file: video_id,
                    provider: HLS_PLAYER_URL,
                    type: 'hls',
                }],
                hls_debug : false,
                hls_debug2 : false,
                hls_lowbufferlength : 3,
                hls_minbufferlength : -1,
                hls_maxbufferlength : 60,
                hls_startfromlowestlevel : false,
                hls_seekfromlowestlevel : false,
                hls_live_flushurlcache : false,
                hls_live_seekdurationthreshold : 60,
                hls_seekmode : "ACCURATE",
                hls_fragmentloadmaxretry : -1,
                hls_manifestloadmaxretry : -1,
                hls_capleveltostage : false,
                width: w,
                height: h,
                primary: "flash",
                autostart: 'true'
            });
        }
        else if(video_type=='T'){
            var h = document.getElementById("video-container").offsetHeight;
            var w = document.getElementById("video-container").offsetWidth;
            $("#video-container").css("backgroundImage", "url('')");
            $("#video-container").css("paddingTop", "0");
            $("#iframe_div").append(getRTSPPlayer(video_id, w, h));
        }
        document.getElementById('play_btn').style.visibility = 'hidden';
    }
    this._playOnSelectIndex = function(index){
        self.playingIndex = index;
        video = self.currentPlaylist[index];
        self._playVideo(video);
    }
    this._goNext = function (){
        self.playingIndex++;
        var video;
        if(self.playingIndex>=self.currentPlaylist.length){
            self.playingIndex = 0;
        }
        video = self.currentPlaylist[self.playingIndex];
        self._playVideo(video);
    }
    this.highlightPlayingItem = function(id){
        $("a > img#selectItem").removeAttr("id");
        $("a#pl_"+id+":first").children("img").attr('id', 'selectItem');
        var currentElement = $("img#selectItem:first").parent().parent()[0];
        var items = $('#bottom_playlist').children()
        for(i=0; i<items.length; i++){ 
            if(currentElement==items[i])
            {
                var scrollWidth = $('#bottom_playlist').width();
                var position = scrollWidth*(i/items.length)
                $('#bottom_playlist').parent().animate({scrollLeft: position}, 500);
                break;
            }
        }
    }

    this.autoPlay = function(delay,index) {
        if(index==undefined)
            index==0;
        setTimeout(function(){videoPlayer._playOnSelectIndex(index)},delay);
    }
}
