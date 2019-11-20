(function(){
    'use strict';
    axios.defaults.xsrfHeaderName = "X-CSRFTOKEN";
    axios.defaults.xsrfCookieName = "csrftoken";

    var app = new Vue({
        el: '#manager',
        delimiters: ['${', '}'],
        data: {
            decisions: [],
            selecting: null,
            edit_url: '',
            playlist_ids: '',
            results:[]
        },
        created: function () {
            var self = this;
            console.log(axios.defaults);
            axios.get('/videos_tag/decision/')
                .then(function (response) {
                    self.decisions = response.data;
                })
                .catch(function (error) {
                    console.log(error);
                });
        },
        methods: {
            select: function (decision) {
                console.log(decision);
                $('#sidebar .list-group-item').removeClass('active');
                $('#menu-'+decision.id).addClass('active');
                this.selecting = decision;
                this.edit_url = '/admin/videos_tagging/tagdecision/' + this.selecting.id + '/';
                this.playlist_ids = '';
                this.results = [];
            },
            exec: function () {
                var self = this;
                axios.post("/videos_tag/decision/" + this.selecting.id + "/exec",
                        {playlist_ids: self.playlist_ids})
                    .then(function(response){
                        console.log(response);
                        self.results = response.data;
                    })
                    .catch(function(error){
                        console.error(error);
                    });
            }
        }
    });
})();
