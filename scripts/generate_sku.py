
import argparse
import json
import os
import random
import sys
from datetime import date, datetime

# ---------------------------------------------------------------------------
# Category definitions  (可按需扩展)
# ---------------------------------------------------------------------------
CATEGORIES = {
    "K": "Kitchen",
    "B": "Beauty / Bathroom",
    "P": "Personal Care",
    "H": "Home",
    "G": "Garment Care",
    "L": "Lighting",
    "S": "Stationery",
    "A": "Apparel",
    # 扩展示例（Claude 推断后可添加）：
    # "E": "Electronics",
    # "T": "Toys & Kids",
    # "O": "Outdoor & Sports",
    # "F": "Food & Beverage",
    # "X": "Other",
}

# 关键词仅作辅助参考，主要靠 Claude 语义判断
CATEGORY_KEYWORDS = {
    "K": ["咖啡", "厨房", "锅", "碗", "水壶", "烤箱", "微波炉", "餐具", "厨具", "炒锅", "蒸锅", "料理机"],
    "B": ["美容", "浴室", "洗漱", "化妆", "护肤", "沐浴", "洗发", "美妆", "护肤仪", "洁面", "香水"],
    "P": ["个护", "牙刷", "按摩", "剃须", "护发", "吹风机", "电吹风", "剃毛", "脱毛仪"],
    "H": ["家居", "收纳", "清洁", "床品", "窗帘", "摆件", "家装", "除螨", "扫地机", "拖把"],
    "G": ["洗衣", "熨烫", "衣架", "衣物", "烘干", "蒸汽", "晾衣"],
    "L": ["灯", "照明", "台灯", "射灯", "灯带", "夜灯", "氛围灯", "补光灯", "手电"],
    "S": ["文具", "笔", "本子", "办公", "打印", "便利贴", "订书机", "剪刀"],
    "A": ["服装", "衣服", "裤子", "裙子", "鞋", "包", "帽子", "配饰", "手链", "项链", "袜子"],
}


def detect_category(product_name: str) -> str | None:
    """关键词匹配，仅作辅助。优先使用 Claude 的语义推断结果（通过 --category 传入）。"""
    for cat, keywords in CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if kw in product_name:
                return cat
    return None


def generate_abbr(product_name_en: str) -> str:
    """从英文名生成 2-4 位缩写。"""
    words = [w for w in product_name_en.upper().split() if w.isalpha()]
    if not words:
        return product_name_en.upper()[:4]
    if len(words) >= 3:
        return "".join(w[0] for w in words[:4])
    if len(words) == 2:
        return words[0][:2] + words[1][:2]
    return words[0][:4]


def generate_sku(category: str, abbr: str, existing_skus: set = None) -> str:
    """生成唯一 SKU 编码。"""
    if existing_skus is None:
        existing_skus = set()
    for _ in range(200):
        number = str(random.randint(1, 999)).zfill(3)
        sku = f"{category}-{abbr}-{number}"
        if sku not in existing_skus:
            return sku
    raise RuntimeError("200次尝试内无法生成唯一 SKU，请检查现有记录数量。")


# ---------------------------------------------------------------------------
# Supabase — 对接 sku_cost 表
# ---------------------------------------------------------------------------
def supabase_get_existing_skus(url: str, key: str) -> set:
    """从 sku_cost 表获取已有 sku_id（去重，用于避免重复编码）。"""
    try:
        from supabase import create_client
        client = create_client(url, key)
        result = client.table("sku_cost").select("sku_id").execute()
        return {row["sku_id"] for row in result.data}
    except Exception as e:
        print(f"[Supabase] 获取现有 SKU 失败: {e}", file=sys.stderr)
        return set()


def supabase_upload_sku_cost(url: str, key: str, record: dict) -> bool:
    """插入一条记录到 sku_cost 表。"""
    try:
        from supabase import create_client
        client = create_client(url, key)
        client.table("sku_cost").insert(record).execute()
        return True
    except Exception as e:
        print(f"[Supabase] 上传失败: {e}", file=sys.stderr)
        return False


