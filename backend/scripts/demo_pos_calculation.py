#!/usr/bin/env python3
"""POS デモ：商品マスタ連携で CO2 算出"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# POS サンプルデータ（商品マスタと連携）
POS_DATA = [
    {"product_code": "BEV001", "product_name": "ペットボトル飲料 500ml", "quantity": 10, "unit_price": 150, "store": "新宿店"},
    {"product_code": "BEV002", "product_name": "缶コーヒー 185ml", "quantity": 5, "unit_price": 120, "store": "新宿店"},
    {"product_code": "FOD001", "product_name": "弁当", "quantity": 8, "unit_price": 450, "store": "新宿店"},
    {"product_code": "FOD002", "product_name": "おにぎり", "quantity": 20, "unit_price": 130, "store": "渋谷店"},
    {"product_code": "BEV007", "product_name": "ビール 350ml", "quantity": 12, "unit_price": 280, "store": "新宿店"},
    {"product_code": "DLY001", "product_name": "トイレットペーパー", "quantity": 6, "unit_price": 180, "store": "渋谷店"},
    {"product_code": "DLY016", "product_name": "T シャツ", "quantity": 3, "unit_price": 2500, "store": "新宿店"},
    {"product_code": "ELE001", "product_name": "スマートフォン", "quantity": 2, "unit_price": 80000, "store": "新宿店"},
    {"product_code": "STA001", "product_name": "ボールペン", "quantity": 50, "unit_price": 120, "store": "渋谷店"},
    {"product_code": "PKG002", "product_name": "段ボール箱 M", "quantity": 20, "unit_price": 80, "store": "物流センター"},
    {"product_code": "UNKNOWN1", "product_name": "未登録商品", "quantity": 5, "unit_price": 100, "store": "新宿店"},  # 未登録商品
]


def main():
    print("=== POS デモ：商品マスタ連携 CO2 算出 ===\n")
    
    # API 呼び出し
    response = client.post("/api/v1/pos", json={"rows": POS_DATA})
    
    if response.status_code != 202:
        print(f"❌ エラー：{response.status_code}")
        print(response.text)
        return
    
    result = response.json()
    
    print(f"✅ 算出完了！")
    print(f"   ジョブ ID: {result['job_id']}")
    print(f"   行数：{result['row_count']}")
    print(f"   分類済：{result['calculated_count']}")
    print(f"   未分類：{result['unclassified_count']}")
    
    print(f"\n📊 Scope 別集計:")
    ss = result['scope_summary']
    print(f"   Scope 1: {ss['scope1']:.2f} kg-CO2e")
    print(f"   Scope 2: {ss['scope2']:.2f} kg-CO2e")
    print(f"   Scope 3: {ss['scope3']:.2f} kg-CO2e")
    print(f"   合計   : {ss['grand_total']:.2f} kg-CO2e")
    
    print(f"\n📦 カテゴリ別集計:")
    for cat, data in sorted(result['category_summary'].items(), key=lambda x: -x[1]['total']):
        print(f"   {cat}: {data['total']:.2f} kg-CO2e ({data['count']} 件)")
    
    print(f"\n📋 行別詳細:")
    for row in result['rows']:
        status = "✅" if row['status'] == 'calculated' else "❌"
        emission = f"{row['emission']:.3f} kg" if row['status'] == 'calculated' else "未登録"
        print(f"   {status} {row['product_code']} ({row['product_name']}): {row['quantity']} 個 → {emission}")
    
    print("\n=== デモ完了 ===")


if __name__ == "__main__":
    main()
