import Semantic.Html 1.0
import QmlWeb 1.0
import DGrid 1.0
import "../Common" as Common
import "../Common/Util.js" as Util


Common.CardLayout {
    property var current_channel;
    property var upload_path;
    property var upload_fileName;

    title: 'นัดหมาย'
    hideCloseButton: true
    headerColor: 'blue'
    toggleCard: false
    id: root

    function searchAndFilter() {
        console.log("dtbFromDate")
        console.log(dtbFromDate.text)
        console.log("ttbTime1")
        console.log(ttbTime1)

        var start = ""
        var end = ""

        var tmp_startdate = dtbFromDate.toDashFormat()
        var tmp_starttime = ""
        var tmp_enddate = dtbToDate.toDashFormat().replace()
        var tmp_endtime = ""

        if(ttbTime1.text){
            tmp_starttime = ttbTime1.text.replace(":","%3A") + "%3A00"
        }else{
            tmp_starttime = "00%3A00%3A00"
        }
        if(ttbTime2.text){
            tmp_endtime = ttbTime2.text.replace(":","%3A") + "%3A00"
        }else{
            tmp_endtime = "23%3A59%3A59"
        }

        if(tmp_startdate > tmp_enddate){
            alert("วันที่เริ่มค้นหา มากกว่าวันที่สิ้นสุด");
        }else{
            start = tmp_startdate + "T" + tmp_starttime + "Z"
            end   = tmp_enddate   + "T" + tmp_endtime   + "Z"

            grdAvailableSlot.model = []
            console.log(userModel.url)
            userModel.url  =  '/appointment/get_available_timeslot_by_time?start=' +start+ '&end=' +end+ '&format=json'
            userModel.fetch()
        }



    }

    RestModel {
        id: createAppModel
        queryMimeType: 'application/json'

        property var provider_id
        property var availableslot_id
        property var user_technician
        property var name
        property var remark
        property var timeslot
        property var first_name
        property var last_name
        property var email
        property var tel
        property var premise_name
        property var address1
        property var address2
        property var province
        property var city
        property var district
        property var zipcode
        property var map_image

        url: "/appointment/create_airtech_appointment/"

        onSaved: {
            root.loading = false
            Util.alert('บันทึกข้อมูลสำเร็จ', 'green')
        }
        onFailed:{
            root.loading = false
            if(error[0]){
                alert(error[0])
            }
        }
    }


    RestModel{
        id: userModel
        url: '/appointment/get_available_timeslot_by_time?start=2017-08-12T12%3A00%3A00Z&end=2017-08-12T12%3A00%3A00Z&format=json'
        property alias result: grdAvailableSlot.model
        onFetched: {
            root.loading = false
            console.log(result)
            for (var key in result) {
                console.log(key);
                if (result.hasOwnProperty(key)) {
                    console.log(result[key].id)
                    console.log(result[key].provider);
                    console.log(result[key].provider.content_object.user);
               }
            }
        }
        onFailed: {
            root.loading = false
            alert('เกิดข้อผิดพลาด')
        }
    }

    Component.onCompleted: {
        //console.log('userModel fetch');
        //userModel.fetch()
        dtbFromDate.setToday()
        dtbToDate.setToday()
    }

    content:[
        Form{
            inline: true
            className: 'small'
            Fields{

                Field {

                    className: 'one wide'
                    label: "ชื่อนัดหมาย"
                }
                Field {
                    className: 'three wide'
                    TextBox { id: txtAppName; }
                }
                Field {
                    className: 'four wide'
                }

                Field{className: 'one wide'}

                Field{
                    className: 'three wide'
                    CheckBox{
                        id: chkDate
                        text: 'ช่วงวันที่นัดหมาย'
                        checked: true
                    }
                }
                Field {
                    className: 'two wide'
                    DateTextBox {
                        id: dtbFromDate
                        doc_label: 'วันที่เริ่มนัดหมาย'
                        placeholder: 'วันที่เริ่มนัดหมาย'
                        thai: false
                    }
                }
                Field {
                    className: 'two wide'
                    DateTextBox {
                        id: dtbToDate
                        doc_label: 'วันที่สิ้นสุดนัดหมาย'
                        placeholder: 'วันที่สิ้นสุดนัดหมาย'
                        thai: false
                    }
                }
            }

            Fields{
                Field{
                    className: 'one wide'
                    label: 'ลูกค้า'
                }
                Field{

                    className: 'three wide'
                    TextBox{
                        id: txtCustomerFirstName
                        placeholder: 'ชื่อ '
                    }
                }
                Field {

                    className: 'four wide'
                    style: 'padding:0'
                    TextBox{
                        id: txtCustomerLastName
                        placeholder: 'นามสกุล '
                    }
                }

                Field{className: 'one wide'}

                Field{
                    className: 'three wide'
                    CheckBox{
                        id: chkSaveDate
                        text: 'ช่วงเวลา'
                        checked: true
                    }
                }
                Field {
                    className: 'two wide'
                    TimeTextBox {
                        id: ttbTime1
                        doc_label: 'เวลา'
                    }
                }
                Field {
                    className: 'two wide'
                    TimeTextBox {
                        id: ttbTime2
                        doc_label: 'เวลา'
                    }
                }
            }

            Fields{
                Field{
                    className: 'one wide'
                }
                Field{

                    className: 'three wide'
                    TextBox{
                        id: txtCustomerTel
                        placeholder: 'เบอร์โทร '
                    }
                }
                Field {

                    className: 'four wide'
                    style: 'padding:0'
                    TextBox{
                        id: txtCustomerEmail
                        placeholder: 'email '
                    }
                }

                Field{className: 'one wide'}

                Field{
                    className: 'three wide'
                }
                Field {
                    className: 'two wide'
                }
                Field{
                    className: 'two wide'
                    Button {
                        className: 'fluid green'
                        id: btnSearch
                        size: 'small'
                        text: 'ค้นหาช่าง'
                        doc_label: 'ค้นหาช่าง'
                        onClicked: {
                            root.loading = true
                            searchAndFilter()
                        }
                    }
                }
            }

            Fields{
                Field{
                    className: 'one wide'
                    label: 'สถานที่ติดตั้ง'
                }
                Field{

                    className: 'seven wide'
                    TextBox{
                        id: txtCustomerPremise
                        placeholder: 'ชื่อ (หมู่บ้าน, อาคาร) '
                    }
                }

                Field{className: 'eight wide'}
            }
            Fields{
                Field{
                    className: 'one wide'
                }
                Field{

                    className: 'seven wide'
                    TextBox{
                        id: txtCustomerAddress1
                        placeholder: 'Adress Line1 '
                    }
                }

                Field{className: 'eight wide'}
            }
            Fields{
                Field{
                    className: 'one wide'
                }
                Field{

                    className: 'seven wide'
                    TextBox{
                        id: txtCustomerAddress2
                        placeholder: 'Adress Line2 '
                    }
                }

                Field{className: 'eight wide'}
            }
            Fields{
                Field{
                    className: 'one wide'
                }
                Field{

                    className: 'three wide'
                    TextBox{
                        id: txtCustomerDistrict
                        placeholder: 'แขวง/ตำบล '
                    }
                }
                Field{

                    className: 'four wide'
                    TextBox{
                        id: txtCustomerCity
                        placeholder: 'เขต/อำเภอ '
                    }
                }

                Field{className: 'eight wide'}
            }
            Fields{
                Field{
                    className: 'one wide'
                }
                Field{

                    className: 'three wide'
                    TextBox{
                        id: txtCustomerProvince
                        placeholder: 'จังหวัด '
                    }
                }
                Field{

                    className: 'four wide'
                    TextBox{
                        id: txtCustomerZipcode
                        placeholder: 'รหัสไปรษณีย์ '
                    }
                }

                Field{className: 'eight wide'}

            }

            Fields{
                Field{
                    className: 'one wide'
                }
                Field{
                    className: 'six wide'
                    Common.CardLayout {
                        title: 'แผนที่'
                        hideCloseButton: true
                        headerColor: 'blue'
                        toggleCard: true
                        expanded: false
                        content:[
                            Uploader {
                                id: uploaderImg
                                accept: "image/*"
                                onStartUpload: {
                                    createAppModel.map_image = filebase64
                                    Util.alert('upload success', 'green', 'ok', 2000, function() {console.log('toast')})

                                    console.log(filebase64);
//                                    console.log(previewImg)
        //                            console.log(uploaderImg.previewImg)
        //                            console.log(previewImg.style)

                                }
                            },
                        ]
                    }

                }
                Field{className: 'eight wide'}

            }

        },
        Br{},
        //start dgrid
        Field{
            label: "เลือกช่าง"

            DGrid {
                id: grdAvailableSlot;
                height: 150;

                function renderCell(object, value, node, options){
                    node.innerHTML += value['id'];
                }

                function renderCell1(object, value, node, options){
                    node.innerHTML += value['content_object']['user']['full_name'];
                    node.setAttribute('style',
                        'background-color: '+object.background_color+';');
                }

                function renderCell2(object, value, node, options){
                    node.innerHTML += value['content_object']['user']['email'];
                    node.setAttribute('style',
                        'background-color: '+object.background_color+'; color: blue;');
                    //node.innerHTML += '<a href=mailto:'+value['email']+'>'+value['email']+'</a>';
                }

                function renderNo(value) {
                    return '<div style="text-align:right">' + (parseInt(value) + 1) + '</div>'
                }

                onSelected:{
                    console.log(grdAvailableSlot.selectedRow.provider)
                }

                columns: [
                    DColumn{label: 'no'; field:'storekey'; width:10; formatter: grdAvailableSlot.renderNo},
                    DColumn {field:'provider'; label:'ชื่อช่าง'; width:200;
                        renderCell: grdAvailableSlot.renderCell1
                    },
                    DColumn {field:'provider'; label:'email'; width:100;
                        renderCell: grdAvailableSlot.renderCell2
                    },
//                    DColumn {field:'start_time';      label:'start';    width:100},
//                    DColumn {field:'end_time';      label:'end';        width:100},
                    DColumn {field:'match_start';      label:'time';        width:100},
//                    DCustomColumn {
//                        field:'action';label:'Action';width:35
//                        Dom {
//                            Button {
//                                id: btn
//                                style: 'display: block; margin-left: auto; margin-right: auto;'
//                                icon: 'list layout'
//                                onClicked: {
//                                    console.log(grdAvailableSlot.selectedRow.name)
//                                    if(tltAction.target != btn) {
//                                        tltAction.target = btn
//                                        tltAction.show()
//                                    }
//                                }
//                            }
//                        }
//                    },
                ]
            }
        },

        Form{
            inline: true
            className: 'small'
            Br{}

            Field {
                label: "Remark เพิ่มเติม"
                TextArea { id: txtRemark; rows: 2 }
            }
            Br{}

            Field{
                Button{
                    backgroundColor: 'green'
                    text: 'นัดหมาย'
                    onClicked : {

                        if(grdAvailableSlot.selectedRow.provider){
                            Util.confirm({
                                titleColor: 'blue',
                                titleName: 'กรุณายืนยัน',
                                textContent: 'ต้องการสร้างนัดหมายกับช่าง '+ grdAvailableSlot.selectedRow.provider.content_object.user.full_name +' ใช่หรือไม่',
                                onApprove: function(){
                                    root.loading = true

                                    createAppModel.provider_id = grdAvailableSlot.selectedRow.provider.id
                                    createAppModel.availableslot_id = grdAvailableSlot.selectedRow.id
                                    createAppModel.user_technician = grdAvailableSlot.selectedRow.provider.content_object.user.id
                                    createAppModel.name = txtAppName.text
                                    createAppModel.remark = txtRemark.text
                                    createAppModel.timeslot = grdAvailableSlot.selectedRow.match_start
                                    createAppModel.first_name = txtCustomerFirstName.text
                                    createAppModel.last_name = txtCustomerLastName.text
                                    createAppModel.email = txtCustomerEmail.text
                                    createAppModel.tel = txtCustomerTel.text
                                    createAppModel.premise_name = txtCustomerPremise.text
                                    createAppModel.address1 = txtCustomerAddress1.text
                                    createAppModel.address2 = txtCustomerAddress2.text
                                    createAppModel.province = txtCustomerProvince.text
                                    createAppModel.city = txtCustomerCity.text
                                    createAppModel.district = txtCustomerDistrict.text
                                    createAppModel.zipcode = txtCustomerZipcode.text
//                                    createAppModel.map_image = uploader.selectedFile

//                                  createAppModel.city = cboCity.value

                                    createAppModel.create()

                                }
                            })
                        }
                        else{
                            alert("โปรดเลือกช่างก่อน")
                        }
                    }
                }
            }

        },

    ]



    TooltipDialog {
        id: tltAction
        activeEvent: 'click'
        onHidden: {

        }
        Button{
            backgroundColor: 'green'
            text: 'ดูตารางว่างทั้งหมด'
            onClicked : {
                alert(grdAvailableSlot.selectedRow.id)
            }
        }
        /*Button{
            backgroundColor: 'yellow'
            text: 'รายละเอียด'
            onClicked : {
                alert(grdAvailableSlot.selectedRow.id)
            }
        }*/
    }

    Modal {
        id: addDialog
        className: "tiny"
        Form {
            tagName: "form"
            htmlAttr: { return {
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
                   'type': 'submit'
                }}
                onClicked: {

                      upload_path = contentFile.dom.value
                      upload_fileName = upload_path.substr(upload_path.lastIndexOf("\\")+1, upload_path.length);

                      content_name.dom.value = upload_fileName.split('.')[0]
                      content_ext.dom.value = '.' + upload_fileName.split('.')[1]

                      //alert(upload_fileName)
                      rmdMessageList.message_list=[]
                      rmdMessageList.create()

                      upload.hide()
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
    } //end modal

}
