# migrate_add_retail_price.py
import sqlite3
import shutil
from datetime import datetime
from pathlib import Path

def migrate_database():
    """
    Migration script to add retail_price column to products table.
    Creates backup before making any changes.
    """
    # مسیر دیتابیس اصلی
    db_path = Path("enterprise.db")
    
    if not db_path.exists():
        print(f"❌ خطا: فایل دیتابیس '{db_path}' یافت نشد!")
        return False
    
    # ایجاد Backup
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = Path(f"enterprise_backup_{timestamp}.db")
    
    try:
        print(f"📦 ایجاد Backup: {backup_path}")
        shutil.copy2(db_path, backup_path)
        print("✅ Backup با موفقیت ایجاد شد")
        
        # اتصال به دیتابیس
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # بررسی وجود جدول products
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='products'
        """)
        
        if not cursor.fetchone():
            print("❌ خطا: جدول 'products' یافت نشد!")
            conn.close()
            return False
        
        # بررسی وجود ستون retail_price
        cursor.execute("PRAGMA table_info(products)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'retail_price' in columns:
            print("ℹ️  ستون 'retail_price' از قبل وجود دارد")
            conn.close()
            return True
        
        # افزودن ستون retail_price
        print("🔧 افزودن ستون 'retail_price' به جدول products...")
        cursor.execute("""
            ALTER TABLE products 
            ADD COLUMN retail_price REAL DEFAULT 0.0
        """)
        
        conn.commit()
        
        # تأیید تغییرات
        cursor.execute("PRAGMA table_info(products)")
        columns_after = [row[1] for row in cursor.fetchall()]
        
        if 'retail_price' in columns_after:
            print("✅ Migration با موفقیت انجام شد!")
            print(f"   - ستون 'retail_price' اضافه شد")
            print(f"   - مقدار پیش‌فرض: 0.0")
            print(f"   - Backup ذخیره شد در: {backup_path}")
            
            # نمایش تعداد محصولات موجود
            cursor.execute("SELECT COUNT(*) FROM products")
            product_count = cursor.fetchone()[0]
            print(f"   - تعداد محصولات موجود: {product_count}")
            
            success = True
        else:
            print("❌ خطا: افزودن ستون ناموفق بود")
            success = False
        
        conn.close()
        return success
        
    except sqlite3.Error as e:
        print(f"❌ خطای دیتابیس: {e}")
        print(f"   می‌توانید از Backup استفاده کنید: {backup_path}")
        return False
    except Exception as e:
        print(f"❌ خطای غیرمنتظره: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("🔄 Migration: افزودن ستون retail_price")
    print("=" * 60)
    print()
    
    success = migrate_database()
    
    print()
    print("=" * 60)
    if success:
        print("✅ Migration کامل شد")
        print()
        print("گام بعدی:")
        print("  - برنامه را اجرا کنید: python main.py")
        print("  - قابلیت Retail Price آماده استفاده است")
    else:
        print("❌ Migration ناموفق بود")
        print("  - از Backup برای بازگردانی استفاده کنید")
    print("=" * 60)
