function set_url_p(){
    url_p = document.getElementById('id_url_name');
    document.getElementById('urlName_p').innerHTML = "http://pentachannel.com/"+url_p.value;
    url_p.setAttribute('onkeyup', 'set_channelUrlName(this, event);');
    url_p.setAttribute('onblur', 'set_channelUrlName(this, event);');
}

function setTag_input(tagname){
    isTrue = true;
    i = 1;
    container = $("#tag_div");
    while(isTrue){        
        var tmp = 'tag'+i;
        if(document.getElementById(tmp)){
            i += 1;
        }
        else {
            html_obj = '<div id="div'+i+'" class="input-group" style="padding-bottom:5px;">\
                    <input id="tag'+i+'" name="tag'+i+'" type="text" class="form-control" value="'+tagname+'"/>\
                    <span class="input-group-btn">\
                        <a id="remove'+i+'" class="btn btn-danger" onclick="setTag_remove('+i+')"><span class="glyphicon glyphicon-trash"></span> '+remove_text+'</a>\
                    </span>\
                </div>';
            container.append(html_obj);
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

function setKey_input(key){
    var container = $("#key_div_master");
    var isTrue = true;
    var i = 1;
    while(isTrue){        
        var tmp = 'key'+i;
        if(document.getElementById(tmp)){
            i += 1;
        }
        else{
            var html_obj = '<div id="key_div'+i+'" class="input-group" style="padding-bottom:5px;">\
                    <input id="key'+i+'" value="'+key+'" type="text" class="form-control"/>\
                    <span class="input-group-btn">\
                        <a class="btn btn-danger" onclick="key_remove('+i+')"><span class="glyphicon glyphicon-trash"></span> '+remove_text+'</a>\
                    </span>\
                </div>';
            container.append(html_obj);
            isTrue = false;
        }
    }
}

function key_remove(id){
    $('#key_div'+id).remove();
}

function submit_channel(action, channelId, isDefault) {
    set_spinner('spinnerbar', 'submitBtn', 'cancelBtn');
    if((isDefault != 'True') && (action == 'update') && (document.getElementsByName('isLive')[0].checked)){
        $.get("/channel/checkLive/"+channelId+"/", function(data) {
            if(data.result == 'true'){ /*Live channel*/
                document.forms['channel_create_form'].submit()
            }
            else if(data.result == 'false'){ /*want change to Live channel*/
                confirmMsg = confirm(data.message);
                if(confirmMsg){
                    $.get("/channel/delete/allPlaylist/"+channelId+"/", function(data) {
                        if(data.result == 'true'){
                            document.forms['channel_create_form'].submit()
                        }
                        else{
                            alert(data.message);
                        }
                    });
                }
                else{
                    location.href = cancelLink;
                }
            }
            else{
                alert(data.message);
            }
        });
    }
    else{
        if(document.getElementById('key_div_master')){
            var elements = document.getElementById('key_div_master').childNodes;
            var index = 1;
            for(var i=0; i<elements.length; i++){
                var id = elements[i].id.split("key_div")[1];
                if(document.getElementById('key'+id).value != ''){
                    var hid = lib_createObj('key_result'+index, 'input', null);
                    hid.type = "hidden"
                    hid.value = document.getElementById('key'+id).value;
                    index += 1;
                    document.getElementById('key_hid_div').appendChild(hid);
                }
            }
        }
        document.forms['channel_create_form'].submit();
    }
}

function createTagButton(tag){
    var button = "<button "+
                    "type=\"button\" " + 
                    "tag_id=\""+tag.id+"\"" +
                    "tag_name=\""+ tag.name + "\"" +
                    "onclick=\"onTagButtonClick(\'"+tag.id+"\',\'"+tag.name+"\');\" "+
                    "class=\"btn btn-default\" " + 
                    "style=\"margin-right: 5px; margin-bottom: 5px;\" >" +
                        tag.name +
                "</button>";
    return button;
}

function createSelectedTagButton(tag){
    var button = "<button "+
                    "type=\"button\" " + 
                    "tag_id=\""+tag.id+"\"" +
                    "tag_name=\""+ tag.name + "\" " +
                    "onclick=\"onSelectedTagButtonClick(\'"+tag.id+"\',\'"+tag.name +"\');\" "+
                    "class=\"btn btn-primary\" " + 
                    "style=\"margin-right: 5px; margin-bottom: 5px;\" >" +
                        tag.name +
                    " <span class='glyphicon glyphicon-remove'></span></button>";
    return button;
}

function renderSelectedTagButton(div_element,tags){
    div_element.empty();
    for(var i=0;i<tags.length;i++){
        var button = createSelectedTagButton(tags[i]);
        div_element.append(button);
    }
}

function addTag(input,tag){
    var data = input.val();
    var tags = JSON.parse(data);
    var duplicate = false;
    for(var i=0;i<tags.length;i++){
        if(tags[i].id==tag.id){
            duplicate = true;
            break;
        }
    }

    if(!duplicate){
        tags.push(tag);
        input.val(JSON.stringify(tags));
    }
}

function removeTag(input,tag){
    var data = input.val();
    var tags = JSON.parse(data);
    var index = -1;
    for(var i=0;i<tags.length;i++){
        if(tags[i].id==tag.id){
            index = i;
            break;
        }
    }

    if(index!=-1){
        tags.splice(index,1);
        input.val(JSON.stringify(tags));
    }
}