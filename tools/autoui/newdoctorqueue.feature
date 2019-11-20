Feature: เปิด Encounter กับนพ.ไกรฤกษ์ ภูสี, พยาบาลส่งคิวเข้าตรวจ

    Scenario:
      Given I log in without clearing session with device MED as doctor
        And I visit REG/MainREG.qml
        And I click เปิดประวัติฉุกเฉิน
        And I check ชาย
        And I check ไทย
        And I fill fake "first_name" in "ชื่อผู้ป่วยฉุกเฉิน" and enter
        And I fill fake "last_name" in "นามสกุลผู้ป่วยฉุกเฉิน" and enter
       When I click Save
       Then I see บันทึกเรียบร้อย
        And keep last hn in context
        And I wait 1.5 sec
       When I select อายุรกรรม (MED) from แผนก
        And I select นพ.ไกรฤกษ์ ภูสี (001) from แพทย์
        And I click ไม่เคยมีประวัติแพ้
        And I click บันทึก Encounter ใหม่
       Then I see บันทึกเรียบร้อย
      Given I visit PTM/MainPatientList.qml
       When I fill from userdata "HN" in "HN" and enter
        And with grid คิวผู้ป่วย
        And row with รอคัดกรอง I double click
       Then I see Chief Complaint
       When I fill fake "sentence" in "Chief Complaint"
        And I click Save
       Then I see ต้องการยืนยันเอกสารใช่หรือไม่
        And I click Confirm
       Then I see บันทึกสำเร็จ
        And I click ตกลง
        And I refresh
        And I wait 3 sec
       When I click ส่งเข้าคิวรอตรวจ
       Then I see เข้าคิวรอตรวจ
        And I click ใช่
        And print "first_name" in userdata
        And print "last_name" in userdata
