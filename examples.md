
# SKU 生成示例

## 示例 1：便携咖啡机（已知类目）

```bash
python scripts/generate_sku.py \
  --product "便携咖啡机" \
  --product-en "Portable Coffee Machine" \
  --category K \
  --abbr PCM \
  --cost-price 45.00 \
  --shipping-cost 5.00 \
  --platform-fee 2.00 \
  --region 1 \
  --effective-from 2025-01-01
```

输出：
```json
{
  "sku": "K-PCM-683",
  "product": "便携咖啡机",
  "product_en": "Portable Coffee Machine",
  "category": "K",
  "category_name": "Kitchen",
  "abbr": "PCM",
  "cost_price": 45.0,
  "region": 1,
  "shipping_cost": 5.0,
  "platform_fee": 2.0,
  "effective_from": "2025-01-01",
  "effective_to": null,
  "supabase": "success",
  "feishu": "success",
  "error": null
}
```

---

## 示例 2：蓝牙音箱（扩展类目 E=Electronics）

产品「蓝牙音箱」不在已知8个类目，Claude 推断应新建 E=Electronics：

```bash
python scripts/generate_sku.py \
  --product "蓝牙音箱" \
  --product-en "Bluetooth Speaker" \
  --category E \
  --abbr BTS \
  --cost-price 38.00 \
  --region 1
```

输出 SKU：`E-BTS-217`

> 使用新类目后，需在 SKILL.md 的分类表中追加：
> `E | Electronics 电子产品 | 音箱、耳机、充电器、数据线`

---

## 示例 3：缩写首字母恰好等于某类目代码

产品「便携扬声器 Portable Speaker」缩写为 PS，类目为 E：

```bash
python scripts/generate_sku.py \
  --product "便携扬声器" \
  --product-en "Portable Speaker" \
  --category E \
  --abbr PS \
  --cost-price 29.00
```

输出 SKU：`E-PS-104`

> P 是 Personal Care 的类目代码，但这里 PS 是缩写（2位），
> 不会与类目 P 混淆，因为格式明确：`<1位类目>-<缩写>-<3位数字>`。

---

## 示例 4：仅本地生成，不上传

```bash
python scripts/generate_sku.py \
  --product "牙刷架" \
  --product-en "Toothbrush Holder" \
  --category B \
  --abbr TBH \
  --no-upload
```
