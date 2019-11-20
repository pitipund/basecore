var monitor = angular.module('monitor', []);

monitor.controller('Controller', ['$scope', function($scope) {
    // do nothing
}]);

monitor.controller('MaintainanceControl', ['$scope', function($scope) {

    $scope.toggle = function(enabled) {
        var message = 'Are you sure you want to DISABLE ALL link?';
        if(enabled) {
            message = 'Are you sure you want to ENABLE ALL link?';
        }
        var proceed = confirm(message);
        if(proceed) {
            document.getElementById('maintainance_toggle').value=enabled;
            document.getElementById('maintainance').submit();
        }
    };

}]);

monitor.directive('errSrc', function() {
    return {
        link: function (scope, element, attrs) {
            element.bind('error', function () {
                if (attrs.src != attrs.errSrc) {
                    var id = attrs.ngSrc.substr(26);
                    id = id.substr(0,id.indexOf('/'));
                    if (scope.$parent.ignoreSS.indexOf(id) == -1) scope.$parent.ignoreSS.push(id);
                    attrs.$set('src', attrs.errSrc);
                    attrs.$set('ng-src', null);
                }
            });
        }
    };
});
//monitor.directive('errSrc', function() {
//  return {
//    link: function(scope, element, attrs) {
//      element.bind('error', function() {
//        if (attrs.src != attrs.errSrc) {
//          attrs.$set('src', attrs.errSrc);
//        }
//      });
//    }
//  }
//});

monitor.controller('ChannelListCtrl', ['$scope', '$http', '$interval', function($scope, $http, $interval) {
    $scope.channels = [];
    $scope.channelSS = {};
    $scope.ignoreSS = [];

    $http({
        method: 'GET',
        url: "/apis/live/v3/"
    })
    .success(function (data, status, headers, config) {
        if (status == 200) {
            // populate initial data with latest_result
            for(var index in data['live_channel']) {
                var channel = data['live_channel'][index];
                if(channel['channel_id'] in latest_result) {
                    channel.status = latest_result[channel['channel_id']];
                } else {
                    channel.status = {};
                }
                channel.restarting = false;
                channel.current_stream_url = channel.stream_url[0];
            }
            $scope.channels = data['live_channel'];
            updateSS();
            $interval(updateSS,6000);
        }
    });

    function updateSS() {
        var index,id;
        for(index in $scope.channels){
            id = $scope.channels[index]['channel_id'].substr(5);
            if($scope.ignoreSS.indexOf(id) == -1)
                $scope.channelSS[$scope.channels[index]['channel_id']] = "http://ss.penta-tv.com/id/" +
                    id + "/default.jpeg?r=" + new Date().toISOString();
        }
    }

    function send_monitor_log(channel, action){
        var name = channel.name;
        return $http({
            method: 'GET',
            url: SEND_MONITOR_LOG_URL+'?name='+name+'&action='+action
        })
        .success(function (data, status, headers, config) {
            if(data.msg == true) {
                channel.status = {
                    'status': data.status,
                    'update_at': data.update_at
                };
                // switch data command
                switch(data.command){
                case 'stop':
                    // already stop, do nothing
                    // if(action=='B'){
                    //     set_new_player(player, data.id, data.url, id, false)
                    // }
                    // if(action=='G'){
                    //     // already stop
                    // }
                    break;
                case 'replay':
                    // workaround to replay
                    channel.current_stream_url = channel.stream_url[0] + '?replay=1';
                    break;
                case 'play':
                    channel.current_stream_url = data.url;
                    break;
                }
            } else{
                alert(channel.name + "\n" + data.result);
                player.sendEvent("PLAY");
            }
            if(action == 'R') {
                channel.restarting = false;
            }
        });
    }

    $scope.good = function(channel) {
        send_monitor_log(channel, 'G');
    };

    $scope.acknowledge = function(channel){
        send_monitor_log(channel, 'A');
    };

    $scope.bad = function(channel){
        send_monitor_log(channel, 'G')
            .success(function(){
                send_monitor_log(channel, 'B');
            });
    };

    $scope.restart = function(channel) {
        confirmMsg = confirm('Are you sure you want to submit action restart?');
        if(confirmMsg) {
            channel.restarting = true;
            send_monitor_log(channel, 'R');
        }
    };

    $scope.edit = function(channel) {
        var id = channel.channel_id.split('_')[1];
        window.open('/admin/curator/curatorsupport/'+id);
    };

}]);

