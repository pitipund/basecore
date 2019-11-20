function add_to_penta(chid, chname, chimg){ // add to Penta
    if(window.ExtensionAPI!=undefined){
        ExtensionAPI.pentaScheme("penta://channel?action=add&channel_id=channel_"+chid+"&name="+encodeURIComponent(chname)+"&icon="+encodeURIComponent(chimg)+"&type=queue");
    }else{
        location.href="/help/manual/how-to-add-channel-to-penta";
    }
}

function playOrQueue(btn, id, action){ //id:playlist id  //play on Penta, add to queue
    if(detectmob()){
        var currentvid = '';
        $.get("/curatorPlayOrQueue/"+id+"/", function(data) {
            if(data.status == 'true'){
                var linkType = "";
                for(i=0;i<data.resultType.length;i++){
                    if(i==0){
                        if(data.resultType[i] == 'Y'){
                            var url = "penta://youtube?1="+data.resultId[i];
                            linkType = "Y";
                        }
                        else if(data.resultType[i] == 'D'){
                            var url = "penta://dailymotion?1="+data.resultId[i];
                            linkType = "D";
                        }
                    }
                    else{
                        if(data.resultType[i] == linkType){
                            url += "&"+(i+1)+"="+data.resultId[i];
                        }
                        else{
                            break;
                        }
                    }
                    if(data.resultId[i]==currentvid_videoid){
                        currentvid = data.resultId[i];
                    }
                }
                if(action == 'play'){
                    if(currentvid!=''){
                        url += "&current="+currentvid;
                    }
                    else{
                        url += "&current="+data.resultId[0];//+"&title="+data.ptitle;// $('#timelineModal').modal('hide');
                    }
                }
                location.href = url;
                btn.innerHTML = added_text;
                btn.className = btn.className+" disabled";
            }
            else{
                if(action == "add to queue"){
                    action_text = queue_text;
                }
                else{
                    action_text = play_text;
                }
                alert(cant_text+action_text);
            }
        });
    }
}

function delete_playlist(playlistId, channelId){
    set_spinner('spinnerbar', 'addPlaylistBtn', 'edit'+playlistId+'Btn');
    var delBtn = document.getElementById('del'+playlistId+'Btn');
    delBtn.className = 'btn btn-danger btn-xs disabled';
    confirmMsg = confirm('Are you sure you want to delete?');
    if(confirmMsg){
        delLink = delLink.replace('ling', playlistId);
        location.href = delLink;
    }
    else{
        listLink = listLink.replace('1234', channelId);
        location.href = listLink;
    }
}

function subscribeChannel(type, channel_id){
    var subbtn = document.getElementById("subscription_button"+channel_id);
    var jqxhr = $.get('/channel/subscribe/'+"?channelid="+channel_id+"&type="+type, function(data){
        if(data.status==1){
            if(type == 0){ //subscribe
                subbtn.className = subbtn.className.replace("btn-info", "btn-danger");
                subbtn.innerHTML = "<span class='glyphicon glyphicon-warning-sign'></span> "+unsubscribe_text;
                subbtn.setAttribute('onclick', 'subscribeChannel(1, "'+channel_id+'")');
            }
            else{
                subbtn.className = subbtn.className.replace("btn-danger", "btn-info");
                subbtn.innerHTML = "<span class='glyphicon glyphicon-star'></span> "+subscribe_text;
                subbtn.setAttribute('onclick', 'subscribeChannel(0, "'+channel_id+'")');
            }
            document.getElementById("subscribers_number"+channel_id).innerHTML = data.msg
        } 
        else{
            alert(data.error)
        }
    });
}

window.fbAsyncInit = function(){
    FB.init({
        appId  :'571837776208476', // App ID from the app dashboard
        status :true,              // Check Facebook Login status
        xfbml  :true               // Look for social plugins on the page
    });
};
(function(){ // Load the SDK asynchronously
    if (document.getElementById('facebook-jssdk')) {return;}
    var firstScriptElement = document.getElementsByTagName('script')[0];
    var facebookJS = document.createElement('script'); 
    facebookJS.id = 'facebook-jssdk';
    facebookJS.src = '//connect.facebook.net/en_US/all.js';
    firstScriptElement.parentNode.insertBefore(facebookJS, firstScriptElement);
}());
    
function fb_publish(name, description, link, picture){
    FB.ui({
        method     :'feed',
        name       :name,
        caption    :window.location.host,
        description:(description),
        link       :link,
        picture    :picture
    },
    function(response){
        if(!response && !response.post_id){
            alert('Post was not published.');
        }
    });
}