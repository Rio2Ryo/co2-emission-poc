#!/usr/bin/env python3
"""商品マスタサンプルデータ作成スクリプト"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.base import Base, ProductMaster
from app.db.session import engine, SessionLocal

# 商品マスタサンプルデータ（100 商品）
SAMPLE_PRODUCTS = [
    # 飲料 (15 商品)
    {"product_code": "BEV001", "product_name": "ペットボトル飲料 500ml", "category": "飲料", "subcategory": "清涼飲料", "scope": 3, "emission_factor": 0.38, "emission_unit": "本", "data_source": "IDEA v3.4", "description": "PET ボトル 500ml 清涼飲料水"},
    {"product_code": "BEV002", "product_name": "缶コーヒー 185ml", "category": "飲料", "subcategory": "コーヒー", "scope": 3, "emission_factor": 0.45, "emission_unit": "本", "data_source": "IDEA v3.4", "description": "スチール缶コーヒー 185ml"},
    {"product_code": "BEV003", "product_name": "牛乳 1L", "category": "飲料", "subcategory": "乳製品", "scope": 3, "emission_factor": 2.8, "emission_unit": "L", "data_source": "IDEA v3.4", "description": "牛乳 1L パック"},
    {"product_code": "BEV004", "product_name": "緑茶 500ml", "category": "飲料", "subcategory": "お茶", "scope": 3, "emission_factor": 0.35, "emission_unit": "本", "data_source": "IDEA v3.4", "description": "PET ボトル緑茶 500ml"},
    {"product_code": "BEV005", "product_name": "炭酸水 500ml", "category": "飲料", "subcategory": "清涼飲料", "scope": 3, "emission_factor": 0.32, "emission_unit": "本", "data_source": "IDEA v3.4", "description": "PET ボトル炭酸水 500ml"},
    {"product_code": "BEV006", "product_name": "果汁 100% オレンジジュース 1L", "category": "飲料", "subcategory": "ジュース", "scope": 3, "emission_factor": 1.2, "emission_unit": "L", "data_source": "IDEA v3.4", "description": "オレンジジュース 100% 1L"},
    {"product_code": "BEV007", "product_name": "ビール 350ml", "category": "飲料", "subcategory": "アルコール", "scope": 3, "emission_factor": 0.55, "emission_unit": "本", "data_source": "IDEA v3.4", "description": "ビール缶 350ml"},
    {"product_code": "BEV008", "product_name": "日本酒 1.8L", "category": "飲料", "subcategory": "アルコール", "scope": 3, "emission_factor": 2.1, "emission_unit": "本", "data_source": "IDEA v3.4", "description": "日本酒 1.8L 瓶"},
    {"product_code": "BEV009", "product_name": "ワイン 750ml", "category": "飲料", "subcategory": "アルコール", "scope": 3, "emission_factor": 1.8, "emission_unit": "本", "data_source": "IDEA v3.4", "description": "ワイン 750ml 瓶"},
    {"product_code": "BEV010", "product_name": "スポーツドリンク 500ml", "category": "飲料", "subcategory": "清涼飲料", "scope": 3, "emission_factor": 0.42, "emission_unit": "本", "data_source": "IDEA v3.4", "description": "スポーツドリンク 500ml"},
    {"product_code": "BEV011", "product_name": "エネルギー飲料 250ml", "category": "飲料", "subcategory": "清涼飲料", "scope": 3, "emission_factor": 0.48, "emission_unit": "本", "data_source": "IDEA v3.4", "description": "エナジードリンク 250ml"},
    {"product_code": "BEV012", "product_name": "豆乳 1L", "category": "飲料", "subcategory": "植物性", "scope": 3, "emission_factor": 0.95, "emission_unit": "L", "data_source": "IDEA v3.4", "description": "無調整豆乳 1L"},
    {"product_code": "BEV013", "product_name": "ミネラルウォーター 2L", "category": "飲料", "subcategory": "清涼飲料", "scope": 3, "emission_factor": 0.55, "emission_unit": "本", "data_source": "IDEA v3.4", "description": "ミネラルウォーター 2L"},
    {"product_code": "BEV014", "product_name": "ウイスキー 700ml", "category": "飲料", "subcategory": "アルコール", "scope": 3, "emission_factor": 2.5, "emission_unit": "本", "data_source": "IDEA v3.4", "description": "ウイスキー 700ml 瓶"},
    {"product_code": "BEV015", "product_name": "プロテインドリンク 500ml", "category": "飲料", "subcategory": "機能性", "scope": 3, "emission_factor": 0.85, "emission_unit": "本", "data_source": "IDEA v3.4", "description": "プロテイン飲料 500ml"},
    
    # 食品 (25 商品)
    {"product_code": "FOD001", "product_name": "弁当", "category": "食品", "subcategory": "調理食品", "scope": 3, "emission_factor": 2.5, "emission_unit": "個", "data_source": "IDEA v3.4", "description": "コンビニ弁当 標準"},
    {"product_code": "FOD002", "product_name": "おにぎり", "category": "食品", "subcategory": "調理食品", "scope": 3, "emission_factor": 0.45, "emission_unit": "個", "data_source": "IDEA v3.4", "description": "コンビニおにぎり"},
    {"product_code": "FOD003", "product_name": "パン（食パン 6 枚切）", "category": "食品", "subcategory": "パン", "scope": 3, "emission_factor": 0.85, "emission_unit": "袋", "data_source": "IDEA v3.4", "description": "食パン 6 枚切り"},
    {"product_code": "FOD004", "product_name": "カップ麺", "category": "食品", "subcategory": "インスタント", "scope": 3, "emission_factor": 0.65, "emission_unit": "個", "data_source": "IDEA v3.4", "description": "カップラーメン"},
    {"product_code": "FOD005", "product_name": "レトルトカレー", "category": "食品", "subcategory": "レトルト", "scope": 3, "emission_factor": 0.75, "emission_unit": "袋", "data_source": "IDEA v3.4", "description": "レトルトカレー 200g"},
    {"product_code": "FOD006", "product_name": "インスタントラーメン", "category": "食品", "subcategory": "インスタント", "scope": 3, "emission_factor": 0.55, "emission_unit": "袋", "data_source": "IDEA v3.4", "description": "袋麺 5 食パック"},
    {"product_code": "FOD007", "product_name": "スナック菓子", "category": "食品", "subcategory": "菓子", "scope": 3, "emission_factor": 0.48, "emission_unit": "袋", "data_source": "IDEA v3.4", "description": "ポテトチップス 60g"},
    {"product_code": "FOD008", "product_name": "チョコレート", "category": "食品", "subcategory": "菓子", "scope": 3, "emission_factor": 0.62, "emission_unit": "板", "data_source": "IDEA v3.4", "description": "板チョコレート 50g"},
    {"product_code": "FOD009", "product_name": "クッキー", "category": "食品", "subcategory": "菓子", "scope": 3, "emission_factor": 0.52, "emission_unit": "箱", "data_source": "IDEA v3.4", "description": "クッキー詰め合わせ"},
    {"product_code": "FOD010", "product_name": "ヨーグルト", "category": "食品", "subcategory": "乳製品", "scope": 3, "emission_factor": 0.35, "emission_unit": "個", "data_source": "IDEA v3.4", "description": "プレーンヨーグルト 100g"},
    {"product_code": "FOD011", "product_name": "チーズ", "category": "食品", "subcategory": "乳製品", "scope": 3, "emission_factor": 0.85, "emission_unit": "個", "data_source": "IDEA v3.4", "description": "プロセスチーズ 6 個"},
    {"product_code": "FOD012", "product_name": "ハム", "category": "食品", "subcategory": "加工肉", "scope": 3, "emission_factor": 0.72, "emission_unit": "袋", "data_source": "IDEA v3.4", "description": "ロースハム 5 枚"},
    {"product_code": "FOD013", "product_name": "ソーセージ", "category": "食品", "subcategory": "加工肉", "scope": 3, "emission_factor": 0.68, "emission_unit": "袋", "data_source": "IDEA v3.4", "description": "ウインナーソーセージ 8 本"},
    {"product_code": "FOD014", "product_name": "納豆", "category": "食品", "subcategory": "大豆製品", "scope": 3, "emission_factor": 0.18, "emission_unit": "パック", "data_source": "IDEA v3.4", "description": "納豆 3 パック"},
    {"product_code": "FOD015", "product_name": "豆腐", "category": "食品", "subcategory": "大豆製品", "scope": 3, "emission_factor": 0.22, "emission_unit": "丁", "data_source": "IDEA v3.4", "description": "木綿豆腐 300g"},
    {"product_code": "FOD016", "product_name": "卵", "category": "食品", "subcategory": "畜産", "scope": 3, "emission_factor": 0.42, "emission_unit": "パック", "data_source": "IDEA v3.4", "description": "鶏卵 10 個"},
    {"product_code": "FOD017", "product_name": "鶏むね肉", "category": "食品", "subcategory": "畜産", "scope": 3, "emission_factor": 1.8, "emission_unit": "kg", "data_source": "IDEA v3.4", "description": "鶏むね肉 1kg"},
    {"product_code": "FOD018", "product_name": "豚バラ肉", "category": "食品", "subcategory": "畜産", "scope": 3, "emission_factor": 3.2, "emission_unit": "kg", "data_source": "IDEA v3.4", "description": "豚バラ肉 1kg"},
    {"product_code": "FOD019", "product_name": "牛もも肉", "category": "食品", "subcategory": "畜産", "scope": 3, "emission_factor": 8.5, "emission_unit": "kg", "data_source": "IDEA v3.4", "description": "牛肉 もも 1kg"},
    {"product_code": "FOD020", "product_name": "鮭切り身", "category": "食品", "subcategory": "水産", "scope": 3, "emission_factor": 2.1, "emission_unit": "kg", "data_source": "IDEA v3.4", "description": "塩鮭切り身 1kg"},
    {"product_code": "FOD021", "product_name": "マグロ刺身", "category": "食品", "subcategory": "水産", "scope": 3, "emission_factor": 3.5, "emission_unit": "kg", "data_source": "IDEA v3.4", "description": "マグロ刺身用 1kg"},
    {"product_code": "FOD022", "product_name": "米（白米）", "category": "食品", "subcategory": "穀物", "scope": 3, "emission_factor": 1.2, "emission_unit": "kg", "data_source": "IDEA v3.4", "description": "白米 5kg"},
    {"product_code": "FOD023", "product_name": "パスタ", "category": "食品", "subcategory": "穀物", "scope": 3, "emission_factor": 0.85, "emission_unit": "袋", "data_source": "IDEA v3.4", "description": "乾燥パスタ 500g"},
    {"product_code": "FOD024", "product_name": "うどん（乾麺）", "category": "食品", "subcategory": "穀物", "scope": 3, "emission_factor": 0.72, "emission_unit": "袋", "data_source": "IDEA v3.4", "description": "うどん乾麺 500g"},
    {"product_code": "FOD025", "product_name": "冷凍ピザ", "category": "食品", "subcategory": "冷凍食品", "scope": 3, "emission_factor": 1.1, "emission_unit": "個", "data_source": "IDEA v3.4", "description": "冷凍ピザ 1 枚"},
    
    # 日用品 (20 商品)
    {"product_code": "DLY001", "product_name": "トイレットペーパー", "category": "日用品", "subcategory": "紙製品", "scope": 3, "emission_factor": 0.45, "emission_unit": "ロール", "data_source": "IDEA v3.4", "description": "トイレットペーパー 1 ロール"},
    {"product_code": "DLY002", "product_name": "ティッシュ", "category": "日用品", "subcategory": "紙製品", "scope": 3, "emission_factor": 0.28, "emission_unit": "箱", "data_source": "IDEA v3.4", "description": "ボックスティッシュ"},
    {"product_code": "DLY003", "product_name": "コピー用紙 A4", "category": "日用品", "subcategory": "紙製品", "scope": 3, "emission_factor": 1.8, "emission_unit": "kg", "data_source": "IDEA v3.4", "description": "コピー用紙 A4 500 枚"},
    {"product_code": "DLY004", "product_name": "洗剤（洗濯用）", "category": "日用品", "subcategory": "洗剤", "scope": 3, "emission_factor": 0.85, "emission_unit": "kg", "data_source": "IDEA v3.4", "description": "洗濯洗剤 1kg"},
    {"product_code": "DLY005", "product_name": "食器用洗剤", "category": "日用品", "subcategory": "洗剤", "scope": 3, "emission_factor": 0.62, "emission_unit": "本", "data_source": "IDEA v3.4", "description": "食器用洗剤 500ml"},
    {"product_code": "DLY006", "product_name": "シャンプー", "category": "日用品", "subcategory": "化粧品", "scope": 3, "emission_factor": 0.55, "emission_unit": "本", "data_source": "IDEA v3.4", "description": "シャンプー 500ml"},
    {"product_code": "DLY007", "product_name": "ボディソープ", "category": "日用品", "subcategory": "化粧品", "scope": 3, "emission_factor": 0.52, "emission_unit": "本", "data_source": "IDEA v3.4", "description": "ボディソープ 500ml"},
    {"product_code": "DLY008", "product_name": "歯磨き粉", "category": "日用品", "subcategory": "化粧品", "scope": 3, "emission_factor": 0.28, "emission_unit": "本", "data_source": "IDEA v3.4", "description": "歯磨き粉 100g"},
    {"product_code": "DLY009", "product_name": "ハンドソープ", "category": "日用品", "subcategory": "化粧品", "scope": 3, "emission_factor": 0.35, "emission_unit": "本", "data_source": "IDEA v3.4", "description": "ハンドソープ 250ml"},
    {"product_code": "DLY010", "product_name": "ゴミ袋", "category": "日用品", "subcategory": "プラスチック", "scope": 3, "emission_factor": 0.42, "emission_unit": "枚", "data_source": "IDEA v3.4", "description": "ゴミ袋 45L 10 枚"},
    {"product_code": "DLY011", "product_name": "ラップ", "category": "日用品", "subcategory": "プラスチック", "scope": 3, "emission_factor": 0.38, "emission_unit": "箱", "data_source": "IDEA v3.4", "description": "食品用ラップ"},
    {"product_code": "DLY012", "product_name": "アルミホイル", "category": "日用品", "subcategory": "金属", "scope": 3, "emission_factor": 0.65, "emission_unit": "箱", "data_source": "IDEA v3.4", "description": "アルミホイル 10m"},
    {"product_code": "DLY013", "product_name": "乾電池 AA", "category": "日用品", "subcategory": "電池", "scope": 3, "emission_factor": 0.18, "emission_unit": "本", "data_source": "IDEA v3.4", "description": "単三乾電池"},
    {"product_code": "DLY014", "product_name": "LED 電球", "category": "日用品", "subcategory": "電気", "scope": 3, "emission_factor": 1.2, "emission_unit": "個", "data_source": "IDEA v3.4", "description": "LED 電球 E26"},
    {"product_code": "DLY015", "product_name": "タオル", "category": "日用品", "subcategory": "繊維", "scope": 3, "emission_factor": 0.85, "emission_unit": "枚", "data_source": "IDEA v3.4", "description": "フェイスタオル"},
    {"product_code": "DLY016", "product_name": "T シャツ", "category": "日用品", "subcategory": "繊維", "scope": 3, "emission_factor": 4.5, "emission_unit": "枚", "data_source": "IDEA v3.4", "description": "コットン T シャツ"},
    {"product_code": "DLY017", "product_name": "ジーンズ", "category": "日用品", "subcategory": "繊維", "scope": 3, "emission_factor": 12.5, "emission_unit": "枚", "data_source": "IDEA v3.4", "description": "デニムジーンズ"},
    {"product_code": "DLY018", "product_name": "靴下", "category": "日用品", "subcategory": "繊維", "scope": 3, "emission_factor": 0.65, "emission_unit": "足", "data_source": "IDEA v3.4", "description": "コットン靴下"},
    {"product_code": "DLY019", "product_name": "ハンカチ", "category": "日用品", "subcategory": "繊維", "scope": 3, "emission_factor": 0.25, "emission_unit": "枚", "data_source": "IDEA v3.4", "description": "コットンハンカチ"},
    {"product_code": "DLY020", "product_name": "マスク", "category": "日用品", "subcategory": "衛生", "scope": 3, "emission_factor": 0.08, "emission_unit": "枚", "data_source": "IDEA v3.4", "description": "不織布マスク"},
    
    # 電子機器 (15 商品)
    {"product_code": "ELE001", "product_name": "スマートフォン", "category": "電子機器", "subcategory": "通信", "scope": 3, "emission_factor": 55.0, "emission_unit": "台", "data_source": "IDEA v3.4", "description": "スマートフォン 1 台"},
    {"product_code": "ELE002", "product_name": "ノート PC", "category": "電子機器", "subcategory": "电脑", "scope": 3, "emission_factor": 180.0, "emission_unit": "台", "data_source": "IDEA v3.4", "description": "ノートパソコン 1 台"},
    {"product_code": "ELE003", "product_name": "デスクトップ PC", "category": "電子機器", "subcategory": "电脑", "scope": 3, "emission_factor": 250.0, "emission_unit": "台", "data_source": "IDEA v3.4", "description": "デスクトップパソコン"},
    {"product_code": "ELE004", "product_name": "モニター 24 インチ", "category": "電子機器", "subcategory": "周辺機器", "scope": 3, "emission_factor": 85.0, "emission_unit": "台", "data_source": "IDEA v3.4", "description": "液晶モニター 24 インチ"},
    {"product_code": "ELE005", "product_name": "キーボード", "category": "電子機器", "subcategory": "周辺機器", "scope": 3, "emission_factor": 8.5, "emission_unit": "個", "data_source": "IDEA v3.4", "description": "USB キーボード"},
    {"product_code": "ELE006", "product_name": "マウス", "category": "電子機器", "subcategory": "周辺機器", "scope": 3, "emission_factor": 4.2, "emission_unit": "個", "data_source": "IDEA v3.4", "description": "USB マウス"},
    {"product_code": "ELE007", "product_name": "タブレット", "category": "電子機器", "subcategory": "通信", "scope": 3, "emission_factor": 45.0, "emission_unit": "台", "data_source": "IDEA v3.4", "description": "タブレット端末"},
    {"product_code": "ELE008", "product_name": "デジタルカメラ", "category": "電子機器", "subcategory": "カメラ", "scope": 3, "emission_factor": 35.0, "emission_unit": "台", "data_source": "IDEA v3.4", "description": "デジタル一眼カメラ"},
    {"product_code": "ELE009", "product_name": "テレビ 55 インチ", "category": "電子機器", "subcategory": "家電", "scope": 3, "emission_factor": 220.0, "emission_unit": "台", "data_source": "IDEA v3.4", "description": "液晶テレビ 55 インチ"},
    {"product_code": "ELE010", "product_name": "冷蔵庫", "category": "電子機器", "subcategory": "家電", "scope": 3, "emission_factor": 180.0, "emission_unit": "台", "data_source": "IDEA v3.4", "description": "冷蔵庫 400L"},
    {"product_code": "ELE011", "product_name": "洗濯機", "category": "電子機器", "subcategory": "家電", "scope": 3, "emission_factor": 120.0, "emission_unit": "台", "data_source": "IDEA v3.4", "description": "洗濯機 8kg"},
    {"product_code": "ELE012", "product_name": "エアコン", "category": "電子機器", "subcategory": "家電", "scope": 3, "emission_factor": 150.0, "emission_unit": "台", "data_source": "IDEA v3.4", "description": "ルームエアコン"},
    {"product_code": "ELE013", "product_name": "電子レンジ", "category": "電子機器", "subcategory": "家電", "scope": 3, "emission_factor": 45.0, "emission_unit": "台", "data_source": "IDEA v3.4", "description": "電子レンジ 20L"},
    {"product_code": "ELE014", "product_name": "掃除機", "category": "電子機器", "subcategory": "家電", "scope": 3, "emission_factor": 35.0, "emission_unit": "台", "data_source": "IDEA v3.4", "description": "掃除機"},
    {"product_code": "ELE015", "product_name": "USB メモリ 32GB", "category": "電子機器", "subcategory": "周辺機器", "scope": 3, "emission_factor": 1.2, "emission_unit": "個", "data_source": "IDEA v3.4", "description": "USB メモリ 32GB"},
    
    # 文具 (15 商品)
    {"product_code": "STA001", "product_name": "ボールペン", "category": "文具", "subcategory": "筆記具", "scope": 3, "emission_factor": 0.08, "emission_unit": "本", "data_source": "IDEA v3.4", "description": "油性ボールペン"},
    {"product_code": "STA002", "product_name": "シャープペンシル", "category": "文具", "subcategory": "筆記具", "scope": 3, "emission_factor": 0.12, "emission_unit": "本", "data_source": "IDEA v3.4", "description": "シャープペン 0.5mm"},
    {"product_code": "STA003", "product_name": "鉛筆", "category": "文具", "subcategory": "筆記具", "scope": 3, "emission_factor": 0.05, "emission_unit": "本", "data_source": "IDEA v3.4", "description": "木製鉛筆 HB"},
    {"product_code": "STA004", "product_name": "消しゴム", "category": "文具", "subcategory": "筆記具", "scope": 3, "emission_factor": 0.03, "emission_unit": "個", "data_source": "IDEA v3.4", "description": "プラスチック消しゴム"},
    {"product_code": "STA005", "product_name": "ノート A5", "category": "文具", "subcategory": "紙製品", "scope": 3, "emission_factor": 0.25, "emission_unit": "冊", "data_source": "IDEA v3.4", "description": "キャンパスノート A5"},
    {"product_code": "STA006", "product_name": "付箋", "category": "文具", "subcategory": "紙製品", "scope": 3, "emission_factor": 0.08, "emission_unit": "冊", "data_source": "IDEA v3.4", "description": "付箋 50 枚"},
    {"product_code": "STA007", "product_name": "ホッチキス", "category": "文具", "subcategory": "事務用品", "scope": 3, "emission_factor": 0.35, "emission_unit": "個", "data_source": "IDEA v3.4", "description": "ホッチキス"},
    {"product_code": "STA008", "product_name": " staples", "category": "文具", "subcategory": "事務用品", "scope": 3, "emission_factor": 0.02, "emission_unit": "箱", "data_source": "IDEA v3.4", "description": "ホッチキス針 1000 本"},
    {"product_code": "STA009", "product_name": "クリップ", "category": "文具", "subcategory": "事務用品", "scope": 3, "emission_factor": 0.01, "emission_unit": "個", "data_source": "IDEA v3.4", "description": "ペーパークリップ"},
    {"product_code": "STA010", "product_name": "ファイル A4", "category": "文具", "subcategory": "事務用品", "scope": 3, "emission_factor": 0.18, "emission_unit": "個", "data_source": "IDEA v3.4", "description": "クリアファイル A4"},
    {"product_code": "STA011", "product_name": "バインダー A4", "category": "文具", "subcategory": "事務用品", "scope": 3, "emission_factor": 0.45, "emission_unit": "個", "data_source": "IDEA v3.4", "description": "リングバインダー A4"},
    {"product_code": "STA012", "product_name": "ハサミ", "category": "文具", "subcategory": "事務用品", "scope": 3, "emission_factor": 0.22, "emission_unit": "個", "data_source": "IDEA v3.4", "description": "事務用ハサミ"},
    {"product_code": "STA013", "product_name": "カッター", "category": "文具", "subcategory": "事務用品", "scope": 3, "emission_factor": 0.15, "emission_unit": "個", "data_source": "IDEA v3.4", "description": "カッターナイフ"},
    {"product_code": "STA014", "product_name": "のり", "category": "文具", "subcategory": "事務用品", "scope": 3, "emission_factor": 0.08, "emission_unit": "本", "data_source": "IDEA v3.4", "description": "固形のり"},
    {"product_code": "STA015", "product_name": "マーカー", "category": "文具", "subcategory": "筆記具", "scope": 3, "emission_factor": 0.12, "emission_unit": "本", "data_source": "IDEA v3.4", "description": "蛍光マーカー"},
    
    # 包装資材 (10 商品)
    {"product_code": "PKG001", "product_name": "段ボール箱 S", "category": "包装資材", "subcategory": "段ボール", "scope": 3, "emission_factor": 0.35, "emission_unit": "個", "data_source": "IDEA v3.4", "description": "段ボール箱 小"},
    {"product_code": "PKG002", "product_name": "段ボール箱 M", "category": "包装資材", "subcategory": "段ボール", "scope": 3, "emission_factor": 0.55, "emission_unit": "個", "data_source": "IDEA v3.4", "description": "段ボール箱 中"},
    {"product_code": "PKG003", "product_name": "段ボール箱 L", "category": "包装資材", "subcategory": "段ボール", "scope": 3, "emission_factor": 0.85, "emission_unit": "個", "data_source": "IDEA v3.4", "description": "段ボール箱 大"},
    {"product_code": "PKG004", "product_name": "プチプチ", "category": "包装資材", "subcategory": "緩衝材", "scope": 3, "emission_factor": 0.42, "emission_unit": "m", "data_source": "IDEA v3.4", "description": "気泡緩衝材 1m"},
    {"product_code": "PKG005", "product_name": "包装紙", "category": "包装資材", "subcategory": "紙", "scope": 3, "emission_factor": 0.18, "emission_unit": "枚", "data_source": "IDEA v3.4", "description": "包装紙 1 枚"},
    {"product_code": "PKG006", "product_name": "リボン", "category": "包装資材", "subcategory": "装飾", "scope": 3, "emission_factor": 0.08, "emission_unit": "m", "data_source": "IDEA v3.4", "description": "包装リボン 1m"},
    {"product_code": "PKG007", "product_name": "封筒 長形 3 号", "category": "包装資材", "subcategory": "封筒", "scope": 3, "emission_factor": 0.12, "emission_unit": "枚", "data_source": "IDEA v3.4", "description": "長形 3 号封筒"},
    {"product_code": "PKG008", "product_name": "封筒 角形 2 号", "category": "包装資材", "subcategory": "封筒", "scope": 3, "emission_factor": 0.18, "emission_unit": "枚", "data_source": "IDEA v3.4", "description": "角形 2 号封筒"},
    {"product_code": "PKG009", "product_name": "ビニール袋", "category": "包装資材", "subcategory": "プラスチック", "scope": 3, "emission_factor": 0.05, "emission_unit": "枚", "data_source": "IDEA v3.4", "description": "レジ袋"},
    {"product_code": "PKG010", "product_name": "ガムテープ", "category": "包装資材", "subcategory": "テープ", "scope": 3, "emission_factor": 0.15, "emission_unit": "巻", "data_source": "IDEA v3.4", "description": "OPP ガムテープ"},
]


def main():
    print("=== 商品マスタサンプルデータ作成 ===\n")
    
    # DB テーブル作成
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # 既存データをクリア
        db.query(ProductMaster).delete()
        db.commit()
        print("既存データをクリアしました")
        
        # サンプルデータ投入
        created_count = 0
        for prod in SAMPLE_PRODUCTS:
            product = ProductMaster(**prod)
            db.add(product)
            created_count += 1
        
        db.commit()
        print(f"✅ {created_count} 件の商品マスタを登録しました")
        
        # 確認
        total = db.query(ProductMaster).count()
        print(f"\n商品マスタ総数：{total} 件")
        
        # カテゴリ別集計
        print("\nカテゴリ別内訳:")
        from sqlalchemy import func
        results = db.query(
            ProductMaster.category, 
            func.count(ProductMaster.id)
        ).group_by(ProductMaster.category).all()
        
        for cat, cnt in results:
            print(f"  {cat}: {cnt} 件")
            
    finally:
        db.close()


if __name__ == "__main__":
    main()
