function search(e){
    var find = 'u&#39;|&#39;';
    var re = new RegExp(find, 'g');
    channel_search = channel_search.replace(re, "'");
    $( "#searchKey_input" ).autocomplete({
        source: channel_search.split(",")
    });
    if(e.keyCode == 13){
        search_word = document.getElementById('searchKey_input').value;
        document.getElementById("q").value = search_word;
        document.forms['searchForm'].action = url;
        document.forms['searchForm'].submit();
    }
}

function click_search(){
    search_word = document.getElementById('searchKey_input').value;
    document.getElementById("q").value = search_word;
    document.forms['searchForm'].action = url;
    document.forms['searchForm'].submit();
}

var stop_running = false;

$(document).ready(function(){
    showload(true);
    setTimeout(function(){ 
        updateBox(); 
    }, 0);
});

$(window).scroll(function() {
    if($(window).scrollTop() + $(window).height() == $(document).height()) {
        if(!stop_running){
            updateBox();
        }
    }
});

function isScrollable() {
    var hContent = $("body").height(); // get the height of your content
    var hWindow = $(window).height();  // get the height of the visitor's browser window
    if(hContent>hWindow) { 
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
        var jqxhr = $.get(getIndexurl+"?page="+next_page, function(data){
            showload(false);
            if(data.status==1){
                next_page = data.pagenumber;
                createBox(data.data);
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
function createBox(data){
    var container = $("#container");
    for(i=0;i<data.length;i++){
        var detail = "";
        var detail_more ="";
        box_number = current_index+i;
        box_id = "box_"+ box_number;
        var channel_url = play_channel_url.replace("cid", data[i]['cid']);
        var playlist_url = play_playlist_url.replace("pid", data[i]['pid']);
        var profile_url = play_profile_url.replace("uid", data[i]['uid']);
        if((data[i]['pdetail'] != '') && (data[i]['pdetail'])){
            detail = '<div id="index'+data[i]['pid']+'More" class="col-xs-12 col-sm-12 col-md-12 col-lg-12" style="padding:0px;"><a href="'+playlist_url+'" style="color:#333">';
            if(data[i]['pdetail'].length > 50){
                detail += data[i]['pdetail'].slice(0,50)+'<a onclick="set_detail_slice(index'+data[i]['pid']+');"><font style="color:#999">...'+more_text+'</font></a></a></div>';
                detail_more = '<div id="index'+data[i]['pid']+'" class="col-xs-12 col-sm-12 col-md-12 col-lg-12 hidden" style="padding:0px 10px 0px 0px;">\
                        <a href="'+playlist_url+'" style="color:#333">\
                            '+data[i]['pdetail']+'<a onclick="set_detail_slice(index'+data[i]['pid']+');"><font style="color:#999">...'+hide_text+'</font></a>\
                        </a>\
                    </div>';
            }
            else{
                detail += data[i]['pdetail']+'</a></div>';
            }
        }
        html_object='<div class="alert alert-info" style="margin-bottom:10px; padding:10px 10px 0px 10px;">\
                        <div class="row">\
                            <div class="col-xs-12 col-sm-12 col-md-12 col-lg-12">\
                                <div class="col-xs-5 col-sm-3 col-md-3 col-lg-3" style="padding:0px; margin-top:-10px;">\
                                    <a href="'+playlist_url+'">\
                                        <image src="'+data[i]['pimg']+'" style="width:100%; margin-top:10px;"/>\
                                    </a>\
                                </div>\
                                <div class="col-xs-7 col-sm-9 col-md-9 col-lg-9" style="padding:0px 0px 0px 10px;">\
                                    <div class="col-xs-12 col-sm-12 col-md-12 col-lg-12" style="padding-left:0px; padding-right:0px;">\
                                        <span class="label label-danger pull-right"><font style="font-size:14px;">'+update_text+' '+data[i]['ptime']+' '+ago_text+'</font></span>\
                                    </div>\
                                    <div class="col-xs-12 col-sm-12 col-md-12 col-lg-12" style="padding-left:0px;">\
                                        <a href="'+playlist_url+'">\
                                            <h4>'+data[i]['pname']+'</h4>\
                                        </a>\
                                    </div>\
                                    '+detail+'\
                                    '+detail_more+'\
                                    <div class="col-xs-12 col-sm-12 col-md-12 col-lg-12" style="padding:0px;">\
                                        <a href="'+channel_url+'">\
                                            <h5>'+channel_text+': '+data[i]['cname']+'</h5>\
                                        </a>\
                                    </div>\
                                    <div class="col-xs-12 col-sm-12 col-md-12 col-lg-12" style="padding:0px;">\
                                        <a href="'+profile_url+'">\
                                            <h5>'+by_text+': '+data[i]['uname']+'</h5>\
                                        </a>\
                                    </div>\
                                </div>\
                            </div>\
                        </div>\
                    </div>';
        container.append(html_object);
    }
}
