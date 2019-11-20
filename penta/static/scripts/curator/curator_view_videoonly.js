var player;
var hasplayed = false;
var success = false;
var isrunning = true;

//video controller
if(video_type=='Y'){
    if(navigator.userAgent.indexOf("PentaRemote Android")>-1){ //is penta remote
        pentaRemote_play_modal();
    }
    else{ //Handle starting video
        function onYouTubePlayerAPIReady(){
            player = new YT.Player('player', {
                videoId: currentvid_videoid,
                events: {
                    'onReady': onPlayerReady,
                    'onStateChange': onPlayerStateChange
                }
            });
        }
        function onPlayerReady(event){ //Handle when the video is ready
            if(!detectMac()){
                if(detectmob()){
                    event.target.seekTo(0.01,true);// normal playing causes a gigantic bug when playing videos in stock browsers in both Android  (Video not response)
                }
                else{//play normally for PC
                    event.target.playVideo();
                }
            }
            else{/*do nothing for iOS*/}
            hasplayed =true;
        }
        function onPlayerStateChange(event){ //Handle when the video ends    
            if(event.data === 0){   
                gotoNextVideo();
            }
            else if(event.data === 1){ //video has been started successfully
                success = true;
            }
        }
    }
}
else if(video_type=='D'){
    if(navigator.userAgent.indexOf("PentaRemote Android")>-1){ //is penta remote
        pentaRemote_play_modal();
    }
    else{
        var params = { allowScriptAccess: "always" };
        (function(){
            var e = document.createElement('script'); e.async = true;
            e.src =  'http://api.dmcdn.net/all.js';
            var s = document.getElementsByTagName('script')[0]; s.parentNode.insertBefore(e, s);
        }());
        window.dmAsyncInit = function(){
            var player = DM.player("player2", {video: currentvid_videoid,  params: params});
            player.addEventListener("apiready", function(e){
                player_dailymotion = e.target;
                if(!detectmob()){
                    e.target.play();
                }
            });
            player.addEventListener("ended", function(e){
                gotoNextVideo();
            });
        };
    }
}
else if(video_type=='V'){
    var f = $('#player2'),
    url = f.attr('src').split('?')[0]
    if (window.addEventListener){
        window.addEventListener('message', onMessageReceived, false);
    }
    else {
        window.attachEvent('onmessage', onMessageReceived, false);
    }
    function onMessageReceived(e){ // Handle messages received from the player
        var data = JSON.parse(e.data);
        switch (data.event){
            case 'ready': onReady(); break;
            case 'pause': onPause(); break;
            case 'finish':onFinish();break;
        }
    }
    function post(action, value) {
        var data = { method: action };
        if(value){
            data.value = value;
        }
        f[0].contentWindow.postMessage(JSON.stringify(data), url);
    }
    function onReady(){
        if(!detectmob()){
            post('play');
        }
        post('addEventListener', 'pause');
        post('addEventListener', 'finish');
        post('addEventListener', 'playProgress');
    }
    function onFinish(){
        gotoNextVideo();
    }
}

function gotoNextVideo(){
    if(currentvid_index<size){
        window.location = nextIndex_url;
    }
    else{
        window.location = nextLink_url;
    }   
}

function gotoPrevVideo(){
    if(currentvid_index>0){
        window.location = prevIndex_url.replace('link', currentvid_index-1);
    }
    else{
        window.location = prevLink_url;
    }
}

function detectMac(){ 
    if( navigator.userAgent.match(/iPhone/i)
    || navigator.userAgent.match(/iPad/i)
    || navigator.userAgent.match(/iPod/i)
    ){
        return true;
    }
    else {
        return false;
    }
}

//expand video for PC
if(!detectmob()){
    if(video_type=='Y'){
        playerelement = $('#player');
    }
    else if(video_type=='D'){
        playerelement = $('#player2');
    }
    else{
        playerelement = $('#player2');
    }
}

//Pause or Play Video button
function swapButton(){
    icon = $("#controller_play");
    if(isrunning){
        if(video_type=='Y'){
            player.pauseVideo();
        }
        else if(video_type=='D'){
            player_dailymotion.pause();
        }
        else if(video_type=='V'){
            post('pause');
        }
        isrunning=false;
        icon.removeClass("glyphicon glyphicon-pause");
        icon.addClass("glyphicon glyphicon-play");
    }
    else{
        if(video_type=='Y'){
            player.playVideo();
        }
        else if(video_type=='D'){
            player_dailymotion.play();
        }
        else if(video_type=='V'){
            post('play');
        }
        isrunning=true;
        icon.removeClass("glyphicon glyphicon-play");
        icon.addClass("glyphicon glyphicon-pause");
    }
}

// get query arguments
var $_GET = {},args = location.search.substr(1).split(/&/);
for (var i=0; i<args.length; ++i) {
    var tmp = args[i].split(/=/);
    if (tmp[0] != "") {
        $_GET[decodeURIComponent(tmp[0])] = decodeURIComponent(tmp.slice(1).join("").replace("+", " "));
    }
}

//force running youtube( because youtube API has a bug that sometimes it does not fetch video)
//!!!!!always put this at the end of this file
if(navigator.userAgent.indexOf("PentaRemote Android")>-1){ //is penta remote
    pentaRemote_play_modal();
}
else if(video_type=='Y'&&!hasplayed){
    onYouTubePlayerAPIReady();  
}

function pentaRemote_play_modal(){
    if(document.getElementById('play_remote')){
        document.getElementById('play_remote').remove();
    }
    var html_obj = '<a id="play_remote" class="btn btn-danger btn-lg" style="position:absolute; top:45%; left:45%;" data-toggle="modal" href="#playlistModal">\
                        <span class="glyphicon glyphicon-play"></span>\
                    </a>';
    $("#video-container").append(html_obj);
}

function set_play_videoHelper_modal(id){
    if(window.VideoHelper.plays != undefined){
        $.get("/curatorPlayOrQueue/"+id+"/", function(data) {
            if(data.status == 'true'){
                var jsonObj = [];
                for(i=0;i<data.resultType.length;i++){
                    if(data.resultType[i] == 'Y'){
                        jsonObj.push({"type": "youtube", "video_id": data.resultId[i]});
                    }
                    else if(data.resultType[i] == 'D'){
                        jsonObj.push({"type": "dailymotion", "video_id": data.resultId[i]});
                    }
                }
                document.getElementById('videoHelper_btn').setAttribute('onclick', "VideoHelper.plays("+"'"+JSON.stringify(jsonObj)+"'"+")");
                $('#videoHelper_btn').click();
            }
            else{
                alert(cant_play_text);
            }
        });
    }
    else{
        if(video_type=='Y'){
            var vtype = 'youtube';
        }
        else if(video_type=='D'){
            var vtype = 'dailymotion';
        }
        document.getElementById('videoHelper_btn').setAttribute('onclick', "VideoHelper.play("+"'"+vtype+"'"+','+"'"+currentvid_videoid+"'"+")");
        $('#videoHelper_btn').click();
    }
}

function set_play_queue_modal(btn, id, action){
    playOrQueue(btn, id, action)
}