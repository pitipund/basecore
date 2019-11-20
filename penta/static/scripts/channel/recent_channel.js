function RecentChannel(domElement,RECENT_CHANNEL_URL){
    var object = this;
    this.domElement = domElement;
    this.RECENT_CHANNEL_URL = RECENT_CHANNEL_URL;
    this.channels = [];

    this.fetchChannel = function(){
        $.get(RECENT_CHANNEL_URL,function(reponse){
            //object.channels = reponse.recent_channel;
            object.channels = reponse.top_channel;
            object._render(object.channels)
        });
    }

    this._render = function(channels){
        var template = '<div class="list-group">\
                {{#channels}}\
                    <a href="{{url}}" class="list-group-item" style="background:none;">\
                        <div class="row">\
                            <div class="col-md-3" style="padding-left:10px;">\
                                <img src="{{icon}}" style="width:100px; height:100px;"></img>\
                            </div>\
                            <div class="col-md-3" style="padding-right:0px;">\
                                <div style="height:100px; overflow:hidden; color:#EEE;">\
                                    <h4 style="margin-top:0px;">{{name}}</h4>\
                                    <p>{{detail}}</p>\
                                </div>\
                            </div>\
                        </div>\
                    </a>\
                {{/channels}}\
            </div>';
        var context = {channels:object.channels};
        $(object.domElement).html(Mustache.render(template, context));
    }
}

function RecentAndTopChannel(mostFollowChannelDomElement, recentDomElement, topDomElement, RECENT_CHANNEL_URL){
    var object = this;
    this.mostFollowChannelDomElement = mostFollowChannelDomElement;
    this.recentDomElement = recentDomElement;
    this.topDomElement = topDomElement;
    this.RECENT_CHANNEL_URL = RECENT_CHANNEL_URL;

    this.fetchChannel = function(){
        $.get(RECENT_CHANNEL_URL,function(reponse){
            object._render(reponse)
        });
    }

    this._render = function(reponse){
        most_follow_channels = reponse.most_follow_channel;
        recent_channels = reponse.recent_channel;
        top_channels = reponse.top_channel;
        var template = '{{#channels}}\
                            <a href="{{url}}">\
                            <div class="item darkCyan">\
                                    <img src="{{icon}}" alt="Touch">\
                                    <h3>{{name}}</h3>\
                            </div>\
                            </a>\
                        {{/channels}}';
        var context = {channels:most_follow_channels}
        $(object.mostFollowChannelDomElement).html(Mustache.render(template, context));
         $("#mostFollowChannel").owlCarousel({autoPlay : 5000});

        context = {channels:recent_channels};
        $(object.recentDomElement).html(Mustache.render(template, context));
         $("#recentChannel").owlCarousel({autoPlay : 5000});

        context = {channels:top_channels};
        $(object.topDomElement).html(Mustache.render(template, context));
         $("#topChannel").owlCarousel({ autoPlay : 5000});

    }
}