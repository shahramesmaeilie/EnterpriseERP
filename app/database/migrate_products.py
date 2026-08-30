# app/database/migrate_products.py
import sqlite3
from pathlib import Path

def migrate_products_table():
    """
    اضافه کردن ستون‌های جدید به جدول products
    بدون حذف دیتای موجود
    """
    db_path = Path("enterprise.db")
    
    if not db_path.exists():
        print("❌ فایل دیتابیس پیدا نشد!")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # بررسی ستون‌های موجود
        cursor.execute("PRAGMA table_info(products)")
        existing_columns = {row[1] for row in cursor.fetchall()}
        print(f"ستون‌های موجود: {existing_columns}")
        
        # لیست ستون‌های جدید که باید اضافه شوند
        new_columns = {
            'barcode': 'TEXT DEFAULT ""',
            'barcode_type': 'TEXT DEFAULT "1D"',
            'quantity': 'INTEGER DEFAULT 0',
            'unit_price': 'REAL DEFAULT 0.0',
            'description': 'TEXT DEFAULT ""'
        }
        
        # اضافه کردن ستون‌های جدید
        for col_name, col_def in new_columns.items():
            if col_name not in existing_columns:
                try:
                    cursor.execute(f"ALTER TABLE products ADD COLUMN {col_name} {col_def}")
                    print(f"✅ ستون {col_name} اضافه شد")
                except sqlite3.OperationalError as e:
                    print(f"⚠️  ستون {col_name}: {e}")
        
        # اگر price و unit_price هر دو وجود دارند، داده‌ها را کپی کن
        cursor.execute("PRAGMA table_info(products)")
        final_columns = {row[1] for row in cursor.fetchall()}
        
        if 'price' in final_columns and 'unit_price' in final_columns:
            cursor.execute("UPDATE products SET unit_price = price WHERE unit_price = 0")
            print("✅ مقادیر price به unit_price کپی شد")
        
        if 'stock' in final_columns and 'quantity' in final_columns:
            cursor.execute("UPDATE products SET quantity = stock WHERE quantity = 0")
            print("✅ مقادیر stock به quantity کپی شد")
        
        conn.commit()
        
        # نمایش ساختار نهایی
        cursor.execute("PRAGMA table_info(products)")
        print("\n📋 ساختار نهایی جدول products:")
        for row in cursor.fetchall():
            print(f"  - {row[1]} ({row[2]})")
        
        print("\n✅ Migration با مفقیت انجام شد!")
        return True
        
    except Exception as e:
        print(f"❌ خطا: {e}")
        conn.rollback()
        return False
        
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_products_table()
