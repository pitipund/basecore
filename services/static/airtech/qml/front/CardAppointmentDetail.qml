import Semantic.Html 1.0
import DGrid 1.0
import QmlWeb 1.0
import '../Common' as Common
import '../Common/Util.js' as Util

Common.CardLayout {
    id: _detailTitleModal
    title: 'รายละเอียด'
    hideCloseButton: false
    headerColor: 'blue'
    toggleCard: false

    property alias detailTitleModal: _detailTitleModal.title
    property alias detailTxtCustomerFirstName: detailTxtCustomerFirstName.text
    property alias detailTxtCustomerLastName: detailTxtCustomerLastName.text
    property alias detailTxtTechnicianName: detailTxtTechnicianName.text
    property alias detailTxtAppointmentTime: detailTxtAppointmentTime.text
    property alias txtCustomerTel: txtCustomerTel.text
    property alias txtCustomerEmail: txtCustomerEmail.text
    property alias txtCustomerPremise: txtCustomerPremise.text
    property alias txtCustomerAddress1: txtCustomerAddress1.text
    property alias txtCustomerAddress2: txtCustomerAddress2.text
    property alias txtCustomerDistrict: txtCustomerDistrict.text
    property alias txtCustomerCity: txtCustomerCity.text
    property alias txtCustomerProvince: txtCustomerProvince.text
    property alias txtCustomerZipcode: txtCustomerZipcode.text

    content:[
        Form{
            inline: true
            className: 'small'
            Fields{
                Field{
                    className: 'one wide'
                    label: 'ลูกค้า'
                }
                Field{

                    className: 'three wide'
                    TextBox{
                        id: 'detailTxtCustomerFirstName'
                        placeholder: 'ชื่อ '
                    }
                }
                Field {

                    className: 'four wide'
                    style: 'padding:0'
                    TextBox{
                        id: 'detailTxtCustomerLastName'
                        placeholder: 'นามสกุล '
                    }
                }

                Field{className: 'one wide'}

                Field{
                    className: 'two wide'
                    label: 'ช่าง'
                }
                Field {
                    className: 'five wide'
                    TextBox{
                        id: detailTxtTechnicianName
                        placeholder: 'ชื่อช่าง'
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
                        placeholder: 'เบอร์โทร'
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
                    className: 'two wide'
                    label: 'เวลานัดหมาย'
                }
                Field {
                    className: 'four wide'
                    TextBox{
                        id: detailTxtAppointmentTime
                        placeholder: 'เวลานัดหมาย '
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


                }
                Field{className: 'eight wide'}

            }
            TextArea {
                id: detailAddressModal; rows: 4
            }
        }
    ]
}
//style: "background: white !important"
//onHidden:{
//    uploader.clear()
//}
