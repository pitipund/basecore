import Semantic.Html 1.0
import QmlWeb 1.0

Modal {
      property var current_channel;

      RestModel{
          id: rmdSchool
          url: "/apis/curator/user"
          queryMimeType: "application/json"
      }

      RestModel {
          id: rmdSuggestUser
          property var user_list
          url: "/sqool/get_users_in_group/"+current_channel+"/"
      }   

      RestModel {
          id: rmdWriteUser
          property var user_list
          url: "/sqool/get_writable_users/"+current_channel+"/"
      }  

      RestModel {
          id: rmdReadUser
          property var user_list
          url: "/sqool/get_readonly_users/"+current_channel+"/"
      }  

      RestModel {
          id: rmdSaveSubscribe
          property var user_list
          property var channel_id 
          property var permission
          property var user_id
          url: "/sqool/save_subscribe/"
          onSaved: {
            reloadUser(rmdReadUser)
            reloadUser(rmdWriteUser)
            reloadUser(rmdSuggestUser)
          }
      }  

      function load(){
        reloadUser(rmdSuggestUser)
        reloadUser(rmdReadUser)
        reloadUser(rmdWriteUser)
      }

      function saveSubscribe(user_id, permission){
        rmdSaveSubscribe.user_id = user_id
        rmdSaveSubscribe.channel_id = current_channel
        rmdSaveSubscribe.permission = permission
        rmdSaveSubscribe.create()
      }

      function reloadUser(rmd){
        rmd.user_list=[]
        rmd.create()
      }

      className: "large"
      Text{
          text: "จัดการสมาชิก"
          className: "header"
      }
      Container{
        className: "content"
        Grid{
          Column {
            className: "five wide"
            Text{
                text: "Suggest List"
                className: "header"
            }
            Dom {
              className: "celled list"
              Repeater {
                  model: rmdSuggestUser.user_list
                  Item {
                    Image{
                        className: "avatar"
                        source:modelData.image
                        style: "width: 10%"
                    }
                    Dom {
                        className: "middle aligned content"
                        Text {
                             text: modelData.full_name
                        }
                      Button{
                          id: btnWrite
                          className: "circular small"
                          icon: "write"
                          onClicked: {
                            saveSubscribe(modelData.id, 'true')
                          }
                          style: "float: right"
                      }
                      Button{
                          id: btnRead
                          className: "circular small"
                          icon: "unhide"
                          onClicked: {
                            saveSubscribe(modelData.id, 'false')
                          }
                          style: "float: right"
                      }
                      // style: "width: 50%"
                    }

                  }
              }
            }
            style: "padding-top: 10px;height:50vh;overflow-y: auto;"

          }
          Column {
            className: "one wide"
          }
          Column {
            className: "five wide"
            Icon {
                className: "circular teal unhide"
            }
            Text{
                text: "Readonly"
                className: "header"
            }
            Dom {
              className: "celled list"
              SearchBox {
                id: sbxReadUser
                placeholder: "เพิ่มสมาชิกด้วยไอดี"
                baseURL: "/sqool/get_user/"
                targetField: 'username'
                title: 'username'
                description: 'full_name'
                minCharacters: 2
                icon: 'add user'
                onSelected: {
                    saveSubscribe(sbxReadUser.selectedRow.id, 'false')
                }
                style: "margin-bottom: 5px"
              }
              Repeater {
                  model: rmdReadUser.user_list
                  Dom {
                    className: "teal image label"
                    Image {
                      source: modelData.user.image
                    }
                    Text {
                         text: modelData.user.full_name
                    }
                    Icon {
                      className: "delete icon"
                      onClicked: {
                        saveSubscribe(modelData.user.id, '---')
                      }
                    }
                    style: "margin-top: 5px"
                  }
              }
            }
            style: "padding-top: 10px;height:50vh;overflow-y: auto;"

          }
          Column {
            className: "five wide"
            Icon {
                className: "circular orange write"
            }
            Text{
                text: "Writable"
                className: "header"
            }
            Dom {
              className: "celled list"
              SearchBox {
                id: sbxWriteUser
                placeholder: "เพิ่มสมาชิกด้วยไอดี"
                size: "mini"
                baseURL: "/sqool/get_user/"
                targetField: 'username'
                title: 'username'
                description: 'full_name'
                minCharacters: 2
                icon: 'add user'
                style: "margin-bottom: 5px"
                onSelected: {
                    saveSubscribe(sbxWriteUser.selectedRow.id, 'true')
                }
              }
              Repeater {
                  model: rmdWriteUser.user_list
                  Dom {
                    className: "orange image label"
                    Image {
                      source: modelData.user.image
                    }
                    Text {
                         text: modelData.user.full_name
                         value: modelData.user.id
                    }
                    Icon {
                      className: "delete icon"
                      onClicked: {
                        saveSubscribe(modelData.user.id,'---')
                      }
                    }
                    style: "margin-top: 5px"
                  }
              }
            }
            style: "padding-top: 10px;height:50vh;overflow-y: auto;"
          }
        }
      }
      Component.onCompleted: {
        load()
      }
  }  