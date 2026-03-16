#!/usr/bin/env python3
"""デモユーザー作成スクリプト"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.base import Base, User
from app.db.session import engine, SessionLocal
from app.api.v1.auth import hash_password

def main():
    print("=== デモユーザー作成 ===\n")
    
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # 既存ユーザーをクリア
        db.query(User).delete()
        db.commit()
        print("既存ユーザーをクリアしました")
        
        # デモユーザー作成
        users = [
            {"email": "admin@demo.com", "password": "demo123", "role": "admin"},
            {"email": "user@demo.com", "password": "demo123", "role": "user"},
            {"email": "yakon@demo.com", "password": "demo123", "role": "admin"},
        ]
        
        for u in users:
            user = User(
                email=u["email"],
                password_hash=hash_password(u["password"]),
                role=u["role"],
            )
            db.add(user)
            print(f"✅ {u['email']} ({u['role']}) を作成")
        
        db.commit()
        
        total = db.query(User).count()
        print(f"\n✅ 合計 {total} 人のユーザーを作成しました")
        
        print("\n📋 ログイン情報:")
        print("   admin@demo.com / demo123 (管理者)")
        print("   user@demo.com / demo123 (一般)")
        print("   yakon@demo.com / demo123 (管理者)")
        
    finally:
        db.close()


if __name__ == "__main__":
    main()
