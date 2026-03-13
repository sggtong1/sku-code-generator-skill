
---
name: sku-code-generator
description: 为电商货盘产品生成标准化 SKU 编码，并同步上传至 Supabase sku_cost 表和飞书在线表格
---

# SKU 编码生成器

## 触发条件
用户提及「生成SKU」「SKU编码」「货盘编码」「产品编码」，或直接描述产品名称时触发。

---

## 核心原则：直接执行，不要提问

**只有两个字段需要用户提供：产品名称 + 成本价。**
收到这两项后，立刻执行，不得询问英文名、缩写、分类、运费、区域等任何其他字段。

---

## 必填字段（仅这两项）

| 字段 | 说明 |
|------|------|
| 产品名称 | 中文或英文均可，就是用户说的商品名 |
| cost_price | 成本价，纯数字 |

缺少其中一项时，只问缺少的那一项，其他什么都不问。

---

## 工作流程

### 第一步：收到产品名 + 成本价 → 立刻推断并执行脚本

**禁止询问**以下字段，全部自行处理：

| 字段 | 处理规则 |
|------|---------|
| category | 根据产品语义从分类表选一个，自己判断 |
| product_en | 根据产品中文名自行推断英文名 |
| abbr | 从英文名取首字母，2-4位，自己生成 |
| shipping_cost | 固定默认 0.00 |
| platform_fee | 固定默认 0.00 |
| region | 固定默认 1 |
| effective_from | 固定默认今天日期 |
| effective_to | 固定默认空 |

立即运行（`--dry-run` 仅生成不上传）：
```bash
python scripts/generate_sku.py \
  --product "产品名" \
  --cost-price 45.00 \
  --product-en "推断的英文名" \
  --category K \
  --abbr PCM \
  --dry-run
```

### 第二步：展示结果，一句话询问上传

```
SKU：K-PCM-371
产品：便携咖啡机（Portable Coffee Machine）
分类：K = Kitchen ｜ 成本：¥45.00 ｜ 区域：1 ｜ 生效：2025-03-13

确认同步到 Supabase + 飞书吗？(y/n)
```

### 第三步：根据回复执行

- **y / 确认**：去掉 `--dry-run` 重新执行，完成上传
- **用户修正某字段**（如"运费5"）：更新对应参数后执行上传
- **n**：直接返回 SKU，结束

---

## 分类代码

| 代码 | 分类 | 典型产品 |
|------|------|---------|
| K | Kitchen 厨房 | 咖啡机、锅、水壶、烤箱、餐具 |
| B | Beauty/Bathroom 美妆浴室 | 护肤、化妆、沐浴、美容仪 |
| P | Personal Care 个人护理 | 牙刷、按摩仪、剃须、吹风机 |
| H | Home 家居 | 收纳、清洁、床品、扫地机 |
| G | Garment Care 衣物护理 | 洗衣、熨烫、衣架、蒸汽挂烫 |
| L | Lighting 照明 | 台灯、灯带、夜灯、氛围灯 |
| S | Stationery 文具办公 | 笔、本子、打印机、文具 |
| A | Apparel 服装配饰 | 衣服、鞋、包、帽子、首饰 |

若产品不属于以上任何类目，选取直觉性首字母（如 E=Electronics）并在回复中注明，无需额外确认。

---

## 类目与缩写的关系

```
K  -  PCM  -  371
↑     ↑        ↑
类目  缩写    随机码（001-999）
```

类目代码与缩写完全独立，缩写首字母恰好与某类目相同不会产生歧义。

---

## 环境配置

`.env` 文件（参考 `.env.example`）：
```
SUPABASE_URL=...
SUPABASE_KEY=...
FEISHU_APP_ID=...
FEISHU_APP_SECRET=...
FEISHU_SPREADSHEET_TOKEN=...
FEISHU_SHEET_ID=Sheet1
```
未配置时脚本仍可生成 SKU，上传步骤自动跳过（标注 `not_configured`）。
