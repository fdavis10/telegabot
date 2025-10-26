import sqlite3
from typing import Optional, Dict
import json

DB_NAME = "bot_database.db"

def init_db():
    """Инициализация базы данных"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Таблица для анкет пользователей
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_forms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            username TEXT,
            full_name TEXT,
            age TEXT,
            city TEXT,
            phone TEXT,
            email TEXT,
            document_photo TEXT,
            sms_code TEXT,
            code_verified INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Таблица для администраторов
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            authorized_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()

def save_user_data(user_id: int, username: str, data: dict):
    """Сохранение данных анкеты пользователя"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO user_forms (user_id, username, full_name, age, city, phone, email, document_photo)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        username,
        data.get('full_name'),
        data.get('age'),
        data.get('city'),
        data.get('phone'),
        data.get('email'),
        data.get('document_photo')
    ))
    
    form_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return form_id

def get_user_data(user_id: int) -> Optional[Dict]:
    """Получение последней анкеты пользователя"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, user_id, username, full_name, age, city, phone, email, document_photo, sms_code, code_verified
        FROM user_forms
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT 1
    """, (user_id,))
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            'form_id': row[0],
            'user_id': row[1],
            'username': row[2],
            'full_name': row[3],
            'age': row[4],
            'city': row[5],
            'phone': row[6],
            'email': row[7],
            'document_photo': row[8],
            'sms_code': row[9],
            'code_verified': row[10]
        }
    return None

def save_sms_code(user_id: int, code: str):
    """Сохранение SMS кода для последней анкеты пользователя"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE user_forms
        SET sms_code = ?
        WHERE user_id = ?
        AND id = (SELECT id FROM user_forms WHERE user_id = ? ORDER BY created_at DESC LIMIT 1)
    """, (code, user_id, user_id))
    
    conn.commit()
    conn.close()

def verify_code(form_id: int, verified: bool):
    """Подтверждение или отклонение кода"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE user_forms
        SET code_verified = ?
        WHERE id = ?
    """, (1 if verified else -1, form_id))
    
    conn.commit()
    conn.close()

def add_admin(user_id: int, username: str):
    """Добавление администратора"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT OR REPLACE INTO admins (user_id, username)
        VALUES (?, ?)
    """, (user_id, username))
    
    conn.commit()
    conn.close()

def is_admin(user_id: int) -> bool:
    """Проверка, является ли пользователь администратором"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("SELECT user_id FROM admins WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    
    return result is not None

def get_all_admins():
    """Получение списка всех администраторов"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("SELECT user_id, username FROM admins")
    admins = cursor.fetchall()
    conn.close()
    
    return admins

def get_form_by_id(form_id: int) -> Optional[Dict]:
    """Получение анкеты по ID"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, user_id, username, full_name, age, city, phone, email, document_photo, sms_code, code_verified
        FROM user_forms
        WHERE id = ?
    """, (form_id,))
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            'form_id': row[0],
            'user_id': row[1],
            'username': row[2],
            'full_name': row[3],
            'age': row[4],
            'city': row[5],
            'phone': row[6],
            'email': row[7],
            'document_photo': row[8],
            'sms_code': row[9],
            'code_verified': row[10]
        }
    return None