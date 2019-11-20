function fb_share(){
    var ch_name = document.getElementById('chname').innerHTML;
    var ch_detail = document.getElementById('chdetail').innerHTML;
    if(document.getElementById('selectItem')){ //selected link
        var name = document.getElementById('selectItem').title;
        var picture = document.getElementById('selectItem').src;
        var description = ch_name+": "+name;
    }
    else{ //channel
        var name = ch_name;
        var picture = document.getElementById('ch_icon').src;
        var description = ch_name;
    }
    if(ch_detail!='None' && ch_detail!=''){
        description += ' - '+ch_detail;
    }
    fb_publish(name, description, document.URL, picture);
}

function penta(action){
    if(action=='add'){
        add_to_penta(id, channel_name, channel_icon);
    }
}