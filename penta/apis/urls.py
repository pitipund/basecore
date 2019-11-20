from django.conf.urls import url
from his.penta.apis import views

urlpatterns = [
    url(r'^apis/add_stream/$', views.add_stream, name='apis_add_stream'),
    url(r'^apis/add_video/$', views.add_video, name='apis_add_video'),
    url(r'^apis/add_kodhit/$', views.add_kodhit, name='apis_add_kodhit'),
    url(r'^apis/add_outstanding/$', views.add_outstanding, name='apis_add_outstanding'),

    url(r'^apis/tags/query/$', views.tags_query, name='apis_tags_query'),
    url(r'^apis/tags/add/$', views.tags_add, name='apis_tags_add'),
    url(r'^apis/search/$', views.SearchList.as_view()),
    url(r'^apis/youtube_playlist/(?P<playlist_id>.+)', views.YoutubePlaylist.as_view()),

    # --- new api v2 --- #

    url(r'^api/docs', views.api_docs, name='api_docs'),

    # user
    url(r'^api/v2/account/create/$', views.api_v2_account_create, name='api_v2_account_create'),
    url(r'^api/v2/account/create_fb/$', views.APIv2CreateFBView.as_view(), name='api_v2_account_create_fb'),
    url(r'^api/v2/account/create_guest/$', views.APIv2CreateGuestView.as_view(), name='api_v2_account_create_guest'),
    url(r'^api/v2/account/login/$', views.api_v2_account_login, name='api_v2_account_login'),
    url(r'^api/v2/account/login//$', views.api_v2_account_login, name='api_v2_account_login_hotfix'),
    url(r'^api/v2/account/logout/$', views.api_v2_account_logout, name='api_v2_account_logout'),
    url(r'^api/v2/account/update_visit_follow_page/$', views.api_v2_account_update_visit_follow_page, name='api_v2_account_update_visit_follow_page'),
    url(r'^api/v2/account/mostcontributers/$', views.AccountMostContributer.as_view(), name='api_v2_account_mostcontributers'),
    url(r'^api/v2/account/profile_picture/$', views.AccountProfilePictureAPIView.as_view(), name='api_v2_account_profile_picture'),


    # tag
    url(r'^api/v2/tag/highlight_list/$', views.api_v2_tag_highlight, name='api_v2_tag_highlight'),
    url(r'^api/v2/tag/manage/$', views.APIv2TagManagerView.as_view(), name='api_v2_tag_manager'),
    url(r'^api/v2/tag/query/$', views.api_v2_tag_query, name='api_v2_tag_query'),
    url(r'^api/v2/tag/add/$', views.api_v2_tag_add, name='api_v2_tag_add'),

    # channel
    url(r'^api/v2/channel/add_pin_queue/$', views.api_v2_add_pin_queue, name='api_v2_add_pin_queue'),
    url(r'^api/v2/channel/latest_channels/$', views.api_v2_latest_channels, name='api_v2_latest_channels'),
    url(r'^api/v2/channel/latest_channels_by_user/$', views.api_v2_latest_channels_by_user, name='api_v2_latest_channels_by_user'),
    url(r'^api/v2/channel/highlight/$', views.api_v2_highlight_channel, name='api_v2_channel_highlight'),
    url(r'^api/v2/channel/random/$', views.api_v2_random_channel, name='api_v2_random_channel'),
    url(r'^api/v2/channel/tag/(?P<tag_id>\d+)/$', views.api_v2_get_channel_from_tag, name='api_v2_channel_tag'),

    url(r'^api/v2/channel/follow/(?P<channel_id>\d+)/$', views.api_v2_follow_channel, name='api_v2_channel_follow'),
    url(r'^api/v2/channel/unfollow/(?P<channel_id>\d+)/$', views.api_v2_unfollow_channel, name='api_v2_channel_unfollow'),
    url(r'^api/v2/channel/subscribe/(?P<channel_id>\d+)/$', views.api_v2_subscribe_channel, name='api_v2_channel_subscribe'),
    url(r'^api/v2/channel/unsubscribe/(?P<channel_id>\d+)/$', views.api_v2_unsubscribe_channel, name='api_v2_channel_unsubscribe'),
    url(r'^api/v2/channel/(?P<channel_id>\d+)/playlist/$', views.APIv2ChannelPlaylistView.as_view(), name='api_v2_channel_playlist_view'),
    url(r'^api/v2/channel/((?P<channel_id>\d+)/)?$', views.APIv2ChannelView.as_view(), name='api_v2_channel_view'),
    url(r'^api/v2/channel/remove_playlist/(?P<channel_id>\d+)/$', views.api_v2_remove_playlist_channel, name='api_v2_remove_playlist_channel'),
    url(r'^api/v2/channel/reorder_playlist/(?P<channel_id>\d+)/$', views.api_v2_reorder_playlist_channel, name='api_v2_reorder_playlist_channel'),
    url(r'^api/v2/channel/inverseorder_playlist/(?P<channel_id>\d+)/$', views.api_v2_orderbyalphabet_playlist_channel, name='api_v2_orderbyalphabet_playlist_channel'),
    url(r'^api/v2/channel/pattern_order_playlist/(?P<channel_id>\d+)/$', views.api_v2_orderby_pattern_playlist_channel, name='api_v2_orderby_pattern_playlist_channel'),
    url(r'^api/v2/channel/set_permission_playlists/(?P<channel_id>\d+)/$', views.api_v2_channel_set_permission_for_all_playlists, name='api_v2_channel_set_permission_for_all_playlists'),
    url(r'^api/v2/channel/createinitdata/$', views.api_v2_channel_create_init_data, name='api_v2_channel_create_init_data'),

    # playlist
    url(r'^api/v2/playlist/latest_videos/$', views.APIv2PlaylistLatestVideo.as_view(), name='api_v2_playlist_latest_videos'),
    url(r'^api/v2/playlist/latest_videos_by_user/$', views.api_v2_playlist_latest_videos_by_user, name='api_v2_playlist_latest_videos_by_user'),
    url(r'^api/v2/playlist/highlight/$', views.api_v2_highlight_playlist, name='api_v2_playlist_highlight'),
    url(r'^api/v2/playlist/saved_unwatched/$', views.api_v2_saved_unwatched, name='api_v2_saved_unwatched'),
    url(r'^api/v2/playlist/tag/(?P<tag_id>\d+)/$', views.api_v2_get_playlist_from_tag, name='api_v2_playlist_tag'),

    url(r'^api/v2/playlist/like/(?P<playlist_id>\d+)/$', views.api_v2_playlist_like, name='api_v2_playlist_like'),
    url(r'^api/v2/playlist/unlike/(?P<playlist_id>\d+)/$', views.api_v2_playlist_unlike, name='api_v2_playlist_unlike'),
    url(r'^api/v2/playlist/save/(?P<playlist_id>\d+)/$', views.api_v2_playlist_save, name='api_v2_playlist_save'),
    url(r'^api/v2/playlist/save_ex/(?P<src>.+)/(?P<src_id>.+)/$', views.api_v2_playlist_save_ex, name='api_v2_playlist_save_ex'),
    url(r'^api/v2/playlist/unsave/(?P<playlist_id>\d+)/$', views.api_v2_playlist_unsave, name='api_v2_playlist_unsave'),
    url(r'^api/v2/playlist/unsave_ex/(?P<src>.+)/(?P<src_id>.+)/$', views.api_v2_playlist_unsave_ex, name='api_v2_playlist_unsave_ex'),
    url(r'^api/v2/playlist/followed/$', views.api_v2_playlist_followed, name='api_v2_playlist_followed'),
    url(r'^api/v2/playlist/((?P<playlist_id>\d+)/)?$', views.APIv2PlaylistView.as_view(), name='api_v2_playlist_view'),
    url(r'^api/v2/playlist/watched/(?P<playlist_id>\d+)/$', views.api_v2_playlist_watched, name='api_v2_playlist_watched'),

    url(r'^api/v2/playlist/play_position/(?P<playlist_id>\d+)/$', views.api_v2_playlist_play_position, name='api_v2_playlist_play_position'),
    url(r'^api/v2/playlist/set_permission/(?P<playlist_id>\d+)/$', views.api_v2_playlist_set_permission, name='api_v2_playlist_set_permission'),
    url(r'^api/v2/playlist/user_might_watch/$', views.api_v2_playlist_user_might_watch, name='api_v2_playlist_user_might_watch'),

    # link
    url(r'^api/v2/link/tag/(?P<tag_id>\d+)/$', views.api_v2_get_link_from_tag, name='api_v2_link_tag'),

    # suggestion
    url(r'^api/v2/suggestion/count_unread/((?P<channel_id>\d+)/)?$', views.api_v2_user_suggestion_unread_count,
        name='api_v2_suggestion_count_view'),
    url(r'^api/v2/suggestion/((?P<channel_id>\d+)/)?$', views.APIv2UserSuggestionView.as_view(),
        name='api_v2_suggestion_view'),
    url(r'^api/v2/suggestion/(?P<action>\w+)/(?P<suggestion_id>\d+)/$', views.APIv2UserSuggestionActionView.as_view(),
        name='api_v2_suggestion_edit_view'),

    # search
    url(r'^api/v2/search/$', views.api_v2_search_playlist, name='api_v2_search_playlist'),
    url(r'^api/v2/search_channel/$', views.api_v2_search_channel, name='api_v2_search_channel'),
    url(r'^api/v2/search_r2/$', views.api_v2_search_r2, name='api_v2_search_r2'),
    url(r'^api/v2/search_history/$', views.api_v2_get_search_history, name='api_v2_search_history'),

    # topic
    url(r'^api/v2/hottopic/$', views.api_v2_hottopic, name='api_v2_hottopic'),
    url(r'^api/v2/hotshared/$', views.api_v2_hotshared, name='api_v2_hotshared'),

    # question
    url(r'^api/v2/question/list_message/(?P<playlist_id>\d+)/$', views.api_v2_question_list_message, name='api_v2_question_list_message'),
    url(r'^api/v2/question/list_questioner/(?P<playlist_id>\d+)/$', views.api_v2_question_list_questioner, name='api_v2_question_list_questioner'),
    url(r'^api/v2/question/send_message/(?P<playlist_id>\d+)/$', views.api_v2_question_send_message, name='api_v2_question_send_message'),
    url(r'^api/v2/question/set_openquestion/(?P<playlist_id>\d+)/$', views.api_v2_question_set_open, name='api_v2_question_set_open'),
    url(r'^api/v2/question/add_suggest_playlist/(?P<thread_id>\d+)/$', views.api_v2_question_add_suggest_playlist, name='api_v2_question_add_suggest_playlist'),
    url(r'^api/v2/question/remove_suggest_playlist/(?P<suggest_id>\d+)/$', views.api_v2_question_remove_suggest_playlist, name='api_v2_question_remove_suggest_playlist'),

    # email
    url(r'^api/v2/email/template/((?P<template_id>\d+)/)?$', views.APIv2EmailTemplateView.as_view(), name='api_v2_email_template_view'),
    url(r'^api/v2/email/channel/(?P<channel_id>\d+)/$', views.APIv2EmailChannelView.as_view(), name='api_v2_email_channel_view'),
    url(r'^api/v2/email/(?P<email_id>\d+)/upload_image/$', views.api_v2_email_upload_image, name='api_v2_email_upload_image'),
    url(r'^api/v2/email/(?P<email_id>\d+)/send/$', views.api_v2_email_send, name='api_v2_email_send'),
    url(r'^api/v2/email/((?P<email_id>\d+)/)?$', views.APIv2EmailView.as_view(), name='api_v2_email_view'),

    # chat
    url(r'^api/v2/chat/live/send_message/$', views.APIv2ChatLiveView.as_view(), name='api_v2_chat_live_view'),

    # util
    url(r'^api/v2/util/video_description/$', views.api_v2_util_video_description, name='api_v2_util_video_description')
]
