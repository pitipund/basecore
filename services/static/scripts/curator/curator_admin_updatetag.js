function arrangeAndSubmit(){
    var elements = document.forms['tags_form'].elements;
    var resultCount = 1;
    for(var i=0; i<elements.length; i++){
        var tag_id = "";
        if((elements[i].id.indexOf("tag_")>=0)&&(elements[i].checked)){ // if tag
            tag_id = elements[i].value;
            var j = i+1;
            var channel_id = [];
            while(j<elements.length){
                if(elements[j].id.indexOf("channel_"+tag_id+"_")>=0){ // if channel
                    if(elements[j].checked){
                        channel_id.push(elements[j].value);
                    }
                }
                else{
                    break;
                }
                j+=1;
            }
            var obj = document.createElement("input");
            obj.type= "hidden";
            obj.name = "result"+resultCount;
                obj.value = '[{'
                   +'"tag_id": "'+tag_id+'",'
                   +'"channel_id": "'+channel_id
                   +'"}]';
            document.getElementById('master_hid').appendChild(obj);
            resultCount+=1;
        }
    }
    document.forms["tags_form"].submit();
}