import Semantic.Html 1.0
import QmlWeb 1.0

Container {
    signal selectChannel(string channel_id, string channel_name)
    signal setLoginStatus(bool isLogin)

    RestModel {
        id: rmd
        property var channel_list
        url: "/sqool/get_channel_list/"
        onFailed: {
            if (xhr.status == 403) {
                setLoginStatus(false)
                alert('กรุณาเข้าสู่ระบบ')
            }
            else {
                setLoginStatus(true)
            }
        }
    }   

    function refresh() {
        rmd.channel_list = []
        rmd.create()
    }

    Dom {
        id: domChannelList
        className: "link items"    
        Repeater {
            model: rmd.channel_list
            Button {
                id: btnChannel
                className: "fluid"
                style: "text-align: left"
                backgroundColor: "transparent"
                onClicked: {
                    domChannelList.children.forEach(function(child) {
                        if (child.$class == "Button") {
                            child.backgroundColor = 'transparent'
                        }
                    })
                    btnChannel.backgroundColor = '#e2e2e2'

                    selectChannel(modelData.id, modelData.name)
                    unread_label.style = "visibility:hidden"
                }
                Grid {
                    Column {
                        className: "two wide"
                        Icon {
                            icon: "large comments top aligned icon"
                        }
                    }
                    Column{
                        className: "six wide"
                        Dom {
                            style: "position:relative;overflow:hidden;padding-bottom:100%;"
                            Image{
                                // className: "rounded tiny"
                                source:modelData.icon
                                style: "position:absolute;"
                            }
                        }   
                    }
                    Column {
                        className: "eight wide"
                        Dom {
                            className: "content"
                            Item {
                                 className: "header"
                                 text: modelData.name
                                 style: "height: 40px;"
                            } 
                            LabelTag {
                                id: unread_label
                                text: modelData.unread
                                link: true
                                backgroundColor: "red"
                                style: (modelData.unread > 0) ? "visibility:visible" : "visibility:hidden"

                                onClicked: {
                                     selectChannel(modelData.id, modelData.name)
                                     unread_label.style = "visibility:hidden"
                                }
                            }

                        }
                    }
                }
            }
        }
        style: "padding-top: 10px;height:90vh;overflow-y: auto;"
    }

    Component.onCompleted: {
        rmd.create()
    }
}
