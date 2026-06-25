from database import get_daily_attendance, get_attendance_report, get_attendance_log, get_employee_by_name, export_monthly_report_to_csv
from datetime import datetime, timedelta
from utils import read_input


def print_daily_attendance():
    """Kunlik davomat bo'yicha hisobi."""
    print("\n" + "="*70)
    print("📊 KUNLIK DAVOMAT HISOBI")
    print("="*70)
    
    date = read_input("Sanani kiriting (YYYY-MM-DD) [bugun]: ")
    if date is None:
        return
    if not date:
        date = datetime.now().date()
    else:
        try:
            date = datetime.strptime(date, "%Y-%m-%d").date()
        except:
            print("❌ Noto'g'ri format!")
            return
    
    records = get_daily_attendance(date)
    
    if not records:
        print("❌ Shu sanada qaydlar yo'q!")
        return
    
    print(f"\n📅 Sana: {date.strftime('%d.%m.%Y (%A)')}\n")
    print(f"{'Ismi':<25} {'Departament':<20} {'Kelib':<8} {'Ketdi':<8} {'Ish vaqti':<12} {'Xolati':<10}")
    print("-" * 85)
    
    keldi_count = 0
    for record in records:
        name = record['name'] if record['name'] else "Qaydlanmadi"
        dept = record['department'] if record['department'] else "-"
        entry = record['entry_time'].strftime('%H:%M') if record['entry_time'] else "-"
        exit_t = record['exit_time'].strftime('%H:%M') if record['exit_time'] else "-"
        work_hours = f"{record['work_hours']:.1f} soat" if record['work_hours'] is not None else "-"
        status = record['status'] if record['status'] else "-"
        
        if entry != "-":
            keldi_count += 1
        
        print(f"{name:<25} {dept:<20} {entry:<8} {exit_t:<8} {work_hours:<12} {status:<10}")
    
    print("-" * 85)
    print(f"✅ Keldi: {keldi_count} ta\n")


def print_weekly_report():
    """Haftalik hisobi."""
    print("\n" + "="*80)
    print("📈 HAFTALIK DAVOMAT HISOBI")
    print("="*80)
    
    days = 7
    start_date = (datetime.now() - timedelta(days=days)).date()
    end_date = datetime.now().date()
    
    report = get_attendance_report(start_date, end_date)
    
    if not report:
        print("❌ Qaydlar yo'q!")
        return
    
    print(f"\n📅 Davr: {start_date} dan {end_date} gacha\n")
    print("{:<25} {:<20} {:<8} {:<8} {:<8} {:<10}".format(
        "Ismi", "Departament", "Kunlar", "Keldi", "Kech", "O'rtacha"
    ))
    print("-" * 85)
    
    for record in report:
        name = record['name'] if record['name'] else "Noma'lum"
        dept = record['department'] if record['department'] else "-"
        kunlar = record['kam_kunlar'] if record['kam_kunlar'] else 0
        keldi = record['keldi'] if record['keldi'] else 0
        kech = record['kech_keldi'] if record['kech_keldi'] else 0
        avg_time = f"{record['orta_vaqt']:.1f}h" if record['orta_vaqt'] else "-"
        
        print(f"{name:<25} {dept:<20} {kunlar:<8} {keldi:<8} {kech:<8} {avg_time:<10}")
    
    print("-" * 85 + "\n")


def print_employee_log():
    """Bitta xodimning kelib ketish tarixi."""
    print("\n" + "="*80)
    print("📋 XODIM KELIB KETISH TARIXI")
    print("="*80)
    
    name = read_input("\nXodimning ismini kiriting: ")
    if name is None:
        return
    if not name:
        print("❌ Ism kiriting!")
        return
    
    employee = get_employee_by_name(name)
    if not employee:
        print(f"❌ '{name}' xodim topilmadi!")
        return
    
    days = read_input("Qancha kunning historiyasi? [7]: ")
    if days is None:
        return
    try:
        days = int(days) if days else 7
    except:
        days = 7
    
    logs = get_attendance_log(employee['id'], days)
    
    if not logs:
        print(f"❌ {name} uchun qaydlar yo'q!")
        return
    
    print(f"\n👤 {name} (Departament: {employee['department']})")
    print(f"💼 Lavozim: {employee['position']}\n")
    print(f"{'Vaqt':<20} {'Harakat':<10} {'Ishonch':<10}")
    print("-" * 45)
    
    for log in logs:
        time_str = log['timestamp'].strftime('%Y-%m-%d %H:%M')
        action = "KELIB ✓" if log['action'] == 'entry' else "KETGAN ✗"
        conf = f"{log['confidence']:.0f}%" if log['confidence'] else "-"
        
        print(f"{time_str:<20} {action:<10} {conf:<10}")
    
    print("-" * 45 + "\n")


def export_report_ui():
    """Eksport qilish uchun foydalanuvchi interfeysi."""
    print("\n" + "="*50)
    print("📥 OYLIK HISOBOTNI EXCELGA YUKLASH")
    print("="*50)
    
    now = datetime.now()
    year_input = read_input(f"Yilni kiriting [{now.year}]: ")
    year = int(year_input) if year_input else now.year
    
    month_input = read_input(f"Oyni kiriting (1-12) [{now.month}]: ")
    month = int(month_input) if month_input else now.month
    
    filename = export_monthly_report_to_csv(year, month)
    
    if filename:
        print(f"\n✅ Hisobot yaratildi: {filename}")
    elif filename is False:
        print("\n⚠️ Ushbu davr uchun ma'lumot topilmadi.")
    else:
        print("\n❌ Eksport qilishda xato yuz berdi.")

def print_menu():
    """Asosiy menyu."""
    while True:
        print("\n" + "="*50)
        print("🏦 BANK DAVOMAT TIZIMI - HISOBOT")
        print("="*50)
        print("1. 📊 Kunlik davomat hisobi")
        print("2. 📈 Haftalik hisobi")
        print("3. 📋 Xodimning tarixi")
        print("4. 📥 Excelga yuklash (.csv)")
        print("5. ❌ Chiqish")
        print("="*50)
        
        choice = read_input("Variantni tanlang (1-4): ")
        if choice is None:
            break
        
        if choice == "1":
            print_daily_attendance()
        elif choice == "2":
            print_weekly_report()
        elif choice == "3":
            print_employee_log()
        elif choice == "4":
            export_report_ui()
        elif choice == "5":
            print("\n✅ Chiqilmoqda...\n")
            break
        else:
            print("❌ Noto'g'ri variant!")


if __name__ == "__main__":
    print_menu()
