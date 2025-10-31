# cogs/academic/HomeworkManager.py

import os
import re
import discord
from discord import ui
from discord.ext import commands
import pymongo
from datetime import datetime
from math import ceil

MONGO_URI = os.getenv("MONGO_URI")

# --------------------------
# Utilities
# --------------------------
DATE_FORMATS = [
    "%Y-%m-%d",      # 2025-11-23
    "%d/%m/%Y",      # 23/11/2025
]
TIME_FORMATS = [
    "%H:%M",         # 09:30
    "%H:%M:%S",      # 09:30:00
]

def _maybe_be(year: int) -> int:
    """ถ้าเป็นปี พ.ศ. (>=2400) ให้แปลงเป็น ค.ศ. โดยลบ 543"""
    return year - 543 if year >= 2400 else year

def _strip_time_from_date_if_any(date_text: str) -> str:
    """
    ลบส่วนเวลาออกจากช่อง 'วัน' ถ้าเผลอวางมาทั้ง timestamp เช่น 2568-11-23T00:00:00
    - เอา 'T' ออกและตัดให้เหลือเฉพาะวันที่
    """
    s = (date_text or "").strip()
    if "T" in s:
        s = s.replace("T", " ")
    # ตัดเวลาออกถ้ามี
    s = re.split(r"\s+\d{1,2}:\d{2}(:\d{2})?$", s)[0]
    return s.strip()

def _fix_be_in_text_date(date_text: str) -> str:
    """แปลงปี พ.ศ. เป็น ค.ศ. ในรูปแบบ YYYY-MM-DD หรือ DD/MM/YYYY"""
    s = date_text.strip()
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})$", s)
    if m:
        y = _maybe_be(int(m.group(1)))
        return f"{y:04d}-{m.group(2)}-{m.group(3)}"
    m = re.match(r"^(\d{2})/(\d{2})/(\d{4})$", s)
    if m:
        y = _maybe_be(int(m.group(3)))
        return f"{m.group(1)}/{m.group(2)}/{y:04d}"
    return s

def _parse_date(date_text: str) -> datetime:
    last_err = None
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(date_text, fmt)
        except Exception as e:
            last_err = e
    raise ValueError(
        f"รูปแบบวันไม่ถูกต้อง: '{date_text}' (ตัวอย่างที่รับได้: 2025-11-23 หรือ 23/11/2025)"
    ) from last_err

def _parse_time(time_text: str) -> tuple[int, int, int]:
    last_err = None
    for fmt in TIME_FORMATS:
        try:
            t = datetime.strptime(time_text, fmt)
            return (t.hour, t.minute, t.second)
        except Exception as e:
            last_err = e
    raise ValueError(
        f"รูปแบบเวลาไม่ถูกต้อง: '{time_text}' (ตัวอย่างที่รับได้: 09:30 หรือ 09:30:00)"
    ) from last_err

def parse_due(date_text: str | None, time_text: str | None):
    """
    รับ 'วัน' และ 'เวลา' แยกกัน (ทั้งคู่บังคับ)
    คืน (due_display => 'YYYY-MM-DD HH:MM', due_ts)
    - รองรับปี พ.ศ. ในช่องวัน
    - ถ้าอย่างใดอย่างหนึ่งว่าง -> raise ValueError
    """
    if not date_text or not date_text.strip():
        raise ValueError("กรุณากรอก 'วันส่ง'")
    if not time_text or not time_text.strip():
        raise ValueError("กรุณากรอก 'เวลา'")

    # จัดการเคสผู้ใช้วาง timestamp มาทั้งชุดในช่องวัน
    date_clean = _strip_time_from_date_if_any(date_text)
    # แก้ปี พ.ศ. -> ค.ศ.
    date_clean = _fix_be_in_text_date(date_clean)

    # parse
    d = _parse_date(date_clean)
    h, m, s = _parse_time(time_text.strip())

    dt = d.replace(hour=h, minute=m, second=s, microsecond=0)
    due_display = dt.strftime("%Y-%m-%d %H:%M")   # ไม่มี 'T' ใช้เว้นวรรค
    due_ts = int(dt.timestamp())
    return (due_display, due_ts)

