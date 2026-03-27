"""
自動車カタログDBのセットアップスクリプト。
トヨタ・ホンダ・スバルの人気車種各5台（計15台）のデータを投入する。
実行: python setup_car_db.py
"""

import os
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.getenv("MEMORY_DATABASE_URL", "postgresql://postgres:postgres@localhost:5433/agent_memory")

# ──────────────────────────────────────────
# 車種データ（2023〜2024年モデル）
# ──────────────────────────────────────────
CAR_DATA = [
    # ===== Toyota =====
    {
        "manufacturer": "トヨタ",
        "model_name": "プリウス",
        "year": 2023,
        "body_type": "セダン（ファストバック）",
        "engine_type": "2.0L TNGA アトキンソンサイクル + 電気モーター（ハイブリッド）",
        "max_power_ps": 196,
        "fuel_economy_wltc": 28.6,
        "seating_capacity": 5,
        "price_min_man_yen": 275,
        "drivetrain": "FF / E-Four（4WD）",
        "safety_features": "Toyota Safety Sense 3.0（プリクラッシュセーフティ、レーンディパーチャーアラート、レーダークルーズコントロール、オートマチックハイビーム）",
        "key_features": "5代目フルモデルチェンジ。低重心スポーティデザイン。E-Fourによる電気式4WD設定。夜間でも機能するプリクラッシュセーフティ。PHEVモデルも設定",
        "description": "トヨタを代表するハイブリッド専用車。5代目となる2023年モデルは低重心・ワイドなスポーティデザインに刷新。2.0LハイブリッドシステムとE-Four（電気式4WD）を組み合わせ、28.6km/LのWLTC燃費を達成。Toyota Safety Sense 3.0搭載で先進安全性能も充実。",
    },
    {
        "manufacturer": "トヨタ",
        "model_name": "ハリアー",
        "year": 2023,
        "body_type": "SUV（クロスオーバー）",
        "engine_type": "2.5L TNGA アトキンソンサイクル + 電気モーター（ハイブリッド）/ 2.0L ダイナミックフォースエンジン",
        "max_power_ps": 171,
        "fuel_economy_wltc": 22.3,
        "seating_capacity": 5,
        "price_min_man_yen": 299,
        "drivetrain": "FF / E-Four（4WD）",
        "safety_features": "Toyota Safety Sense 2.5+（昼夜・自転車・歩行者検知、緊急時操舵支援）",
        "key_features": "プレミアムSUV。パノラマガラスルーフ設定。静粛性に優れた上質な室内空間。デジタルアウターミラー（Z/PHEV）。JBLサウンドシステム設定",
        "description": "トヨタの上質系SUVの代表格。都市派プレミアムSUVとして高い人気を誇る。2.5Lハイブリッドシステムにより22.3km/Lの低燃費を実現。パノラマルーフや充実した快適装備で、SUVながら高級セダンのような乗り心地を提供する。",
    },
    {
        "manufacturer": "トヨタ",
        "model_name": "アルファード",
        "year": 2023,
        "body_type": "ミニバン（フルサイズ）",
        "engine_type": "2.5L TNGA アトキンソンサイクル + 電気モーター（ハイブリッド）",
        "max_power_ps": 190,
        "fuel_economy_wltc": 19.5,
        "seating_capacity": 7,
        "price_min_man_yen": 520,
        "drivetrain": "FF / E-Four（4WD）",
        "safety_features": "Toyota Safety Sense 3.0（緊急時操舵支援、レーントレーシングアシスト、アドバンストパーク）",
        "key_features": "4代目フルモデルチェンジ。エグゼクティブラウンジシート（後席電動リクライニング）。24インチ大型ディスプレイ。TNGA-K GA-Kプラットフォーム採用。VIP送迎需要にも対応",
        "description": "日本最高級ミニバンの代名詞。2023年に4代目へフルモデルチェンジし、内外装を大幅刷新。2.5Lハイブリッドシステムを搭載し19.5km/Lを達成。エグゼクティブラウンジシートによる極上の後席空間が魅力。VIP送迎から家族旅行まで幅広いニーズに応える。",
    },
    {
        "manufacturer": "トヨタ",
        "model_name": "ランドクルーザー250",
        "year": 2024,
        "body_type": "SUV（本格オフロード）",
        "engine_type": "2.8L ディーゼルターボ（1GD-FTV）/ 3.5L V6 ガソリンターボ（V35A-FTS）",
        "max_power_ps": 204,
        "fuel_economy_wltc": 11.1,
        "seating_capacity": 7,
        "price_min_man_yen": 520,
        "drivetrain": "4WD（パートタイム）",
        "safety_features": "Toyota Safety Sense（マルチテレインモニター、アンダーフロアビュー、Toyota Safety Sense 2.5）",
        "key_features": "ランクル300の弟分。ラダーフレーム構造。マルチテレインセレクト（5モード）。KDSS（カイネティックダイナミックサスペンションシステム）。E-KDSS設定",
        "description": "ランドクルーザーシリーズの中核を担う本格オフロードSUV。ラダーフレーム構造と高い最低地上高により、悪路走破性は世界最高水準。ディーゼルターボエンジンによるトルクフルな走りと、7人乗りの広大な室内を両立。世界中で信頼される耐久性を誇る。",
    },
    {
        "manufacturer": "トヨタ",
        "model_name": "カローラクロス",
        "year": 2023,
        "body_type": "コンパクトSUV",
        "engine_type": "1.8L アトキンソンサイクル + 電気モーター（ハイブリッド）/ 1.8L ガソリン",
        "max_power_ps": 98,
        "fuel_economy_wltc": 26.2,
        "seating_capacity": 5,
        "price_min_man_yen": 209,
        "drivetrain": "FF / E-Four（4WD）",
        "safety_features": "Toyota Safety Sense 2.0（プリクラッシュセーフティ、レーンディパーチャーアラート、オートマチックハイビーム）",
        "key_features": "カローラシリーズ初のSUVモデル。1.8Lハイブリッドで26.2km/L達成。使い勝手の良いラゲッジスペース（487L）。後席スライド機構。Toyota Safety Sense標準装備",
        "description": "世界的人気を誇るカローラをベースにしたコンパクトSUV。1.8Lハイブリッドシステムにより26.2km/Lの優れた燃費を実現。5ナンバーサイズのコンパクトなボディながら、SUVらしい高い視点と487Lの大容量ラゲッジを両立。日常使いからアウトドアまで幅広く対応。",
    },

    # ===== Honda =====
    {
        "manufacturer": "ホンダ",
        "model_name": "フィット",
        "year": 2023,
        "body_type": "コンパクトカー（5ドアハッチバック）",
        "engine_type": "1.5L DOHC i-VTEC + 2モーター（e:HEV）/ 1.3L SOHC ガソリン",
        "max_power_ps": 98,
        "fuel_economy_wltc": 31.0,
        "seating_capacity": 5,
        "price_min_man_yen": 165,
        "drivetrain": "FF / 4WD",
        "safety_features": "Honda SENSING（衝突軽減ブレーキ、誤発進抑制機能、車線維持支援システム、アダプティブクルーズコントロール）",
        "key_features": "センタータンクレイアウトによる広い室内空間。後席シートアレンジ6パターン。e:HEVで31.0km/L達成。5つの個性的なグレード展開（BASIC/HOME/NESS/CROSSTAR/LUXE）",
        "description": "ホンダの定番コンパクトカー。センタータンクレイアウトにより、クラストップレベルの室内空間と多彩なシートアレンジを実現。e:HEVシステムにより31.0km/Lの低燃費を達成。5つのグレード展開で多様なライフスタイルに対応する。",
    },
    {
        "manufacturer": "ホンダ",
        "model_name": "ヴェゼル",
        "year": 2023,
        "body_type": "コンパクトSUV",
        "engine_type": "1.5L DOHC i-VTEC + 2モーター（e:HEV）/ 1.5L DOHC ガソリン",
        "max_power_ps": 131,
        "fuel_economy_wltc": 26.0,
        "seating_capacity": 5,
        "price_min_man_yen": 232,
        "drivetrain": "FF / 4WD（リアルタイムAWD）",
        "safety_features": "Honda SENSING（CMBS、誤発進抑制、車線維持、標識認識、後方誤発進抑制）",
        "key_features": "クーペスタイルのSUVデザイン。e:HEVシステムで26.0km/L。低重心スポーティフォルム。PLaY（パノラマサンルーフ、大型ディスプレイ）グレード設定。後席サンシェード標準",
        "description": "ホンダの主力コンパクトSUV。2代目はクーペスタイルの洗練されたデザインに刷新。1.5L e:HEVシステムにより26.0km/Lの優れた燃費を実現。スポーティな外観と室内の使い勝手を高次元で両立。Honda SENSING標準装備で安全性も充実。",
    },
    {
        "manufacturer": "ホンダ",
        "model_name": "ステップワゴン",
        "year": 2023,
        "body_type": "ミニバン",
        "engine_type": "1.5L DOHC i-VTEC + 2モーター（e:HEV）/ 1.5L DOHC VTECターボ",
        "max_power_ps": 150,
        "fuel_economy_wltc": 20.0,
        "seating_capacity": 8,
        "price_min_man_yen": 299,
        "drivetrain": "FF / 4WD",
        "safety_features": "Honda SENSING（全グレード標準）、後方誤発進抑制機能、後退出庫サポート",
        "key_features": "わくわくゲート（横開き+後ろ跳ね上げ式）リアゲート。AIR仕様（ルーフ高確保）とSPADA（スポーティ）の2系統。3列目シート床下格納。e:HEVで20.0km/L",
        "description": "ホンダの人気ファミリーミニバン。6代目は独自のわくわくゲートを採用し、子供の乗り降りや荷物の積み下ろしを大幅に改善。1.5L e:HEVシステムにより20.0km/Lを達成。3列8人乗りの広大な室内と高い積載性で、ファミリーの多様なニーズに対応する。",
    },
    {
        "manufacturer": "ホンダ",
        "model_name": "シビック",
        "year": 2023,
        "body_type": "セダン / ハッチバック",
        "engine_type": "1.5L DOHC VTECターボ / 2.0L DOHC i-VTEC + 2モーター（e:HEV）",
        "max_power_ps": 182,
        "fuel_economy_wltc": 18.5,
        "seating_capacity": 5,
        "price_min_man_yen": 299,
        "drivetrain": "FF",
        "safety_features": "Honda SENSING（全グレード標準）、BSI（後側方接近車両警報）、後退出庫サポート",
        "key_features": "11代目グローバルモデル。1.5Lターボで182PS/240Nm。e:HEVで高燃費と高出力を両立。Type R（330PS）設定。欧州仕込みのハンドリング性能。6速MT設定（Type R）",
        "description": "ホンダのグローバルモデルとして世界中で販売されるスポーティセダン/ハッチバック。11代目は欧州車に匹敵する高品質感と走行性能を実現。1.5Lターボで182PSを発揮し、e:HEVモデルは低燃費と爽快な走りを両立。スポーツ性と日常使いの使い勝手を高水準でまとめた一台。",
    },
    {
        "manufacturer": "ホンダ",
        "model_name": "フリード",
        "year": 2024,
        "body_type": "コンパクトミニバン",
        "engine_type": "1.5L DOHC i-VTEC + 2モーター（e:HEV）/ 1.5L DOHC ガソリン",
        "max_power_ps": 106,
        "fuel_economy_wltc": 27.0,
        "seating_capacity": 7,
        "price_min_man_yen": 209,
        "drivetrain": "FF / 4WD",
        "safety_features": "Honda SENSING 360（全方位Honda SENSING、Honda CycleDetection）全グレード標準",
        "key_features": "3代目フルモデルチェンジ。Honda SENSING 360を初採用。CROSSTAR（アウトドア仕様）追加。両側電動スライドドア。e:HEVで27.0km/L達成。コンパクトサイズに7人乗り",
        "description": "コンパクトなボディに7人乗りを実現したホンダの人気ミニバン。2024年の3代目では進化したHonda SENSING 360を全グレードに標準装備。1.5L e:HEVにより27.0km/Lの低燃費を達成。両側電動スライドドアと使いやすい室内レイアウトで、ファミリー層から高い支持を得る。",
    },

    # ===== Subaru =====
    {
        "manufacturer": "スバル",
        "model_name": "フォレスター",
        "year": 2023,
        "body_type": "SUV",
        "engine_type": "2.5L BOXER（水平対向4気筒NA）/ 2.0L BOXER + モーター（e-BOXER）",
        "max_power_ps": 184,
        "fuel_economy_wltc": 14.0,
        "seating_capacity": 5,
        "price_min_man_yen": 280,
        "drivetrain": "AWD（対称型AWD・全車）",
        "safety_features": "EyeSight（ツーリングアシスト、プリクラッシュブレーキ）、後退時自動ブレーキ、SRH（ステアリング連動ヘッドライト）",
        "key_features": "全車対称型フルタイムAWD。最低地上高220mm。e-BOXERマイルドハイブリッド設定。X-MODE（2段切換式）搭載。視界の広いドライバーズシート。撥水シート採用グレードあり",
        "description": "スバルのミドルサイズSUVの主力モデル。全車対称型フルタイムAWDと最低地上高220mmにより、悪路・雪道での走破性は国産SUV屈指。e-BOXERマイルドハイブリッドにより燃費を改善。EyeSightによる先進安全装備と実用的なアウトドア性能を兼ね備える。",
    },
    {
        "manufacturer": "スバル",
        "model_name": "レヴォーグ",
        "year": 2023,
        "body_type": "スポーツワゴン",
        "engine_type": "1.8L BOXER DOHCターボ（CB18型・直噴）",
        "max_power_ps": 177,
        "fuel_economy_wltc": 14.0,
        "seating_capacity": 5,
        "price_min_man_yen": 329,
        "drivetrain": "AWD（対称型AWD・全車）",
        "safety_features": "EyeSight X（AI搭載・世界初）、ツーリングアシスト、前後誤発進抑制、高速道路同一車線自動運転技術",
        "key_features": "SGP（スバルグローバルプラットフォーム）採用。世界初EyeSight X（AI×地図情報×EyeSight）。1.8Lターボで177PS/300Nm。スポーツワゴンのスタンダードとして高評価。STIスポーツ#設定",
        "description": "スバルのスポーツワゴンの旗艦モデル。2代目は新開発1.8Lターボエンジンと世界初のEyeSight Xを搭載。AIと地図情報を組み合わせた高度な運転支援を実現。SGPの採用により優れた操縦安定性と快適な乗り心地を両立。全車AWDでスポーティな走りと実用性を高次元で融合。",
    },
    {
        "manufacturer": "スバル",
        "model_name": "アウトバック",
        "year": 2023,
        "body_type": "SUVワゴン（クロスオーバー）",
        "engine_type": "2.5L BOXER（水平対向4気筒NA・直噴）",
        "max_power_ps": 175,
        "fuel_economy_wltc": 13.2,
        "seating_capacity": 5,
        "price_min_man_yen": 399,
        "drivetrain": "AWD（対称型AWD・全車）",
        "safety_features": "EyeSight（ツーリングアシスト）、後退時自動ブレーキ、BSM（後側方警戒支援）、RCTA",
        "key_features": "最低地上高213mm（国産ワゴン最高クラス）。大容量ラゲッジ（522L）。ルーフレール標準装備。X-MODE搭載。エアロルーフレール設定。革シート設定",
        "description": "スバルのアウトドア派向けクロスオーバーSUVワゴン。最低地上高213mmはワゴンクラス最高水準で、SUVに匹敵する悪路走破性を誇る。2.5L BOXERエンジン搭載の全車AWDで、どんな路面でも安定した走りを提供。522Lの大容量ラゲッジとルーフレールでアウトドアにも最適。",
    },
    {
        "manufacturer": "スバル",
        "model_name": "インプレッサ",
        "year": 2023,
        "body_type": "5ドアハッチバック",
        "engine_type": "2.0L BOXER（水平対向4気筒NA・直噴 FB20型）",
        "max_power_ps": 154,
        "fuel_economy_wltc": 17.0,
        "seating_capacity": 5,
        "price_min_man_yen": 259,
        "drivetrain": "AWD（対称型AWD・全車）",
        "safety_features": "EyeSight（全グレード標準）、後退時自動ブレーキ、SRH（ステアリング連動ヘッドライト）",
        "key_features": "6代目（GU型）新世代スバルデザイン採用。SGPプラットフォーム。全車AWD・全車EyeSight標準。新型2.0L直噴エンジン搭載。スバルの入門モデルとして高品質を実現",
        "description": "スバルのコンパクトハッチバックの主力モデル。6代目は新世代スバルデザインを採用し、スポーティで洗練された外観に刷新。新開発2.0L直噴BOXERエンジンと対称型フルタイムAWDを全車標準装備。EyeSightも全グレード標準で、安全性と走りの質感を高次元でまとめたモデル。",
    },
    {
        "manufacturer": "スバル",
        "model_name": "WRX S4",
        "year": 2023,
        "body_type": "スポーツセダン",
        "engine_type": "2.4L BOXER DOHCターボ（FA24F型・直噴）",
        "max_power_ps": 275,
        "fuel_economy_wltc": 12.4,
        "seating_capacity": 5,
        "price_min_man_yen": 445,
        "drivetrain": "AWD（対称型AWD・全車）",
        "safety_features": "EyeSight X、BSM（後側方警戒支援）、後退時自動ブレーキ、フロント&リアビューモニター",
        "key_features": "2.4Lターボで275PS/375Nm。Sport Lineartronic（スポーツCVT）。SI-DRIVE（3モード）。VAB型WRX STIの後継ポジション。EyeSight X搭載。18インチアルミ標準",
        "description": "スバルのハイパフォーマンスセダン。2.4Lターボは275PS・375Nmの強力なスペックを誇り、全車対称型AWDと組み合わせて圧倒的な走行性能を実現。EyeSight Xによる高度な運転支援も搭載し、スポーツ性と日常使いの快適性を両立。スバルのスポーツモデルのフラッグシップ的存在。",
    },
]


