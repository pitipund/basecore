$(document).ready(function(){
    function highlightText(item, query, highlightClass) {
        if(query.length == 0)
            return item;
        var tokens = query.trim().split(/\s+/).sort( function(a, b) {
            return b.length - a.length;
        });
        var highlight = "<span class='"+highlightClass+"'>$1</span>";
        var regex = new RegExp( '(' + tokens.join('|') + ')', 'gi' );
        return item.replace( regex, highlight );
    }
    var busy = false;
    $('#navSearchInput').typeahead({
        delay: 200,
        source: function(query, process) {
            var widget = this;
            if(!busy) {
                busy = true;
                return $.ajax({
                    url: "/api/v2/search/?q="+query+"&page=1&per_page=8",
                    dataType: 'json',
                    success: function (data) {
                        busy = false;
                        if(data.search_text != $('#navSearchInput').val()) {
                            widget.lookup();
                            return false;
                        }
                        var result = [];
                        for(var i in data.playlists) {
                            result.push({
                                'id': data.playlists[i].id,
                                'name': data.playlists[i].name,
                                'channel_id': data.playlists[i].channel,
                                'channel_name': data.playlists[i].channel_name,
                                'thumb': data.playlists[i].link.real_thumbnail.replace('0.jpg', '1.jpg'),
                                'duration': data.playlists[i].link.duration_s,
                                'src': data.playlists[i].src,
                                'src_id': data.playlists[i].src_id,
                                'play_url': data.playlists[i].play_url
                            });
                        }
                        return typeof data == 'undefined' ? false : process(result);
                    },
                    error: function(data) {
                        busy = false;
                    }
                });
            }
        },
        matcher: function(obj) {
            return true;
        },
        highlighter: function(obj) { // must modified argument from bootstrap3-typehead
            var query = this.query;
            var name = highlightText(obj.name, query, 'typeahead_highlight_top');
            var channel = highlightText(obj.channel_name, query, 'typeahead_highlight_bottom');
            var srcStyle = obj.src ? "search" : "th-large" ;
            var caledDuration = obj.duration >= 60 ? parseInt(obj.duration/60).toString() : "น้อยกว่า 1";
            var duration = (obj.duration > 0) ? ("&nbsp&nbsp <span class='glyphicon glyphicon-time'></span> &nbsp"+caledDuration+"  นาที") : "";
            var itm = "<table width='100%' style='border-top:1px dashed grey;'>"
             + "<tr>"
             + "<td width='80px' rowspan='2'><img class='typeahead_photo' src='" + obj.thumb + "' /></td>"
             + "<td align='left' class='typeahead_top'>"+name+"</td>"
             + "<tr class='typeahead_bottom'>"
             + "<td align='left'>&nbsp;&nbsp;&nbsp;&nbsp;<span class='glyphicon glyphicon-"+srcStyle+"'></span> "+channel+duration+"</td>"
             + "</tr>"
             + "</table>";
            return itm;
        },
        selectNone: function() { // must modified function 'select' and add selectNone in bootstrap3-typehead
            $('#searchForm').submit(); 
        },
        afterSelect: function(obj) {
            var query=this.query;
            if(obj.src) {
                window.open("/th/generalplay/"+obj.src+"/"+obj.src_id+"/?q="+query, "_self");
            } else {
                window.open(obj.play_url+"?q="+query, "_self");
            }
        },
        items: 10,
        autoSelect: false
    });

    $("#createChannelButton").click(function() {

        $("#createChannelform").ajaxSubmit({
            url: "/feed/channel/",
            type: 'POST',
            success: onDone,
            error: onFail

        });

        function onDone(data) {
            console.log("on create success !!");
            console.log(data);
            $("#createChannelModal").modal("hide");
            $('body').removeClass('modal-open');
            $('.modal-backdrop').remove();
            location.replace("/th/channel/" + data.id);
        }
        function onFail(data) {
            console.log("fail!" + data.detail);
        }

        return false;
    });
    // document.getElementById("navSearchInput").focus(); // Temporary comment out

    $('[data-toggle="tooltip"]').tooltip();
    $(".sideBarToggle").click(function(){
        $("div#wrapper").toggleClass("toggled");
    });
});