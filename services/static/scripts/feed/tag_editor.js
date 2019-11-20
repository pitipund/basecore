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

function createTagButton(tag){
    var button = "<button "+
                    "type=\"button\" " + 
                    "tag_id=\""+tag.id+"\"" +
                    "tag_name=\""+ tag.name + "\"" +
                    "data-tagid=\""+tag.id+ "\"" +
                    "data-tagname=\""+tag.name+ "\"" +
                    // "onclick=\"onTagButtonClick(\'"+tag.id+"\',\'"+tag.name+"\');\" "+
                    "class=\"create-tag-btn btn btn-default\" " + 
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
                    // "onclick=\"onSelectedTagButtonClick(\'"+tag.id+"\',\'"+tag.name +"\');\" "+
                    "data-tagid=\""+tag.id+ "\"" +
                    "data-tagname=\""+tag.name+ "\"" +
                    "class=\"selected-tag-btn btn btn-primary\" " + 
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

function reloadForTags(parent,tags) {
    console.log(parent)
    parent.find(".tag-editor-content > .tags-render").val(JSON.stringify(tags));
    renderSelectedTagButton(parent.find(".tag-editor-content > .tag_selected "), tags);
    for(index in tags) {
        var tag = tags[index]
        console.log("<option value="+tag.id+" selected='selected'></option>")
        parent.find(".tag-editor-content > .tags-to-send").append("<option value="+tag.id+" selected='selected'></option>")
    }
}

$.fn.tagEditorComponent = function(urlTagQuery, urlTagAdd) {
    var typingTimer;
    var delayTime = 500;

    var tags_render = $(this).find(".tag-editor-content > .tags-render");
    var tag_selected = $(this).find(".tag-editor-content > .tag_selected");
    var txtboxWord = $(this).find(".tag-editor-content > .tag_add > div > .txtboxWord");
    var btnCreateTag = $(this).find(".tag-editor-content > .tag_add > div > span >.btnCreateTag");
    var tag_list = $(this).find(".tag-editor-content > .tag_add > .tag_list");
    var tags_to_send = $(this).find(".tag-editor-content > .tags-to-send");

    var setValueForTags = function(tags) {
        newVal = [];
        for(index in tags){
            newVal.push(parseInt(tags[index].id));
        }
        tags_render.val(JSON.stringify(newVal));
    }

    var onSelectedTagButtonClick = function(id,name){
        removeTag(tags_render,{"name":name,"id":id});
        renderSelectedTagButton(tag_selected,JSON.parse(tags_render.val()));
        tags_to_send.find("option[value='"+id+"']").remove();
    }

    var onTagButtonClick = function(id,name){
        addTag(tags_render,{"name":name,"id":id});
        renderSelectedTagButton(tag_selected,JSON.parse(tags_render.val()));
        tags_to_send.append("<option value="+id+" selected='selected'></option>")
    }

    var restDelay = function(){
        clearTimeout(this.typingTimer);
        typingTimer = setTimeout(function(){
            doGetTag();
        },delayTime);
        return true;
    }

    var doGetTag = function(){
        console.log("do get tag call")
        var word = txtboxWord.val();
        console.log(word);
        console.log(tag_list)
        $.get(urlTagQuery + "?word=" + word, function(response){
            tag_list.empty()
            for(var i=0;i<response.length;i++){
                var button = createTagButton(response[i]);
                tag_list.append(button);
            }
        });
    }

    txtboxWord.keyup(function(){
        restDelay();
    });

    btnCreateTag.click(function(){
        var word = txtboxWord.val();
        if(word!="") {
            btnCreateTag.button('loading');
            $.get(urlTagAdd + "?word="+word,function(response){
                btnCreateTag.button('reset');
                if(response['success']){
                    obj.onTagButtonClick(response['id'],response['name']);
                    obj.doGetTag();
                }else {
                    alert(response['error']);
                }
            });
        }else {
            alert("Failed to create empty tag.");
        }
    });

    $(this).on("click",".create-tag-btn",function(){
        onTagButtonClick($(this).data("tagid"),$(this).data("tagname"));
    })

    $(this).on("click",".selected-tag-btn",function(){
        onSelectedTagButtonClick($(this).data("tagid"),$(this).data("tagname"));
    })

    restDelay();
}