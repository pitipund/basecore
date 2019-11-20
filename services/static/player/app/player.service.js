(function (){

	angular.module('player')
		.factory('PlayerService', PlayerService);

	PlayerService.$inject = ['$http'];

	function PlayerService($http) {

		var PlayerService = {
			getPlaylist: getPlaylist,
			getChannel: getChannel,
			getChannelPlaylist: getChannelPlaylist,
			setStartEndForPlaylist: setStartEndForPlaylist,
			setVideoPermission: setVideoPermission,
			setAllVideosPermission: setAllVideosPermission,
			listQuestionMessage: listQuestionMessage,
			listQuestioner: listQuestioner,
			sendQuestionMessage: sendQuestionMessage,
			setOpenForQuestion: setOpenForQuestion,
			addSuggestPlaylistById: addSuggestPlaylistById,
			removeSuggestById: removeSuggestById
		};

		return PlayerService;

		function getPlaylist(playlist_id) {
			return $http.get('/api/v2/playlist/'+playlist_id+'/');
		}	

		function getChannel(channel_id) {
			return $http.get('/api/v2/channel/'+channel_id+'/');
		}

		function getChannelPlaylist(channel_id, page) {
			return $http.get('/api/v2/channel/'+channel_id+'/playlist/?page='+page+'&per_page=25&reverse=true');
		}

		function setStartEndForPlaylist(playlist_id, params) {
			return $http.post('/api/v2/playlist/play_position/'+playlist_id+'/', params);
		}

		function setVideoPermission(playlist_id, params) {
			return $http.post('/api/v2/playlist/set_permission/'+playlist_id+'/', params);	
		}

		function setAllVideosPermission(channel_id, params) {
			return $http.post('/api/v2/channel/set_permission_playlists/'+channel_id+'/', params);	
		}		

		function listQuestionMessage(playlist_id, from_id) {
			url = '/api/v2/question/list_message/'+playlist_id+'/'
			if(from_id) {
				url = url+'?from='+from_id;
			}
			return $http.get(url);	
		}

		function listQuestioner(playlist_id) {
			return $http.get('/api/v2/question/list_questioner/'+playlist_id+'/');	
		}

		function sendQuestionMessage(playlist_id, params) {
			return $http.post('/api/v2/question/send_message/'+playlist_id+'/', params);	
		}		

		function setOpenForQuestion(playlist_id, params) {
			return $http.post('/api/v2/question/set_openquestion/'+playlist_id+'/', params);	
		}

		function addSuggestPlaylistById(thread_id, params) {
			return $http.post('/api/v2/question/add_suggest_playlist/'+thread_id+'/', params);	
		}
		
		function removeSuggestById(thread_id, params) {
			return $http.post('/api/v2/question/remove_suggest_playlist/'+thread_id+'/', params);	
		}
	}

})();