
---
name: sku-code-generator
description: 为电商货盘产品生成标准化 SKU 编码，并同步上传至 Supabase sku_cost 表和飞书在线表格
---

# SKU 编码生成器

## 触发条件
用户提及「生成SKU」「SKU编码」「货盘编码」「产品编码」，或直接描述产品名称时触发。

---

## 核心原则

**不问不必要的问题。** 凡是能推断或有默认值的字段，直接处理；只在真正无法确定时才询问。上传前做一次确认即可。

---

## 必填字段

以下两个字段**必须由用户提供**，缺一不可：

| 字段 | 说明 |
|------|------|
| 产品核心词 | 产品名称，中文或英文均可 |
| cost_price | 成本价，数字，单位元 |

若用户未提供其中任何一项，直接询问该字段，不做其他推断。

---

## 工作流程

### 第一步：直接推断，立刻生成

收到产品名称 + 成本价后，其余字段按以下规则自动处理：

| 字段 | 处理方式 |
|------|---------|
| category | 根据产品语义判断（参见分类表） |
| abbr | 根据产品英文名取首字母，2-4位；无英文名则 AI 自行推断 |
| shipping_cost | 默认 0.00 |
| platform_fee | 默认 0.00 |
| region | 默认 1 |
| effective_from | 默认今天 |
| effective_to | 默认空 |

生成命令（`--dry-run` 先不上传）：
```bash
python scripts/generate_sku.py \
  --product "产品名" \
  --cost-price 45.00 \
  --product-en "Product Name" \
  --category K \
  --abbr PCM \
  --dry-run
```

### 第二步：展示结果，询问上传

向用户展示生成结果（紧凑格式）：

```
SKU：K-PCM-371
产品：便携咖啡机（Portable Coffee Machine）
分类：K = Kitchen
成本：¥0.00  运费：¥0.00  平台费：¥0.00
区域：1  生效：2025-03-13

是否同步上传到 Supabase + 飞书？(y/n)
若需修改成本等字段，请一并告知。
```

### 第三步：根据用户回复执行

- **用户直接 y / 确认**：去掉 `--dry-run` 重新执行，完成上传
- **用户提供补充信息**（如"成本35，运费5"）：将字段补入后执行上传
- **用户 n / 不上传**：直接返回 SKU，流程结束

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