def human_left(ts: int | None) -> str:
    """สร้างข้อความ 'เหลือ X วัน' หรือ 'เลยกำหนด' จาก timestamp (วินาที)"""
    if not ts:
        return ""
    now = datetime.now().timestamp()
    diff_days = (ts - now) / 86400.0
    if diff_days < 0:
        return "⏰ เลยกำหนดแล้ว"
    days_left = ceil(diff_days)
    if days_left == 0:
        return "⏰ กำหนดวันนี้"
    return f"⏳ เหลือ {days_left} วัน"

# --------------------------
# Modal สำหรับเพิ่มการบ้าน (วัน/เวลา แยกช่อง และ 'เวลา' บังคับ)
# --------------------------
class HomeworkModal(ui.Modal, title="เพิ่มการบ้านใหม่"):
    subject_input = ui.TextInput(
        label="ชื่อวิชา",
        placeholder="เช่น GEN101 General Physics, INT101 Programming",
        required=True,
    )
    assignment_input = ui.TextInput(
        label="ชื่องาน หรือ รายละเอียดการบ้าน",
        placeholder="เช่น รายงานบทที่ 5, แบบฝึกหัดท้ายบท",
        style=discord.TextStyle.paragraph,
        required=True,
    )
    due_date_input = ui.TextInput(
        label="วันส่ง (บังคับ)",
        placeholder="รองรับ: 2025-11-23 หรือ 23/11/2025 (พ.ศ. เช่น 2568-11-23 ก็ได้)",
        required=True,
    )
    due_time_input = ui.TextInput(
        label="เวลา (บังคับ)",
        placeholder="เช่น 09:30 หรือ 23:59 หรือ 09:30:00",
        required=True,
    )

    def __init__(self, db_collection):
        super().__init__()
        self.db_collection = db_collection

    async def on_submit(self, interaction: discord.Interaction):
        subject = self.subject_input.value
        assignment = self.assignment_input.value
        due_date_raw = self.due_date_input.value
        due_time_raw = self.due_time_input.value

        try:
            due_display, due_ts = parse_due(due_date_raw, due_time_raw)
        except ValueError as e:
            await interaction.response.send_message(f"❌ {e}", ephemeral=True)
            return

        homework_data = {
            "user_id": interaction.user.id,
            "subject": subject.strip(),
            "assignment": assignment.strip(),
            "due_display": due_display,  # 'YYYY-MM-DD HH:MM' (ไม่มี T)
            "due_ts": due_ts,            # unix seconds
        }
        self.db_collection.insert_one(homework_data)

        await interaction.response.send_message(
            f"✅ บันทึกการบ้านวิชา **{subject}** แล้ว! 🗓️ {due_display}",
            ephemeral=True
        )

