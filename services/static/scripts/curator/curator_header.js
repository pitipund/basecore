function search(e){
    var find = 'u&#39;|&#39;';
    var re = new RegExp(find, 'g');
    channel_search = channel_search.replace(re, "'");
    $("#searchNav_input").autocomplete({
        source: channel_search.split(",")
    });
    $("#searchNav_input").autocomplete('widget').zIndex(10000);
    if(e.keyCode == 13){
        tag_filter = document.getElementById('searchNav_input').value;
        var urlSet = url;
        document.getElementById("q").value = tag_filter;
        document.forms['searchNavForm'].action = urlSet;
        document.forms['searchNavForm'].submit();
    }
}

function click_search(){
    tag_filter = document.getElementById('searchNav_input').value;
    var urlSet = url;
    document.getElementById("q").value = tag_filter;
    document.forms['searchNavForm'].action = urlSet;
    document.forms['searchNavForm'].submit();
}