def setup():
    conn = psycopg2.connect(DB_URL)
    with conn.cursor() as cur:
        # テーブル作成
        cur.execute("""
            CREATE TABLE IF NOT EXISTS car_catalog (
                id                  SERIAL PRIMARY KEY,
                manufacturer        VARCHAR(50)   NOT NULL,
                model_name          VARCHAR(100)  NOT NULL,
                year                INTEGER,
                body_type           VARCHAR(100),
                engine_type         TEXT,
                max_power_ps        INTEGER,
                fuel_economy_wltc   FLOAT,
                seating_capacity    INTEGER,
                price_min_man_yen   INTEGER,
                drivetrain          VARCHAR(50),
                safety_features     TEXT,
                key_features        TEXT,
                description         TEXT,
                UNIQUE (manufacturer, model_name)
            )
        """)

        # データ投入（既存レコードは上書き）
        for car in CAR_DATA:
            cur.execute("""
                INSERT INTO car_catalog
                    (manufacturer, model_name, year, body_type, engine_type,
                     max_power_ps, fuel_economy_wltc, seating_capacity,
                     price_min_man_yen, drivetrain, safety_features, key_features, description)
                VALUES
                    (%(manufacturer)s, %(model_name)s, %(year)s, %(body_type)s, %(engine_type)s,
                     %(max_power_ps)s, %(fuel_economy_wltc)s, %(seating_capacity)s,
                     %(price_min_man_yen)s, %(drivetrain)s, %(safety_features)s, %(key_features)s, %(description)s)
                ON CONFLICT (manufacturer, model_name) DO UPDATE SET
                    year               = EXCLUDED.year,
                    body_type          = EXCLUDED.body_type,
                    engine_type        = EXCLUDED.engine_type,
                    max_power_ps       = EXCLUDED.max_power_ps,
                    fuel_economy_wltc  = EXCLUDED.fuel_economy_wltc,
                    seating_capacity   = EXCLUDED.seating_capacity,
                    price_min_man_yen  = EXCLUDED.price_min_man_yen,
                    drivetrain         = EXCLUDED.drivetrain,
                    safety_features    = EXCLUDED.safety_features,
                    key_features       = EXCLUDED.key_features,
                    description        = EXCLUDED.description
            """, car)
            print(f"  投入: {car['manufacturer']} {car['model_name']}")

    conn.commit()
    conn.close()
    print(f"\n✓ {len(CAR_DATA)} 車種のデータを投入しました。")


if __name__ == "__main__":
    setup()
