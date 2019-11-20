Feature: เปิด Encounter กับนพ.ไกรฤกษ์ ภูสี

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
        And I wait 1 sec
       When I select อายุรกรรม (MED) from แผนก
        And I select นพ.ไกรฤกษ์ ภูสี (001) from แพทย์
        And I click ไม่เคยมีประวัติแพ้
        And I click บันทึก Encounter ใหม่
       Then I see บันทึกเรียบร้อย
        And print "first_name" in userdata
        And print "last_name" in userdata
