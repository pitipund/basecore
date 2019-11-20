import Semantic.Html 1.0
import QmlWeb 1.0
import "../Common/Util.js" as Util

Container {
    property var current_channel;
    property var upload_path
    property var upload_fileName
  
    Grid {
        Column {
            className: "four wide"
            ChannelList {
                id: channelList
                onSelectChannel: {
                    current_channel = channel_id
                    channel_header.text = channel_name
                    rmdMessageList.message_list=[]
                    rmdMessageList.create()
                    btnManageSubscriber.style = 'display: block'
                }
                onSetLoginStatus: {
                    if (isLogin){
                        btnCreateChannel.enabled = true
                    } else {
                        btnCreateChannel.enabled = false
                    }
                }
            }
              Button{
                  id: btnCreateChannel
                  text: "สร้างห้อง"
                  className: "big"
                  onClicked: {
                      modalCreateChannel.show()
                  }
                  style: "width:100%; margin-top: 20px;"
              }
        }
        Column {
           className: "ten wide"
           /*style: "background-color: blue"
           Button {
              text: "call me"
          }*/
          
          Dom {
              RestModel {
                 id: rmdMessageList 
                 property var message_list
                 url: "/sqool/get_message_channel/" + current_channel + '/'
                 onSaved: {
                    //alert(messageList.dom.scrollHeight+500)
                    contentRow.visible = true
                    contentFile.dom.value=''
                    contentTxt.text=''
                    //messageList.dom.scrollTop = messageList.dom.scrollHeight+500;
                 }
              }
          }
          Dom {
              RestModel {
                 id: writeMessage
                 property string content: contentTxt.text
                 property string content_type: "text"
                 url: "/sqool/write_message_channel/" + current_channel + '/'
                 onSaved: {
                     rmdMessageList.message_list=[]
                     rmdMessageList.create()
                     contentTxt.loading = false
                 }
              }
          }
          Dom {
            id: channel_header
            className: "center aligned header"
            text: ""
          }
          Dom{
             id : messageList
             Repeater {
                  model: rmdMessageList.message_list
                  Dom   {
                        Component.onCompleted: {
                            if(rmdMessageList.message_list.indexOf(modelData) == rmdMessageList.message_list.length-1){
                                messageList.dom.scrollTop = messageList.dom.scrollHeight+500;
                            }
                        }

                        Message{
                            Dom{
                                className: "content ui grid"
                                Image{
                                    className: "tiny"
                                    source: modelData.author.image
                                    style : "width:40px;"
                                }
                                Dom {
                                    className: "content"
                                    Text{
                                        className: "header"
                                        text: modelData.author.username
                                    }
                                }
                            }
                            Br{}
                            Image{
                                //source : (modelData.content_type=="video") ? modelData.content_file.replace(modelData.content , modelData.content.split('.')[0]+"_thumbnail.png")  : modelData.content_file
                                displayNone: (modelData.content_type != "image")
                                source : (modelData.content_type=="image") ? modelData.content_file : ""
                            }
                            ImageButton{
                                displayNone: (modelData.content_type != "file")
                                source:"/media/images/file_icon.png"
                                text:"download"
                                className:"small"
                                onClicked:{
                                    window.location.href = modelData.content_file
                                }
                            }
                            Text{
                                text: (modelData.content_type=="text" || modelData.content_type=="file") ? modelData.content : ""
                            }
                            Dom {
                                tagName: "video"
                                displayNone: (modelData.content_type != "video")
                                htmlAttr: {
                                    return {
                                        'width': "100%",
                                        'height': "100%",
                                        'controls':''
                                    }
                                }
                                Dom {
                                    tagName: "source"
                                    htmlAttr: { 
                                        return {
                                            'src': modelData.content_file,
                                            'type': "video/" + modelData.content.split('.')[1]
                                        }
                                    }
                                }
                            }
                            Br{}
                            Br{}
                            Text{
                                text: moment(modelData.send_at).format("LLL")
                                style: "font-size:10px"
                            }
                        }
                        Br {}
                  } //End dom
              }//End Repeater
              style: "height:80vh;overflow-y: auto;"
          }//End Dom

          Form {
              Fields {
                  id: contentRow
                  visible: false
                  Field {
                      className: "two wide"
                      Button{
                          id: uploadBtn
                          text: "+"
                          onClicked: {
                              uploadChoice.show()
                          }
                          style: "width:100%;"
                      }
                  }
                  Field {
                      className: "twelve wide"
                      TextBox {
                          id: contentTxt
                          placeholder: "write message here"
                          size: "huge"
                          onEntered:{
                              contentTxt.loading = true
                              writeMessage.create()
                          }
                      }
                  }
                  Field {
                      className: "two wide"
                      Button{
                          id: sendBtn
                          text: "send"
                          onClicked: {
                              if (contentTxt.text != ""){
                                  contentTxt.loading = true
                                  writeMessage.create()
                              }
                          }
                      }
                      style: "width:100%;"
                  }
              }
          }
        }
          Column {
            Button{
                  id: btnManageSubscriber
                  className: "massive"
                  icon: "users"
                  onClicked: {
                      modalManageSubscriber.current_channel = current_channel
                      modalManageSubscriber.load()
                      modalManageSubscriber.show()
                  }
                  style: "display: none"
              }
          }
    }
    Modal {
        id: uploadChoice
        className: "tiny"
        Button {
                text: "Upload Image"
                onClicked: {
                    content_type.dom.value = 'image'
                    uploadLabel.text = "select upload image file"
                    uploadChoice.hide()
                    upload.show()
                }
                style: "width:100%;"
        }
        Br{}
        Button {
                text: "Upload Video"
                onClicked: {
                    content_type.dom.value = 'video'
                    uploadLabel.text = "select upload video file"
                    uploadChoice.hide()
                    upload.show()
                }
                style: "width:100%;"
        }
        Br{}
        Button {
                text: "Upload File"
                onClicked: {
                    content_type.dom.value = 'file'
                    uploadLabel.text = "select upload file"
                    uploadChoice.hide()
                    upload.show()
                }
                style: "width:100%;"
        }
        style: "width:20%;"
    }

    Modal {
        id: upload
        className: "tiny"
        Form {
            tagName: "form"
            htmlAttr: { return {
                'id': 'mainForm',
                'method': 'POST',
                'target': 'uploadFrame',
                'action': '/sqool/post_content_channel/' + current_channel + '/',
                'enctype' : 'multipart/form-data'
            }}
            Br{}
            Text{
                id: "uploadLabel"
                text: "select upload file"
                style: "font-size:20px;"
            }
            Dom {
                tagName: "input"
                htmlAttr: { return {
                    'type': 'hidden',
                    'name': 'csrfmiddlewaretoken',
                    'value': Util.getCookie('csrftoken'),
                }}
            }
           Dom {
                id: contentFile
                tagName: "input"
                htmlAttr: { return {
                    'type': 'file',
                    'id': 'contentFile',
                    'name': 'content'
                }}
            }
           Dom {
                id: content_name
                tagName: "input"
                htmlAttr: { return {
                    'type': 'hidden',
                    'name': 'content_name',
                    'value': ''
                }}
            }
           Dom {
                id: content_ext
                tagName: "input"
                htmlAttr: { return {
                    'type': 'hidden',
                    'name': 'content_ext',
                    'value': ''
                }}
            }
           Dom {
                id: content_type
                tagName: "input"
                htmlAttr: { return {
                    'type': 'hidden',
                    'name': 'content_type',
                    'value': 'image'
                }}
            }
            Button {
                tagName: "input"
                text: "upload"
                htmlAttr: { return {
                   'type': 'button'
                }}
                onClicked: {
                      upload_path = contentFile.dom.value
                      upload_fileName = upload_path.substr(upload_path.lastIndexOf("\\")+1, upload_path.length);
                      content_name.dom.value = upload_fileName.split('.')[0]
                      content_ext.dom.value = '.' + upload_fileName.split('.')[1]

                      var is_upload = Util.submitForm()
                      
                      if(is_upload){
                          rmdMessageList.message_list=[]
                          rmdMessageList.create()
                          upload.hide()  
                      }
                } 
           }
           Button{
                htmlAttr: { return {
                    'type': 'button'
                }}
                text: "exit"
                onClicked: {
                    rmdMessageList.message_list=[]
                    rmdMessageList.create()
                    upload.hide()  
                }
           }
           Dom {
                id: frame
                tagName: "iframe"
                htmlAttr: { return {
                    'name': 'uploadFrame'
                }}
                style: "width:1px;height:1px;visibility:hidden;"
           }
       }
    } 

    CreateChannel {
      id: modalCreateChannel
      onApprove: {
        channelList.refresh()
      }
    }

    ManageSubscriber {
      id: modalManageSubscriber
    }
}
