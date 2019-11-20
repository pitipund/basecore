Segment{
    id: root
    property alias roomId: cboRoom.value

    signal saved()

    RestModel {
        id: rmdRoomAdmission
        url: '/apis/APP/admit-appointment-order/'

        onFailed: {
            root.loading = false
            frmRoomAdmission.showError(error)
        }
        onSaved: {
            root.loading = false
            Util.alert('บันทึกข้อมูลสำเร็จ', 'green')
            root.saved()
        }
    }

    function setHN(hn) {
        txtHN.text = hn
    }

    Button {
        text: 'บันทึกรายการ'
        onClicked: {
            Util.confirm({
                titleColor: 'blue',
                titleName: 'กรุณายืนยัน',
                textContent: 'ต้องการบันทึก ใช่หรือไม่',
                onApprove: function(){
                    root.loading = true
                    rmdRoomAdmission.save()
                }
            })
        }
    }
}