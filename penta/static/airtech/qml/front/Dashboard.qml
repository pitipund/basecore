import Semantic.Html 1.0
import DGrid 1.0
import QmlWeb 1.0
import '../Common' as Common
import '../Common/Util.js' as Util



Common.CardLayout {
    id: _root
    title: 'ค้นหานัดหมาย'
    headerColor: 'teal'

    function searchAppAndFilter() {
        query = {}
        if(chkAppNo.checked) {
            query.appointment_id = appNoTextBox.text
        }

        if(chkDate.checked){
            var start = ""
            var end = ""

            var tmp_startdate = dtbFromDate.toDashFormat()
            var tmp_starttime = ""
            var tmp_enddate = dtbToDate.toDashFormat().replace()
            var tmp_endtime = ""

            if(tmp_startdate > tmp_enddate){
                alert("วันที่เริ่มค้นหา มากกว่าวันที่สิ้นสุด");
            }else{
                start = tmp_startdate + "T" + "00:00:00" + "Z"
                end   = tmp_enddate   + "T" + "23:59:59" + "Z"
                query.start = start
                query.end = end
            }
        }

        grdApp.model = []
        console.log(appointmentModel.url)

        appointmentModel.query = query
        _root.loading = true
        appointmentModel.fetch()

    }

    Component.onCompleted: {

        dtbFromDate.setToday()
        dtbToDate.setToday()
    }

    RestModel{
        id: appointmentModel
        url: '/appointment/search_airtech_appointment/'
        property alias result: grdApp.model
        onFetched: {
            _root.loading = false
            console.log(result)
        }
        onFailed: {
            _root.loading = false
            alert('เกิดข้อผิดพลาด')
        }
    }

    RestModel {
        id: cancelAppModel
        queryMimeType: 'application/json'

        property var app_id

        url: "/appointment/cancel_appointment/"

        onSaved: {
            _root.loading = false
            searchAppAndFilter()
            Util.alert('ยกเลิกสำเร็จ', 'green')
        }
        onFailed:{
            _root.loading = false
            if(error[0]){
                alert(error[0])
            }
        }
    }

    Modal {
        id:detailModal
        style: "background: white !important"
        CardAppointmentDetail {
            id: cardAppointmentDetail
            detailTitleModal: ""
            detailTxtCustomerFirstName: grdApp.selectedRow.service_detail.client.first_name
            detailTxtCustomerLastName: grdApp.selectedRow.service_detail.client.last_name
            detailTxtTechnicianName: grdApp.selectedRow.service_detail.provider.content_object.user.email
            detailTxtAppointmentTime: grdApp.selectedRow.finalize_time
            txtCustomerTel: grdApp.selectedRow.service_detail.client.tel
            txtCustomerEmail: grdApp.selectedRow.service_detail.client.email
            txtCustomerPremise: grdApp.selectedRow.address.name
            txtCustomerAddress1: grdApp.selectedRow.address.address1
            txtCustomerAddress2: grdApp.selectedRow.address.address2
            txtCustomerDistrict: grdApp.selectedRow.address.district
            txtCustomerCity: grdApp.selectedRow.address.city
            txtCustomerProvince: grdApp.selectedRow.address.province
            txtCustomerZipcode: grdApp.selectedRow.address.zipcode
        }
//        onHidden:{
//            uploader.clear()
//        }
    }

    content:[
        Form{
            inline: true
            className: 'small'
            Fields{
                Field{
                    className: 'two wide'
                    CheckBox{
                        id: chkAppNo
                        text: 'เลขนัดหมาย'
                        checked: false
                    }
                }
                Field {
                    className: 'two wide'
                    TextBox {
                        id: appNoTextBox
                    }
                }
                Field {
                    className: 'four wide'
                    style: 'padding:0'
                    LabelTag {
                        id: lbtApp
                        className: 'large fluid'
                        text: '-'
                    }
                }

                Field{className: 'one wide'}

                Field{
                    className: 'two wide'
                    CheckBox{
                        id: chkStatus
                        text: 'ตามสถานะ'
                        checked: false
                    }
                }
                Field {
                    className: 'four wide disabled'
                    ComboBox{
                        id: cboStatus
                        search: true
                        fullTextSearch: true
                    }
                }
            }

            Fields{
                Field{
                    className: 'two wide'
                    CheckBox{
                        id: chkDate
                        text: 'ตามวันที่'
                        checked: true
                    }
                }
                Field {
                    className: 'three wide'
                    DateTextBox {
                        id: dtbFromDate
                        thai: false
                    }
                }
                Field {
                    className: 'three wide'
                    DateTextBox {
                        id: dtbToDate
                        thai: false
                    }
                }
            }

            Fields{
                Field{
                    className: 'two wide'
                    CheckBox{
                        id: chkCustomer
                        text: 'รหัสลูกค้า'
                        checked: false
                    }
                }
                Field{
                    className: 'two wide disabled'
                    ActionTextBox {
                        id: atbCustomer
                    }
                }
                Field {
                    className: 'four wide'
                    style: 'padding:0'
                    LabelTag {
                        id: lbtCustomer
                        className: 'large fluid'
                        text: '-'
                    }
                }
            }

            Fields{
                Field{
                    className: 'two wide'
                    CheckBox{
                        id: chkTechnical
                        text: 'รหัสช่าง'
                        checked: false
                    }
                }
                Field{
                    className: 'two wide disabled'
                    ActionTextBox {
                        id: atbTechnical
                    }
                }
                Field {
                    className: 'four wide'
                    style: 'padding:0'
                    LabelTag {
                        id: lbtTechnical
                        className: 'large fluid'
                        text: '-'
                    }
                }
                Field {className:' one wide'}
                Field{
                    className: 'one wide'
                    Button {
                        className: 'fluid blue'
                        id: btnSearch
                        size: 'small'
                        text: 'ค้นหา'
                        doc_label: 'ค้นหา'
                        onClicked: {
                            searchAppAndFilter()
                        }
                    }
                }
                Field{
                    className: 'two wide'
                    Button{
                        className: 'fluid green'
                        id: btnAdd
                        size: 'small'
                        icon: 'plus'
                        text: 'สร้างนัดหมายใหม่'
                        onClicked: {
                            window.open("/media/airtech/create.html");
                        }
                    }
                }
            }
        },
        Br {},

        DGrid {
            id: grdApp
            height: 400
            function renderRow(row, args, dojoUtil){
                if(args[0]['is_active'] == false){
                    dojoUtil.domStyle.set(row, 'backgroundColor', '#ff9999')
                }
                return row
            }

            function generateIcon(className) {
                return $('<i class="' + className + '" style=" ' +
                       'display:block; margin-left:auto; margin-right:auto; margin-bottom:3px;' +
                       '"></i>')[0]
            }

            function zeroPad(nr,base){
                var  len = (String(base).length - String(nr).length)+1;
                return len > 0? new Array(len).join('0')+nr : nr;
            }

            function renderId(object, value, node, options){
                val_id = zeroPad(value, 1000)
                node.innerHTML += val_id;
            }
            function renderCellCustomer(object, value, node, options){

                node.innerHTML += value['client']['first_name'];
                node.setAttribute('style',
                    'background-color: '+object.background_color+';');
            }
            function renderCellTechnician(object, value, node, options){
                console.log(value);
                if(value['provider']['content_object']['user'] != undefined){
                    node.innerHTML += value['provider']['content_object']['user']['full_name'];
                    node.setAttribute('style',
                    'background-color: '+object.background_color+';');
                }

            }
            function renderIs_done(object, value, node, options){
                if (value['is_done']) {
                    node.append(generateIcon('green checkmark big link icon'))
                }
            }
            function renderProviderStatus(object, value, node, options){
                if (value == "Request") {
                    node.append(generateIcon('yellow question big link icon'))
                }else if (value == "Confirmed") {
                    node.append(generateIcon('green checkmark big link icon'))
                }else if (value == "Rejected") {
                    node.append(generateIcon('red close big link icon'))
                }
            }

            function renderIcon(object, value, node, options) {
                // interaction: warning circle
                if (value) {
                    node.append(generateIcon('green checkmark big link icon'))
                }else{
                    node.append(generateIcon('red close big link icon'))
                }
            }

            columns: [

                DColumn {field: 'id'        ;label: 'id'         ;width: 20;
                        renderCell: grdApp.renderId
                    },
                DColumn {field: 'name'       ;label: 'นัดหมาย'    ;width: 40},

                DColumn {field:'service_detail'; label:'ลูกค้า'; width:180;
                        renderCell: grdApp.renderCellCustomer
                    },
                DColumn {field:'service_detail'; label:'ชื่อช่าง'; width:180;
                        renderCell: grdApp.renderCellTechnician
                    },

                DColumn {field: 'finalize_time'      ;label: 'วัน - เวลา' ;width: 80},
                DColumn {field: 'provider_status'    ;label: 'ช่างตอบรับ'      ;width: 40;
                        renderCell: grdApp.renderProviderStatus
                    },
                DColumn {field: 'service_detail'    ;label: 'จบงาน?'      ;width: 30;
                        renderCell: grdApp.renderIs_done
                    },
                DColumn {field: 'is_active'        ;label: 'Active?'         ;width: 30;
                        renderCell: grdApp.renderIcon
                    },
//                DColumn {field: 'remark'    ;label: 'หมายเหตุ'   ;width: 80},
                DColumn {field: 'service_type_name'       ;label: 'service_type'    ;width: 80},
                DCustomColumn {
                    field:'action';label:'Action';width:35
                    Dom {
                        Button {
                            id: btn
                            style: 'display: block; margin-left: auto; margin-right: auto;'
                            icon: 'list layout'
                            onClicked: {
                                console.log(grdApp.selectedRow.name)
                                if(appAction.target != btn) {
                                    appAction.target = btn
                                    appAction.show()
                                }
                            }
                        }
                    }
                },
            ]

            TooltipDialog {
                id: appAction
                activeEvent: 'click'

                LabelTag {
                    className: 'fluid'
                    id: titleAppAction
                    text: '-'
                }
                onHidden: {

                }

                Button{
                    backgroundColor: 'green'
                    text: 'รายละเอียด'
                    onClicked : {
//                        alert(grdApp.selectedRow.id)
                        cardAppointmentDetail.detailTitleModal = "รายละเอียด (ID: "+grdApp.selectedRow.id+")";

                        console.log(grdApp.selectedRow);
                        detailModal.show()
                    }
                }

//                Button{
//                    backgroundColor: 'yellow'
//                    text: 'แก้ไข'
//                    onClicked : {
//                        alert(grdApp.selectedRow.id)
//                    }
//                }


                Button{
                    backgroundColor: 'red'
                    text: 'ยกเลิกนัดหมาย'
                    onClicked : {
                        Util.confirm({
                            titleColor: 'blue',
                            titleName: 'กรุณายืนยัน',
                            textContent: 'ต้องการยกเลิกนัดหมาย '+ grdApp.selectedRow.id +' ใช่หรือไม่',
                            onApprove: function(){

                                cancelAppModel.app_id = grdApp.selectedRow.id
                                cancelAppModel.create()

                            }
                        })

                    }
                }
            }
        }
    ]

}
