Feature: เปิด Encounter กับนพ.ไกรฤกษ์ ภูสี, พยาบาลส่งคิวเข้าตรวจ, หมอสร้าง admit order แบบไม่นัด

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
       Then I see alert บันทึกเรียบร้อย
        And I click CloseOpenVN
        And I see ถ่ายรูป
        And I click ตกลง
       When I fill in วันเดือนปีเกิด with 01/01/2530
        And I click บันทึกข้อมูลผู้ป่วย
      Given I visit PTM/MainPatientList.qml
       When I fill from userdata "HN" in "HN" and enter
        And with grid คิวผู้ป่วย
        And row with รอคัดกรอง I double click
       Then I see Chief Complaint
       When I fill fake "sentence" in "Chief Complaint"
        And I click Save
       Then I see ต้องการยืนยันเอกสารใช่หรือไม่
        And I click Confirm
        And I see บันทึกสำเร็จ
        And I click ตกลง
       When with grid ตาราง Vital Signs
        And I wait 1 sec
        And row with น้ำหนัก I fill in result with 60
        And I click บันทึก Vital Sign
       Then I see บันทึกรายการสำเร็จ
        And I click ตกลง
        And I refresh
        And I wait 3 sec
       When I click ส่งเข้าคิวรอตรวจ
       Then I see เข้าคิวรอตรวจ
        And I click ใช่
      Given I visit DPO/MainDPO.qml
       When I fill from userdata "HN" in "กรอง HN หรือ ชื่อ-สกุล" and enter
        And with grid คิวผู้ป่วยหน้าห้องแพทย์
        And row with รอพบแพทย์ I double click
        And I wait 1 sec
        And I fill fake "sentence" in "Present illness"
        And I slowly type in Medical Term with test[enter]
        And I click Check out
        And I wait 1 sec
        And I check Admit
        And I click Check out
        And with card จองเตียง (ADMIT ORDER)
        And I slowly type in Medical Term with test[enter]
        And I fill in เวลา with 21:00
        And I select Premium from ประเภทหอผู้ป่วย
        And I fill in จำนวนวันที่อยู่ with 2
        And I fill in เหตุผลในการ Admit with ง่วงนอน
        And I select นพ.ไกรฤกษ์ ภูสี (001) from แพทย์เจ้าของไข้
        And I check ไม่ต้องงด
        And I click บันทึกรายการจอง
        And I wait 1 sec
        And I see บันทึกรายการสำเร็จ
      Given I visit PTM/MainPatientList.qml
       When I fill from userdata "HN" in "HN" and enter
        And I wait 1 sec
        And with grid คิวผู้ป่วย
        And row with ออกจากห้องตรวจ I double click
        And I wait 5 sec
        And I click Discharge
        And I wait 1 sec
        And I select Improved from สภาพผู้ป่วยก่อนจำหน่าย
        And I select Admit from Discharge Status
        And I click บันทึก
       Then I see Discharge Complete
        And print "first_name" in userdata
        And print "last_name" in userdata
