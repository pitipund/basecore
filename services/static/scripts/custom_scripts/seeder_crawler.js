$(function() {
    $( ".sortable" ).sortable();
});

// document.getElementById('tags_form').onsubmit = function() {
//     return false;
// }

function name_auto(e, name, id){
    var find = 'u&#39;|&#39;';
    var re = new RegExp(find, 'g');
    name = name.replace(re, "");
    $("#name_input"+id).autocomplete({
        source: name.split(",")
    });
}

function submitValues(){
    var elements = document.forms['tags_form'].elements;
    for(var i=0; i<elements.length; i++){
        if((elements[i].name.indexOf("ch_")>=0)&&(elements[i].checked)){ // if channel
            channel_index = elements[i].name.split("_")[1];
            var j = i+1;
            while(j<elements.length){
                if(elements[j].name.indexOf("pl_")>=0){ // if playlist
                    if(elements[j].checked){
                        var k = j+1;
                        var link = [];
                        while(k<elements.length){
                            if(elements[k].name.indexOf("lk_")>=0){ // if link
                                if(elements[k].checked){
                                    link.push(elements[k].value);
                                }
                                k+=1;
                            }
                            else{
                                if(link.length > 0){ // result
                                    var obj = document.createElement("input");
                                    temp = elements[i].value.split("__");
                                    obj.type= "hidden";
                                    obj.name = "result"+k;
                                    obj.value = "";
                                    if(type==0){
                                        obj.value = '[{'
                                       +'"seeder_id": "'+temp[0]+'",'
                                       +'"seeder_name": "'+temp[1].replace(/["']/g, "")+'",'
                                       +'"playlist_name": "'+elements[j].value.replace(/["']/g, "")+'",'
                                       +'"links": "'+link
                                       +'"}]';
                                    }
                                    else{
                                         obj.value = '[{'
                                       +'"seeder_id": "'+temp[0]+'",'
                                       +'"seeder_tag": "'+document.getElementById("tag_"+channel_index).options[document.getElementById("tag_"+channel_index).selectedIndex].value+'",'
                                       +'"seeder_channel": "'+document.getElementById("toch_"+channel_index).options[document.getElementById("toch_"+channel_index).selectedIndex].value+'",'
                                       +'"seeder_name": "'+temp[1].replace(/["']/g, "")+'",'
                                       +'"playlist_name": "'+elements[j].value.replace(/["']/g, "")+'",'
                                       +'"seeder_extra": "'+document.getElementById("name_input"+channel_index).value+'",'
                                       +'"links": "'+link
                                       +'"}]';
                                    }
                                    document.getElementById('master_hid').appendChild(obj);
                                }
                                j = k;
                                break;
                            }
                        }
                    }
                    else{
                        j+=1;
                    }
                }
                else if(elements[j].name.indexOf("ch_")>=0){
                    i = j-1;
                    break;
                }
                else{
                    j+=1;
                }
            }
        }
    }
    document.forms['tags_form'].submit();
}

function search(e){
    if((e.keyCode == 13) || (e.keyCode == 0)) {
        value = encodeURIComponent(document.getElementById('search_name').value);
        if(value!=""){
            window.location=target_url+"?title="+value;
        }
        else{
            alert("Invalid input");
        }
    }
}