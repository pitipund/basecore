function live_channel(channelID, streamUrl, image){
    CHANNEL_ID = channelID;
    $("ul.nav-sidebar li").removeClass("active");
    $("ul.nav-sidebar li#channel_"+channelID).addClass("active");
    $("#btn_unfollow").attr('onclick','unfollowChannelID("'+channelID+'");');
    document.getElementById('btn_add_penta').className += ' hidden';
    updateVideoPlayerTitle(document.getElementById('channel_'+channelID).title);
    showUnfollow(true);
    showChannel(false);
    channel_name = document.getElementById('channel_'+channelID).title;
    if(document.getElementById('iframe_div')){
        var elem = document.getElementById('iframe_div');
        elem.parentNode.removeChild(elem)
    }
    var url = encodeURIComponent(streamUrl)+"&provider=http&http.startparam=start";
    var so = new SWFObject('http://player.longtailvideo.com/player.swf','mpl','100%','100%','9');
    so.addParam('allowscriptaccess','always');
    so.addParam('allowfullscreen','true');
    so.addVariable('autostart','true');
    so.addVariable('file',url);
    so.addVariable('image',image);
    so.addVariable('stretching','exactfit');
    var container = $("#div_container");
    container.append('<div id="iframe_div"></div>');
    so.write('iframe_div');
    $("#bottom_playlist").hide();
    $("#play_btn").hide();
    $("#video_message").hide();
}

function updateActiveChannel(channelID, isUnfollow, isChannel){
    CHANNEL_ID = channelID;
    $("ul.nav-sidebar li").removeClass("active");
    $("ul.nav-sidebar li#channel_"+channelID).addClass("active");
    $("#btn_unfollow").attr('onclick','unfollowChannelID('+channelID+');');
    $("#btn_edit_channel").attr('onclick','location.href="/'+ user_id + '/channel/edit/'+channelID+'/";');
    $("#btn_add_playlist").attr('onclick','location.href="/'+channelID+'/playlist/create/";');
    $("#btn_delete_channel").attr('href','/channel/delete/'+channelID+'/');
    $("#btn_delete_channel").attr('onclick',"return confirm('"+DELETE_CHANNEL_TEXT+"');");
    updateVideoPlayerTitle(document.getElementById('channel_'+channelID).title);
    showUnfollow(isUnfollow);
    showChannel(isChannel);
    channel_name = document.getElementById('channel_'+channelID).title;
}

function unfollowChannelID(channelID){
    if(!confirm('Unfollow this channel?')){
        return;
    }
    var url = SUBSCRIBE_CHANNEL+ "?channelid="+channelID+"&type=1";
    var a = new Model(url);
    a.getTags(unfollowDidSuccess);
    $("#channel_"+channelID).remove();
}

function unfollowDidSuccess(success){
    if(success.status==0){
        alert(success.msg)
    }
    else{
        var following_channels = $(".following");
        if(following_channels.length>0){
            var channel = following_channels[0];
            var channel_id = channel.id.split("channel_")[1];
            select_channel_id(channel_id);
            updateActiveChannel(channel_id, true, false);
        }
        else{
            document.location.reload(true)
        }
    }
}

function showUnfollow(show){
    document.getElementById('btn_unfollow').className = document.getElementById('btn_unfollow').className.replace('hidden', '');
    if(show==false)
        document.getElementById('btn_unfollow').className = document.getElementById('btn_unfollow').className+' hidden';
}

function showChannel(show){
    document.getElementById('btn_channel').className = document.getElementById('btn_channel').className.replace('hidden', '');
    if(show==false)
        document.getElementById('btn_channel').className = document.getElementById('btn_channel').className+' hidden';
}

function fb_share(){
    var ch = document.getElementById('channel_'+CHANNEL_ID);
    if(CHANNEL_ID.indexOf("live_")>-1){//digital channel
        var url = window.location.protocol+"//"+window.location.host+"/live/"+CHANNEL_ID.replace('live_','');
    }
    else{//curator channel
        var url = window.location.protocol+"//"+window.location.host+"/channel/"+CHANNEL_ID;
    }
    if(document.getElementById('selectItem')){ //selected link
        var name = document.getElementById('selectItem').title;
        var picture = document.getElementById('selectItem').src;
        var description = ch.title+": "+name;
        url += '?current='+$('#selectItem').parent().children('input')[0].value;
    }
    else{ //channel
        var name = ch.title;
        var picture = ch.getElementsByTagName('img')[0].src;
        var description = ch.title;
    }
    fb_publish(name, description, url, picture);
}

function penta(action){
    if(action=='add'){
        var channel = document.getElementById('channel_'+CHANNEL_ID);
        add_to_penta(CHANNEL_ID, channel.title, channel.getElementsByTagName('img')[0].src);
    }
    // else if(action=='queue'){
    //     add_to_queue(document.getElementById('selectItem').name);
    // }
}
