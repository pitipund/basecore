function createChannel(){
    set_spinner('spinnerbar', 'sendBtn', 'cancelBtn');
    document.getElementById('channel_id').value = document.getElementById('channel_select').value;
    document.forms['content_create_form'].submit();
}

function setChannel(){
    channel = document.getElementById('channelhid').value;    
    channel_sel = document.getElementById('channel_selhid').value;
    var channelJson =JSON.parse(channel);
    var channel_select = document.createElement('select');
    channel_select.id = "channel_select";
    channel_select.style.width = "81%";
    channel_select.innerHTML = "";
    for(i in channelJson){
        if(channel_sel!=''){
            if(channel_sel == channelJson[i].chid){
                channel_select.innerHTML += "<option value="+channelJson[i].chid+" selected>"+channelJson[i].chname+"</option>";
            }
            else{
                channel_select.innerHTML += "<option value="+channelJson[i].chid+">"+channelJson[i].chname+"</option>";
            }
        }
        else{
            channel_select.innerHTML += "<option value="+channelJson[i].chid+">"+channelJson[i].chname+"</option>";
        }
    }
    channel_div = document.getElementById('channel_div');
    channel_div.appendChild(channel_select);
}
