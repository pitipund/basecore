function getParameterByName(name) {
    name = name.replace(/[\[]/, "\\[").replace(/[\]]/, "\\]");
    var regex = new RegExp("[\\?&]" + name + "=([^&#]*)"),
        results = regex.exec(location.search);
    return results === null ? "" : decodeURIComponent(results[1].replace(/\+/g, " "));
}

function TagModel(GET_TAGS_URL){
    this.GET_TAGS_URL = GET_TAGS_URL;

    this.getTags = function(callback) {
        $.get(GET_TAGS_URL, function(result){
            callback(result['tag']);
        });
    }
}


window.onpopstate = function(e){
    console.log('popstate fired!');
    console.log(event);
    this.tagList.setTagsById(getParameterByName("tag_id"));
}

function TagList(domElement){
    //constructor
    this.tags = [];
    this.domElement = domElement;
    this.selectedTag;

    //register event listener
    $(this.domElement).on("click", "li", function() {
        $('#tagList > li').removeClass("active");
        $(this).addClass('active');
        $(domElement).trigger("select", [$(this).data("tag")]);
        window.history.pushState({}, "penta", '?tag_id='+$(this).data("id"))
    });

    this.setTagsById = function(tag_id) {
        for(index in this.tags) {
            var tag = this.tags[index]
            if (tag.tag_id == tag_id) {
                this.setTags(this.tags, this.tags[index])
            }
        }
    }

    this.setTags = function(tags, selectedTag){
        this.tags = tags;
        this.selectedTag = selectedTag;
        $(this.domElement).trigger("select", [selectedTag]);
        this._render();
    };

    this._render = function() {
        var object = this;
        var template = '{{#tags}} <li class="large" data-id="{{tag_id}}"><a><span>{{tag_name}}</span></a></li>{{/tags}}';
        var context = {tags: this.tags};
        $(this.domElement).html(Mustache.render(template, context));

        $(this.domElement).children("li").each(function(index) {
            var tag = object.tags[index];
            $(this).data("tag", tag);  //embed tag object into dom element

            if(tag.tag_name == object.selectedTag.tag_name) {
                $(this).addClass('active'); //toggle selected tag
            }
        });
    };
}

function BrowseController(tagModel, tagList) {
    var object = this;
    this.tagModel = tagModel;
    this.tagList = tagList;

    this.tagModel.getTags(function(tags) {
        var tag_id = getParameterByName("tag_id");
        var default_index = 0;
        if(tag_id){
            for(index in tags) {
                var tag = tags[index];
                if(tag.tag_id==tag_id) {
                    default_index = index;
                    break;
                }
            }
        }

        object.selectedTag = tags[default_index];
        object.tagList.setTags(tags, tags[default_index]);
        
    });

}

function ChannelList(domElement){
    var object = this;
    var initOpacity = 0.0;
    this.domElement = domElement;
    this.selectedTag;
    this.channels;
    this.favorite_channels;


    $(this.domElement).on("click", "button.btn-follow", function() {
        var channel = $(this).data("channel");
        var url = SUBSCRIBE_CHANNEL + "?channelid={channel_id}&type={type}";
        if(channel.id.indexOf('channel_')>-1){
            var channel_id = channel.id.substr("channel_".length);
        }
        else if(channel.id.indexOf('live_')>-1){
            var channel_id = channel.id;
        }
        url = url.replace("{channel_id}",channel_id);
        url = url.replace("{type}",channel.isSubscribe?"1":"0");
        $.get(url,function(result){
            if(page_header=='browse'){
                object.setSelectedTag(object.selectedTag);
            }
            else if(page_header=='search'){
                object.setSelectedSearch(word);
            }
            $(object.domElement).trigger("followChanged", [channel]);
        });
    });

    this.getChannels = function(){
        return object.channels;
    }

    this.setSelectedTag = function (selectedTag){
        if(this.selectedTag==selectedTag)
            initOpacity = 1.0;
        else 
            initOpacity = 0.0;    
        this.selectedTag = selectedTag;
        var url = GET_CHANNELS_URL.replace("TAG_ID",selectedTag.tag_id);
        $.get(url, function(result){
            object.channels = result.channel;
            object._render(result.channel);
        });
    }

    this.setSelectedSearch = function (selectedSearch){
        this.selectedSearch = selectedSearch;
        if(selectedSearch==''){
            selectedSearch = 'all';
        }
        //convert html speacial charactor to normal string eg. &#39; => '
        var span = document.createElement('span');
        span.innerHTML = selectedSearch;
        selectedSearch =  span.innerHTML;
        //////////////////////////////////////////////////////////////////
        var url = GET_SEARCH_URL.replace("WORD", selectedSearch);
        $.get(url, function(result){
            object.channels = result.channel;
            object._render(result.channel);
            $(object.domElement).trigger("searchCompleted", [result.channel]);
        });
    }

    this._render = function(channels){
        var template = '{{#channels}}\
                            <div class="col-xs-6 col-sm-4 col-md-4 col-lg-3 channelView" style="opacity:'+initOpacity+'; padding:0px 5px 10px;">\
                                <a class="thumbnail" href="{{url}}" style="margin-bottom:0px;" >\
                                    <img src="{{image}}" class="image_index" style="height:200px;">\
                                </a>\
                                <div class="channel_title">\
                                    {{name}}<span id="isLive_span{{id}}"></span>\
                                    <button type="button" class="btn-follow btn btn-success pull-right">'+followText+'</button>\
                                </div>\
                            </div>\
                        {{/channels}}';
        var context = {channels: channels};
        var html = Mustache.render(template, context);
        $(this.domElement).html(html);

        if (initOpacity==0.0) {
            $('.channelView').animate({
                opacity: 1.0
            }, 700, function(){
                // Animation complete.
            });
            initOpacity=1;
        }

        $("div.channelView").children("div").each(function(index) {
            var buttonFollow = $(this).children("button.btn-follow")[0];
            var channel = object.channels[index];
            if(channel.isLive == "True"){
                document.getElementById('isLive_span'+channel.id).innerHTML = '<font style="color:red;">('+LIVE_TEXT+')</font>';
            }
            $(buttonFollow).data("channel", channel);
            if(channel.isSubscribe==true){
                $(buttonFollow).removeClass('btn-success').addClass('btn-danger');
                $(buttonFollow).text(unfollowText);
            }
        });
    }
}