monitor.directive('pentaPlayer', [function(){
    var id = 0;
    function link(scope, element, attrs) {
        var url;
        var player;
        var autostart = 'true';

        function setupRTMPPlayer(element_id, url, width, height) {
            player = $("<video id='video-"+ element_id +"' class='video-js' controls preload='auto' width='" + width+"' height='"+ height +"'" +
                "  data-setup='{}'></video>");
		    $("#"+element_id).append(player);
            videojs('video-'+ element_id, {}, function onPlayerReady() {
                this.play();
            }).src({
                src: url,
                type: 'rtmp/mp4'
            });
        }

        function setupM3U8Player(element_id, url, width, height) {
            //player = $('<embed type="application/x-vlc-plugin" autoplay="yes" loop="yes" target="'+url+'" height="'+height+'" width="'+width+'">');
            player = $("<video id='video-"+ element_id +"' class='video-js' controls preload='auto' width='" + width+"' height='"+ height +"'" +
                    "  data-setup='{}'></video>");
		    $("#"+element_id).append(player);
            videojs('video-'+ element_id, {}, function onPlayerReady() {
                this.play();
            }).src({
                src: url,
                type: 'application/x-mpegURL'
            });
        }

        function setupPentaStream(element_id, url, width, height) {
            function reqListener() {
                var responseURL = this.responseURL;
                console.log(responseURL);
                player = $("<video id='video-"+ element_id +"' class='video-js' controls preload='auto' width='" + width+"' height='"+ height +"'" +
                    "  data-setup='{}'></video>");
                $("#"+element_id).append(player);

                videojs('video-'+ element_id, {}, function onPlayerReady() {
                    this.play();
                }).src({
                    src: responseURL,
                    type: 'application/x-mpegURL'
                });
            }

            var oReq = new XMLHttpRequest();
            oReq.addEventListener("load", reqListener);
            oReq.open("GET", url);
            oReq.send();
        }

        function setupDefaultPlayer(element_id, url, width, height) {
            player = $("<video id='video-"+ element_id +"' class='video-js' controls preload='auto' width='" + width+"' height='"+ height +"'" +
                    "  data-setup='{}'></video>");
            $("#"+element_id).append(player);
            videojs('video-'+ element_id, {}, function onPlayerReady() {
                this.play();
            }).src({
                src: url,
                type: 'video/mp4'
            });
        }

        function updatePlayer() {
            if(!element.attr('id')) {
                ++id;
                element.attr('id', 'player'+id);
            }
            while (element.firstChild){
                element.removeChild();
            }
            element.html('<input value="' + url +'" style="width:100%">');
            if(url.indexOf('rtmp://') == 0) {
                setupRTMPPlayer(element.attr('id'), url, element.attr('width'), element.attr('height'));
            } else if(url.indexOf('.m3u8') > 0) {
                setupM3U8Player(element.attr('id'), url, element.attr('width'), element.attr('height'));
            } else if (url.indexOf('gatekeeper.penta-tv.com/redir/') > 0 ||
                       url.indexOf('gatekeeper.penta.center/redir/') > 0) {
                setupPentaStream(element.attr('id'), url, element.attr('width'), element.attr('height'));
            } else {
                setupDefaultPlayer(element.attr('id'), url, element.attr('width'), element.attr('height'));
            }
        }

        scope.$watch(attrs.pentaPlayer, function(value) {
            url = value;
            if(scope.player_playing) {
                console.log('stopping');
                scope.stop();
                scope.play();
            }
            if(!element.attr('width')) {
                element.attr('width', 272);
            }
            if(!element.attr('height')) {
                element.attr('height', 153);
            }
        });
        scope.player_playing = false;
        scope.stop = function() {
            console.log('stop clicked');
            videojs('video-'+ element.attr('id')).dispose();
            while (element.firstChild){
                element.removeChild();
            }
            scope.player_playing = false;
        };
        scope.play = function() {
            if(scope.player_playing) {
                console.log('already playing');
                return;
            }
            scope.player_playing = true;
            updatePlayer();
        };

    }
    return {
        link: link
    };
}]);

monitor.directive('channelStatus', [function() {
    function link(scope, element, attrs) {
        function updateStatus(status, update_at) {
            element.removeClass();
            switch(status){
                case 'G':
                    element.addClass("label label-success pull-right");
                    element.text('Good at ' + update_at);
                    break;
                case 'A':
                    element.addClass("label label-info pull-right");
                    element.text('Acknowledge at ' + update_at);
                    break;
                case 'R':
                    element.addClass("label label-info pull-right");
                    element.text('Restart at ' + update_at);
                    break;
                case 'L':
                    element.addClass("label label-warning pull-right");
                    element.text('Low Buffer at ' + update_at);
                    break;
                case 'S':
                    element.addClass("label label-warning pull-right");
                    element.text('Skipped at ' + update_at);
                    break;
                case 'B':
                    element.addClass("label label-danger pull-right");
                    element.text('Bad at ' + update_at);
                    break;
            }
        }
        // initialization
        scope.$watch(attrs.channelStatus, function(value) {
            if('status' in value) {
                updateStatus(value.status, value.update_at);
            }
        });
    }
    return {
        link: link,
        template: "<span style='padding: 5px;'></span>"
    }
}]);

monitor.filter('namestrip', function() {
    return function(text) {
        return text.replace(' (ทดลอง)', '');
    };
});

monitor.filter('statusFilter', [function() {
    return function(channels, show) {
        var ret = [], i, l;
        l = channels.length;
        if (!show || !(show.ack || show.bad || show.skip || show.low)) {
            return channels;
        }
        for (i=0; i<l; i++) {
            if (show.bad && channels[i].status.status=='B'){
                ret.push(channels[i]);
            }
            if (show.ack && channels[i].status.status=='A'){
                ret.push(channels[i]);
            }
            if (show.skip && channels[i].status.status=='S'){
                ret.push(channels[i]);
            }
            if (show.low && channels[i].status.status=='L'){
                ret.push(channels[i]);
            }
        }
        return ret;
    };
}]);