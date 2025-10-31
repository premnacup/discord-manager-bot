-----

# Discord Manager & Utility Bot

บอท Discord อเนกประสงค์ที่สร้างด้วย [`discord.py`](https://www.google.com/search?q=%5Bhttps://discordpy.readthedocs.io/%5D\(https://discordpy.readthedocs.io/\)) มาพร้อมกับฟีเจอร์จัดการเซิร์ฟเวอร์, เครื่องมืออำนวยความสะดวก และระบบตารางเรียนส่วนตัว บอทใช้ `cogs` ในการจัดการคำสั่งอย่างเป็นระบบ, `dotenv` สำหรับการจัดการ Token อย่างปลอดภัย และ `pymongo` สำหรับการจัดเก็บข้อมูลตารางเรียน

-----

## ✨ ฟีเจอร์หลัก

  * **General**: ตรวจสอบค่า Latency (`ping`), ทักทายผู้ใช้งาน (`hello`), และแสดงข้อมูลเซิร์ฟเวอร์ (`info`)
  * **Role Management**: (ต้องมีสิทธิ์) สร้าง, ลบ และมอบหมาย role ให้กับสมาชิกที่ถูกกล่าวถึง
  * **Academic Schedule**: (ต้องใช้ MongoDB) เพิ่ม, ลบ และดูตารางเรียนส่วนตัวของผู้ใช้ผ่านคำสั่งง่ายๆ
  * **Fun**: ส่ง custom emoji แบบสุ่ม
  * **Help Command**: แสดงเมนูช่วยเหลือแบบ embed ที่สวยงามและเข้าใจง่าย
  * **Modular Loading**: โหลดคำสั่งทั้งหมดจากโฟลเดอร์ `cogs` โดยอัตโนมัติ

-----

## 🧱 คำสั่งทั้งหมด

> Prefix เริ่มต้น: **`b`** หรือ **`t`** (หรือ mention บอท)

### ทั่วไป (General)

| Command | Usage | Description |
| --- | --- | --- |
| `bping` | `bping` | ตอบกลับด้วย Latency ของบอท (ms) |
| `bhello` | `bhello` | ทักทายผู้ที่ใช้คำสั่ง |
| `binfo` | `binfo` | แสดงข้อมูลของบอทและเซิร์ฟเวอร์ในรูปแบบ embed |
| `brick [n]` | `brick [n]` | ส่ง custom emoji แบบสุ่ม 1-10 ชิ้น (ชื่อเดิม `rick`) |
| `bhelp` | `bhelp` | แสดงหน้าต่างช่วยเหลือพร้อมคำสั่งทั้งหมด |

### จัดการ Role (Role Management)

**หมายเหตุ:** ผู้ใช้ต้องมี Role ชื่อ **"Moderator"** และบอทต้องมีสิทธิ์ `Manage Roles`

| Command | Usage | Description |
| --- | --- | --- |
| `bcrole` | `bcrole <role_name> [#HEX]` | สร้าง Role ใหม่ พร้อมกำหนดสี (สุ่มสีหากไม่ระบุ) |
| `brrole` | `brrole <role_name>` | ลบ Role ตามชื่อ |
| `barole` | `barole <role_name> @user1 @user2 ...` | เพิ่ม Role ที่มีอยู่แล้วให้กับสมาชิกที่ mention |

### ตารางเรียน (Academic Schedule)

**หมายเหตุ:** ฟีเจอร์นี้ต้องการการตั้งค่า `MONGO_URI` ในไฟล์ `.env`

| Command | Usage | Description |
| --- | --- | --- |
| `baddclass` | `baddclass` | เปิดเมนูแบบ dropdown และ modal เพื่อเพิ่มวิชาเรียนในตาราง |
| `bmyschedule`| `bmyschedule` | แสดงตารางเรียนทั้งหมดของผู้ใช้ จัดเรียงตามวันและเวลา |
| `bdelclass` | `bdelclass <subject_name>` | ลบวิชาเรียนออกจากตารางตามชื่อวิชา (รองรับชื่อที่มีเว้นวรรค) |

-----

## 🧰 สิ่งที่ต้องมี (Requirements)

  * Python **3.10+**
  * `discord.py`
  * `python-dotenv`
  * `pymongo[srv]`

คุณสามารถติดตั้งทั้งหมดได้ผ่าน `requirements.txt`:

```bash
pip install -r requirements.txt
```

-----

## 🔧 การติดตั้งและใช้งาน

1.  **สร้างบอท Discord**: ไปที่ [Discord Developer Portal](https://discord.com/developers/applications) สร้างแอปพลิเคชัน, เพิ่ม Bot user และคัดลอก **Token**

2.  **เปิดใช้งาน Intents**: ในหน้า Bot ของแอป, เปิดใช้งาน **Privileged Gateway Intents** ทั้ง 3 อย่าง:

      * `SERVER MEMBERS INTENT`
      * `MESSAGE CONTENT INTENT`

3.  **เชิญบอทเข้าเซิร์ฟเวอร์**: สร้าง URL เชิญบอทด้วยสิทธิ์ `bot` และ `applications.commands` พร้อมกับ Permissions ที่จำเป็น:

      * `Manage Roles`
      * `Send Messages`
      * `Embed Links`

4.  **ตั้งค่าโปรเจกต์**:

      * สร้างไฟล์ `.env` ในโฟลเดอร์หลัก
      * เพิ่ม `DISCORD_TOKEN` และ `MONGO_URI` (หากต้องการใช้ระบบตารางเรียน) ลงในไฟล์ `.env`

    **ไฟล์ `.env`:**

    ```
    DISCORD_TOKEN=YOUR_BOT_TOKEN_HERE
    MONGO_URI=YOUR_MONGODB_CONNECTION_STRING_HERE
    ```

5.  **รันบอท**:

    ```bash
    python main.py
    ```

    บอทจะทำการเชื่อมต่อกับ Discord และโหลด Cogs ทั้งหมดโดยอัตโนมัติ และ Log จะถูกบันทึกลงใน `discord.log`

-----

## 🔐 สิทธิ์ที่ต้องการ (Permissions)

  * **Discord Developer Portal**: ต้องเปิดใช้งาน **Message Content** และ **Server Members** Intents
  * **ในเซิร์ฟเวอร์ Discord**:
      * Role ของบอทต้องมีสิทธิ์ **Manage Roles** เพื่อให้คำสั่งสร้าง/ลบ/เพิ่ม Role ทำงานได้
      * **ลำดับ Role (Hierarchy)**: Role ของบอทต้องอยู่สูงกว่า Role ที่ต้องการจะจัดการ

-----

## 📁 โครงสร้างโปรเจกต์

```
.
├── cogs/
│   ├── academic/
│   │   └── schedule.py
│   ├── roles/
│   │   └── role_management.py
│   └── utility/
│       └── info.py
├── main.py             # ไฟล์หลักสำหรับรันบอท
├── .env                # ไฟล์เก็บค่า Token และ MONGO_URI
├── requirements.txt    # รายการ library ที่ต้องติดตั้ง
├── .gitignore          # ไฟล์ที่ถูกละเว้นโดย Git
└── README.md
```
