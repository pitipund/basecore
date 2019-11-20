Feature: จัดการ Role
  :usecase: USR_2

  Scenario: Administrator can create new role
    Given I logged in as admin
      And I visit manage/users/
      And click button Role
     When click button เพิ่ม role
      and fill form name with พยาบาล
      and fill form start_date with 01/05/2017
      and fill form end_date with 31/05/2017
      and click button บันทึก
     Then I see role "พยาบาล" was added successfully

  Scenario: Administrator can edit existing role
    Given I logged in as admin
      And I visit manage/users/
      And click button Role
     When click button เพิ่ม role
      and fill form name with ผู้ใช้ HIS
      and fill form start_date with 01/05/2017
      and fill form end_date with 31/05/2017
      and click button บันทึก
     Then I see role "ผู้ใช้ HIS" was added successfully
     When click button ผู้ใช้ HIS
      and fill form name with เปลี่ยนชื่อ
      and click button บันทึก
     Then I see "เปลี่ยนชื่อ" was changed successfully

  Scenario: Administrator can delete existing role
    Given I logged in as admin
      And I visit manage/users/
      And click button Role
     When click button เพิ่ม role
      and fill form name with ผู้ใช้ HIS
      and fill form start_date with 01/05/2017
      and fill form end_date with 31/05/2017
      and click button บันทึก
     Then I see role "ผู้ใช้ HIS" was added successfully
     When click button ผู้ใช้ HIS
      and click link ลบ
     Then I see คุณแน่ใจหรือที่จะลบ role "ผู้ใช้ HIS"
     When click button ใช่, ฉันแน่ใจ
     Then I see ลบ role "ผู้ใช้ HIS" เรียบร้อยแล้ว