# ---------------------------------------------------------------------------
# 飞书（Lark）集成
# ---------------------------------------------------------------------------
def feishu_get_token(app_id: str, app_secret: str) -> str | None:
    try:
        import requests
        resp = requests.post(
            "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
            json={"app_id": app_id, "app_secret": app_secret},
            timeout=10,
        )
        data = resp.json()
        if data.get("code") == 0:
            return data["tenant_access_token"]
        print(f"[飞书] 获取 Token 失败: {data}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"[飞书] 网络错误: {e}", file=sys.stderr)
        return None


def feishu_append_row(token: str, spreadsheet_token: str, sheet_id: str, values: list) -> bool:
    try:
        import requests
        url = (
            f"https://open.feishu.cn/open-apis/sheets/v2/spreadsheets"
            f"/{spreadsheet_token}/values_append"
        )
        resp = requests.post(
            url,
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json={"valueRange": {"range": f"{sheet_id}!A:Z", "values": [values]}},
            timeout=10,
        )
        data = resp.json()
        if data.get("code") == 0:
            return True
        print(f"[飞书] 写入表格失败: {data}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"[飞书] 写入错误: {e}", file=sys.stderr)
        return False


# ---------------------------------------------------------------------------
# 工具
# ---------------------------------------------------------------------------
def load_env():
    env_path = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".env"))
    if not os.path.exists(env_path):
        return
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip())


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    load_env()

    parser = argparse.ArgumentParser(description="生成货盘 SKU 编码并同步上传至 sku_cost 表")
    # 产品基本信息
    parser.add_argument("--product", required=True, help="产品名称（sku_name）")
    parser.add_argument("--product-en", default="", help="产品英文名（用于生成缩写）")
    parser.add_argument("--category", default="", help="分类代码，留空则自动推断（优先由 Claude 传入）")
    parser.add_argument("--abbr", default="", help="产品缩写（2-4位大写字母），留空则自动生成")
    # sku_cost 表字段
    parser.add_argument("--cost-price", type=float, default=0.0, help="成本价 cost_price")
    parser.add_argument("--region", type=int, default=1, help="区域 region（默认1）")
    parser.add_argument("--shipping-cost", type=float, default=0.0, help="运费 shipping_cost")
    parser.add_argument("--platform-fee", type=float, default=0.0, help="平台费 platform_fee")
    parser.add_argument("--effective-from", default=str(date.today()), help="生效日期 effective_from（YYYY-MM-DD）")
    parser.add_argument("--effective-to", default=None, help="截止日期 effective_to（YYYY-MM-DD，可选）")
    # 控制选项
    parser.add_argument("--no-upload", action="store_true", help="跳过上传，仅本地生成 SKU")
    args = parser.parse_args()

    result = {
        "sku": None,
        "product": args.product,
        "product_en": args.product_en,
        "category": None,
        "category_name": None,
        "abbr": None,
        "cost_price": args.cost_price,
        "region": args.region,
        "shipping_cost": args.shipping_cost,
        "platform_fee": args.platform_fee,
        "effective_from": args.effective_from,
        "effective_to": args.effective_to,
        "supabase": "skipped",
        "feishu": "skipped",
        "error": None,
    }

    # ── 分类代码 ──────────────────────────────────────────────────────────────
    if args.category:
        category = args.category.upper()
    else:
        category = detect_category(args.product)

    if not category:
        result["error"] = (
            f"无法自动识别分类，请通过 --category 指定。"
            f"当前已知类目：{', '.join(f'{k}={v}' for k, v in CATEGORIES.items())}。"
            f"若产品不属于任何已知类目，可传入新字母（如 E=Electronics），"
            f"并在 SKILL.md 的 CATEGORIES 中添加该定义。"
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        sys.exit(1)

    category_name = CATEGORIES.get(category, f"Custom({category})")
    result["category"] = category
    result["category_name"] = category_name

    # ── 缩写 ──────────────────────────────────────────────────────────────────
    if args.abbr:
        abbr = args.abbr.upper()
    elif args.product_en:
        abbr = generate_abbr(args.product_en)
    else:
        result["error"] = "无法生成缩写，请通过 --abbr 或 --product-en 提供英文名"
        print(json.dumps(result, ensure_ascii=False, indent=2))
        sys.exit(1)

    result["abbr"] = abbr

    # ── 查重（从 sku_cost 获取已有 sku_id）────────────────────────────────────
    supabase_url = os.environ.get("SUPABASE_URL", "")
    supabase_key = os.environ.get("SUPABASE_KEY", "")
    supabase_ready = bool(supabase_url and supabase_key)

    existing_skus: set = set()
    if supabase_ready and not args.no_upload:
        existing_skus = supabase_get_existing_skus(supabase_url, supabase_key)

    # ── 生成 SKU ──────────────────────────────────────────────────────────────
    try:
        sku = generate_sku(category, abbr, existing_skus)
    except RuntimeError as e:
        result["error"] = str(e)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        sys.exit(1)

    result["sku"] = sku

    if args.no_upload:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    now_iso = datetime.utcnow().isoformat()

    # ── Supabase 上传 → sku_cost 表 ───────────────────────────────────────────
    if supabase_ready:
        record = {
            "sku_id": sku,
            "sku_name": args.product,
            "cost_price": args.cost_price,
            "region": args.region,
            "shipping_cost": args.shipping_cost,
            "platform_fee": args.platform_fee,
            "effective_from": args.effective_from,
        }
        if args.effective_to:
            record["effective_to"] = args.effective_to

        ok = supabase_upload_sku_cost(supabase_url, supabase_key, record)
        result["supabase"] = "success" if ok else "failed"
    else:
        result["supabase"] = "not_configured"

    # ── 飞书追加行 ────────────────────────────────────────────────────────────
    feishu_app_id     = os.environ.get("FEISHU_APP_ID", "")
    feishu_app_secret = os.environ.get("FEISHU_APP_SECRET", "")
    feishu_token_id   = os.environ.get("FEISHU_SPREADSHEET_TOKEN", "")
    feishu_sheet_id   = os.environ.get("FEISHU_SHEET_ID", "Sheet1")
    feishu_ready = bool(feishu_app_id and feishu_app_secret and feishu_token_id)

    if feishu_ready:
        token = feishu_get_token(feishu_app_id, feishu_app_secret)
        if token:
            # 列顺序对应飞书表格表头：
            # sku_id | sku_name | category | category_name | abbr |
            # cost_price | shipping_cost | platform_fee | region |
            # effective_from | effective_to | created_at
            row = [
                sku,
                args.product,
                category,
                category_name,
                abbr,
                args.cost_price,
                args.shipping_cost,
                args.platform_fee,
                args.region,
                args.effective_from,
                args.effective_to or "",
                now_iso,
            ]
            ok = feishu_append_row(token, feishu_token_id, feishu_sheet_id, row)
            result["feishu"] = "success" if ok else "failed"
        else:
            result["feishu"] = "auth_failed"
    else:
        result["feishu"] = "not_configured"

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