# --------------------------
# View/Button (กันคนอื่นกด)
# --------------------------
class AddHWView(discord.ui.View):
    def __init__(self, db_collection, allowed_user_id: int | None = None, timeout: float | None = 180):
        super().__init__(timeout=timeout)
        self.db_collection = db_collection
        self.allowed_user_id = allowed_user_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if self.allowed_user_id and interaction.user.id != self.allowed_user_id:
            await interaction.response.send_message(
                "🚫 ปุ่มนี้สำหรับผู้ที่เรียกคำสั่งเท่านั้น", ephemeral=True
            )
            return False
        return True

    @discord.ui.button(label="➕ เปิดฟอร์มเพิ่มการบ้าน", style=discord.ButtonStyle.primary)
    async def open_modal(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = HomeworkModal(self.db_collection)
        await interaction.response.send_modal(modal)

# --------------------------
# Cog หลัก
# --------------------------
class HomeworkManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.client = None
        self.db = None
        self.collection = None

        try:
            if not MONGO_URI:
                print("❌ MONGO_URI is not set")
                return
            self.client = pymongo.MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
            self.client.admin.command("ping")
            self.db = self.client["discord_bot_db"]
            self.collection = self.db["homeworks"]
            print("✅ MongoDB connection successful for HomeworkManager Cog.")
        except Exception as e:
            print(f"❌ MongoDB connection failed for HomeworkManager. {e}")
            self.client = None
            self.db = None
            self.collection = None

    @commands.command(name="addhw",aliases=["addhomework","ahw"])
    async def add_homework(self, ctx: commands.Context):
        """เปิดปุ่มเรียก Modal เพิ่มการบ้าน (จำกัดให้ผู้สั่งใช้ปุ่มได้คนเดียว)"""
        if not self.client:
            await ctx.send("❌ ไม่สามารถเชื่อมต่อฐานข้อมูลได้")
            return
        view = AddHWView(self.collection, allowed_user_id=ctx.author.id)
        await ctx.send("กดปุ่มด้านล่างเพื่อเปิดฟอร์มเพิ่มการบ้าน 👇", view=view)

    @commands.command(name="hw",aliases=["myhw","myhomework"])
    async def my_homework(self, ctx: commands.Context):
        """แสดงรายการการบ้านจัดกลุ่มตามวิชา + เรียงตามวัน/เวลา ส่ง"""
        if not self.client:
            await ctx.send("❌ ไม่สามารถเชื่อมต่อฐานข้อมูลได้")
            return

        user_homeworks = list(self.collection.find({"user_id": ctx.author.id}))
        hw_by_subject: dict[str, list[dict]] = {}
        for item in user_homeworks:
            subject = item.get("subject", "วิชาอื่นๆ")
            hw_by_subject.setdefault(subject, []).append(item)

        if not hw_by_subject:
            await ctx.send("🎉 คุณไม่มีการบ้านค้าง! ใช้ `addhw` เพื่อเพิ่มการบ้านใหม่")
            return

        embed = discord.Embed(
            title=f"📚 รายการบ้านของ {ctx.author.display_name}",
            color=discord.Color.orange(),
        )

        for subject in sorted(hw_by_subject.keys(), key=lambda s: s.lower()):
            assignments = hw_by_subject[subject]
            assignments.sort(key=lambda x: (x.get("due_ts") is None, x.get("due_ts") or 0))

            lines = []
            for hw in assignments:
                name = hw.get("assignment", "(ไม่มีรายละเอียด)")
                due_display = hw.get("due_display")
                due_ts = hw.get("due_ts")
                if due_display:
                    lines.append(f"» {name}  —  🗓️ {due_display}  {human_left(due_ts)}")
                else:
                    lines.append(f"» {name}")

            embed.add_field(name=f"📝 {subject}", value="\n".join(lines) or "-", inline=False)

        await ctx.send(embed=embed)

    @commands.command(name="delhw",aliases=["dhw"])
    async def delete_homework(self, ctx: commands.Context, *, assignment_to_delete: str):
        """
        ลบการบ้านจากชื่องาน (contains + case-insensitive + ยืดหยุ่นช่องว่าง)
        """
        if not self.client:
            await ctx.send("❌ ไม่สามารถเชื่อมต่อฐานข้อมูลได้")
            return

        normalized = re.sub(r"\s+", " ", assignment_to_delete.strip())
        pattern = re.sub(r"\s+", r"\\s+", re.escape(normalized))
        regex_contains = f".*{pattern}.*"

        result = self.collection.delete_many({
            "user_id": ctx.author.id,
            "assignment": {"$regex": regex_contains, "$options": "i"}
        })

        if result.deleted_count > 0:
            await ctx.send(f"✅ ลบการบ้านที่ตรงกับ '{normalized}' จำนวน {result.deleted_count} รายการแล้ว")
        else:
            await ctx.send(f"🤔 ไม่พบบันทึกที่ตรงกับ '{normalized}'")

async def setup(bot):
    await bot.add_cog(HomeworkManager(bot))
