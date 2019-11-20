import Semantic.Html 1.0
import QmlWeb 1.0

Modal {
    signal approve()

    RestModel{
        id: rmdSchool
        property var school_list
        url: "/sqool/get_school_list/"
        property alias school_list : cboSchool.items

        onFailed:{
            if(error[0]){
                alert(error[0])
            }
        }
    }

    RestModel{
        id: rmdChannel
        url: "/sqool/create_channel_base64/"
        queryMimeType: 'application/json'
        property var icon
        property var sqool_group
        property var name

        onSaved: {
            modalCreateChannel.hide()
            clear()
            approve()
        }
        onFailed:{
            if(error[0]){
                alert(error[0])
            }
        }
    }

    className: "small"
    Text{
        text: "สร้างห้อง"
        className: "header"
    }
    Container{
        className: "content"
        Form {
            id: form
            validateSetting: {
                return {
                    fields:{
                        โรงเรียน: ['empty'],
                        ชื่อห้อง: ['empty']
                    },
                    prompt: {
                        empty: 'กรุณาระบุ {identifier}'
                    },
                }
            }

            Field {
                label:"โรงเรียน"
                className:"twelve wide required"
                ComboBox{
                    id: cboSchool
                    dataValidate: "โรงเรียน"
                    Component.onCompleted:{
                        rmdSchool.fetch()
                    }
                }
            }
            Field {
                label:"ชื่อห้อง"
                className:"twelve wide required"
                TextBox{
                    id: txtChannelName
                    dataValidate: 'ชื่อห้อง'
                }
            }
            Field {
                label:"รูปห้อง"
                className:"twelve wide"
            }

            Button{
                id: btnUpload
                className: 'red'
                text: 'Upload'
                icon: ""
                doc_label: 'Upload ภาพ'
                onClicked: {
                    uploaderModal.show();
                }
            }
            Message{
                className: 'error'
            }

            Divider {}
            Button {
                id: btnCreate
                tagName: "input"
                className: "primary"
                text: "ตกลง"
                onClicked: {
                    if (form.validateForm()) {
                        rmdChannel.sqool_group = cboSchool.value
                        rmdChannel.name = txtChannelName.text
                        rmdChannel.create()
                    }
                }
                style: "width:22%; margin-left:25%"
            }
            Button {
                className: "deny"
                text: "ยกเลิก"
                htmlAttr: { return {
                      'type': 'button'
                }}
                onClicked: {
                    modalCreateChannel.hide()
                    clear()
                }
                style: "width:22%; margin-right:25%; float: right"
            }
        }
    }
    Modal {
        id:uploaderModal
        className: 'mini'
        Uploader {
            id: uploader
            accept: "image/*"
            onStartUpload: {
                rmdChannel.icon = filebase64
                uploaderModal.hide()
                btnUpload.className = "green"
                btnUpload.icon = "checkmark"
            }
        }
        style: "background: white !important"

        onHidden:{
            uploader.clear()
        }
    }
    function clear(){
        cboSchool.clear()
        txtChannelName.text = ""
        uploader.clear()
        btnUpload.className = "red"
        btnUpload.icon = ""
    }
  }  