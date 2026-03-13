
---
name: sku-code-generator
description: 为电商货盘产品生成标准化 SKU 编码，并同步上传至 Supabase sku_cost 表和飞书在线表格
---

# SKU 编码生成器

## 触发条件
用户提及「生成SKU」、「SKU编码」、「货盘编码」、「产品编码」时触发本技能。

---

## SKU 格式规则

```
<CATEGORY>-<PRODUCT_ABBR>-<3_DIGIT_RANDOM>
示例：K-PCM-683
```

### 分类代码（Category Codes）

| 代码 | 分类 | 典型产品关键词 |
|------|------|--------------|
| K | Kitchen 厨房 | 咖啡机、锅、水壶、烤箱、餐具、料理机 |
| B | Beauty/Bathroom 美妆浴室 | 护肤、化妆、沐浴、洗漱、美容仪、香水 |
| P | Personal Care 个人护理 | 牙刷、按摩仪、剃须、脱毛仪、吹风机 |
| H | Home 家居 | 收纳、清洁、床品、窗帘、摆件、扫地机 |
| G | Garment Care 衣物护理 | 洗衣、熨烫、衣架、烘干、蒸汽挂烫 |
| L | Lighting 照明 | 台灯、射灯、灯带、夜灯、氛围灯 |
| S | Stationery 文具办公 | 笔、本子、打印机、便利贴、文具套装 |
| A | Apparel 服装配饰 | 衣服、裤子、裙子、鞋、包、帽子、手链 |

> **注意**：上表关键词仅供参考，Claude 应优先使用语义理解进行分类判断，而非严格依赖关键词匹配。

---

## 类目不在已知范围时的处理策略

当产品不属于上述任何类目时，按以下优先级处理：

### 1. 语义靠近原则
先尝试从语义角度归并到最相近的现有类目。例如：
- 「音箱、耳机」→ 可考虑 H（Home）或新建 E（Electronics）
- 「宠物用品」→ 无近似类目，应新建
- 「运动器材」→ 无近似类目，应新建

### 2. 新建类目字母规则
若确需新建，遵循以下规则：
- **选取直觉性强的首字母**，如 E=Electronics、T=Toys、O=Outdoor、F=Food、M=Maternal & Baby、Z=Others
- **字母不得与现有类目冲突**（已占用：K/B/P/H/G/L/S/A）
- **向用户确认后方可使用**，并在本文件的分类表中追加记录

### 3. 缩写字母与类目代码的关系
两者完全独立，互不影响：
```
K - PCM - 683
↑    ↑     ↑
类目  缩写  随机码
```
- 类目代码 = 表示产品所属大类，**单一字母**
- 产品缩写 = 取自产品英文名，**2-4位**，与类目字母无关
- 缩写首字母即使恰好与某类目代码相同（如 P-PS-042），也不会产生歧义

---

## 工作流程

### 第一步：收集产品信息
使用模板询问：
```
产品名称（中文）：
产品名称（英文，可选）：
成本价（cost_price）：
运费（shipping_cost，默认0）：
平台费（platform_fee，默认0）：
销售区域（region，默认1）：
生效日期（effective_from，默认今天）：
截止日期（effective_to，可选）：
```

### 第二步：推断分类与缩写
1. 根据语义判断 CATEGORY 代码（参照分类表）
2. 从英文名生成 2-4 位大写缩写（PRODUCT_ABBR）
3. 若类目不在已知范围，提出新类目方案并询问用户确认
4. 向用户展示推断结果，确认后继续

### 第三步：执行生成脚本
```bash
python scripts/generate_sku.py \
  --product "产品中文名" \
  --product-en "Product English Name" \
  --category <CODE> \
  --abbr <ABBR> \
  --cost-price 25.00 \
  --shipping-cost 3.50 \
  --platform-fee 1.20 \
  --region 1 \
  --effective-from 2025-01-01
```

脚本将自动：
1. 查询 `sku_cost` 表中已有 `sku_id`，确保编码不重复
2. 生成唯一 SKU
3. 插入记录到 Supabase `sku_cost` 表
4. 追加行至飞书在线表格
5. 输出 JSON 结果

### 第四步：呈现结果
```
✅ SKU 生成成功

推荐 SKU：K-PCM-683
─────────────────────────────
K   = Kitchen（厨房类）
PCM = Portable Coffee Machine
683 = 三位随机编号

成本信息：
成本价    ¥25.00
运费      ¥3.50
平台费    ¥1.20
生效日期  2025-01-01

同步状态：
Supabase sku_cost 表 ✅ 已上传
飞书表格             ✅ 已追加
```

---

## 飞书表格列顺序

飞书表格应设置以下表头（第1行），列顺序固定：

| A | B | C | D | E | F | G | H | I | J | K | L |
|---|---|---|---|---|---|---|---|---|---|---|---|
| sku_id | sku_name | category | category_name | abbr | cost_price | shipping_cost | platform_fee | region | effective_from | effective_to | created_at |

---

## 环境配置

在项目根目录创建 `.env`（参考 `.env.example`）：

```env
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=your-anon-key

FEISHU_APP_ID=cli_xxx
FEISHU_APP_SECRET=xxx
FEISHU_SPREADSHEET_TOKEN=shtcnXXXXXXXXXX
FEISHU_SHEET_ID=Sheet1
```

未配置时脚本仍可本地生成 SKU，上传步骤跳过并在 JSON 中标注 `not_configured`。
