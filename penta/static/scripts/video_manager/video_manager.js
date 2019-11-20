function Model(GET_TAGS_URL){
    this.GET_TAGS_URL = GET_TAGS_URL;
    this.getTags = function(callback){
        $.get(GET_TAGS_URL, function(result){
            callback(result);
        });
    }
}

function VideoManagerModel(domElement){
    var self = this
    self.domElement = domElement;
    self.videos;
    self.current_channel_id;

    this.select_channel= function(url) {
        var a = new Model(url);
        a.getTags(self.setVideoList);
    }

    this.select_channel_id = function(channel_id){
        self.updateActiveChannel(channel_id);
        var url = REST_ALL_VIDEO_URL+channel_id;
        // if(current != ''){
        //     url += '?current='+current;
        // }
        self.current_channel_id = channel_id
        self.select_channel(url);
        
    }

    this.setVideoList = function(result){
        
        console.log(result)
        var params = { channel:result.channel_id };
        var queryString = $.param(params);
        history.pushState('', '', '?'+queryString);
        $("#channelId_hid").attr('value',result.channel_id)
        if(result.videos.length==0){
            // alert('No video for this channel');
            self._renderEmpty(result);
        } else {
            self.videos = result.videos;
            self._render(result);
        }
    }

    this.updateActiveChannel = function(channelID){
        CHANNEL_ID = channelID;
        $("ul.nav-sidebar li").removeClass("active");
        $("ul.nav-sidebar li#channel_"+channelID).addClass("active");
        channel_name = $('#channel_'+channelID).title;
    }

    this.updatePlaylistOrder = function() {
        if($("#videoList").children().length>0){
            var playlists = []
            var pinned_id = $('.pinned_box.selected').attr("data");
            $.each($("#videoList").children(),function(index,item){ playlists.push($(item).attr('data'))})

            $.post( REORDER_URL, { playlist_id : JSON.stringify(playlists),
                                   pinned_id : pinned_id })
            .done(function( data ) {
                //alert( "Data Loaded: " + data );
            });
        }
    }

    this._renderBase = function(channel){
        $("#channeltitle").html(channel.channel_name);
        $("#channelthumbnail").attr("src",channel.icon_url);
    }

    this._render = function(channel){
        self._renderBase(channel)
        var template = '{{#videos}}\
                            <li style="position:relative; padding:0px 0px 10px;" data="{{playlist_id}}" class="is_available_{{isAvailable}}">\
                                <a class="thumbnail" style="margin-bottom:0px;" >\
                                    <img src="{{thumbnail_url}}" class="image_index" style="height:200px;">\
                                    <div class="wrench_box" id="wrench_{{playlist_id}}" data="{{playlist_id}}"><span class="glyphicon glyphicon-wrench" style=""></span></div>\
                                    <div class="trash_box" id="trash_{{playlist_id}}" data="{{id}}"><span class="glyphicon glyphicon-trash" style=""></span></div>\
                                    <div class="pinned_box" id="pin_{{playlist_id}}" data="{{playlist_id}}"><span class="glyphicon glyphicon-pushpin" style=""></span></div>\
                                </a>\
                                <div class="video_title">\
                                    {{name}}<span id="isLive_span{{id}}"></span>\
                                </div>\
                            </li>\
                        {{/videos}}';
        var context = {videos: self.videos};
        var html = Mustache.render(template, context);
        $(self.domElement).html(html);


        $.each(self.videos,function(index,video){
            if(video.isPinned) {
                $('#pin_'+video.playlist_id).addClass("selected");
            }
        });

        $(".wrench_box").click(function(){
            var playlist_id = $(this).attr("data");
            edit_video(playlist_id,user_id);
        });

        $(".pinned_box").click(function(){
            $(".pinned_box").removeClass("selected");
            $(this).addClass("selected");
        });

        $(".trash_box").click(function(){
            video_id = $(this).attr("data");
            delete_video(video_id, self.current_channel_id);
        });
    }

    this._renderEmpty = function(channel){
        self._renderBase(channel)
        template = '<h1>No video for this channel.</h1>'
        $(self.domElement).html(template);
    }
}