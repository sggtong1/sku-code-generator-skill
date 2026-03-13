
# SKU Code Generator Skill

为电商货盘产品生成标准化 SKU 编码，并自动同步至 Supabase 数据库和飞书在线表格。

## 安装

**Workspace 级别**
```
skills/sku-code-generator-skill/
```

**User 级别**
```
~/.claude/skills/sku-code-generator-skill/
```

安装后重启 Claude Code 生效。

---

## 依赖安装

```bash
pip install -r requirements.txt
```

---

## 环境配置

复制 `.env.example` 为 `.env` 并填入配置：

```bash
cp .env.example .env
```

### Supabase 配置

1. 登录 [Supabase](https://supabase.com) 控制台
2. 进入 `Settings > API`，获取 `Project URL` 和 `anon public key`
3. 在 SQL Editor 创建表：

```sql
CREATE TABLE sku_codes (
    id          BIGSERIAL PRIMARY KEY,
    sku         TEXT UNIQUE NOT NULL,
    product_name     TEXT,
    product_name_en  TEXT,
    category         TEXT,
    category_name    TEXT,
    abbreviation     TEXT,
    created_at       TIMESTAMPTZ DEFAULT NOW()
);
```

### 飞书表格配置

1. 在 [飞书开放平台](https://open.feishu.cn) 创建企业自建应用
2. 开启权限：`云文档 > 电子表格 > 读写权限`
3. 将应用添加至目标表格的协作者
4. 从表格 URL 中获取 `spreadsheetToken`
5. 在表格第一行添加表头（可选）：
   ```
   SKU | 产品名称 | 英文名 | 分类代码 | 分类名称 | 缩写 | 生成时间
   ```

---

## 直接调用脚本

```bash
# 完整参数
python scripts/generate_sku.py \
  --product "便携咖啡机" \
  --product-en "Portable Coffee Machine" \
  --category K \
  --abbr PCM

# 仅生成，不上传
python scripts/generate_sku.py \
  --product "便携咖啡机" \
  --product-en "Portable Coffee Machine" \
  --no-upload
```

输出为 JSON 格式，包含 SKU 编码和上传状态。

---

## SKU 格式

```
<CATEGORY>-<PRODUCT_ABBR>-<3_DIGIT_RANDOM>
示例：K-PCM-683
```

| 代码 | 分类 |
|------|------|
| K | Kitchen 厨房 |
| B | Beauty/Bathroom 美妆浴室 |
| P | Personal Care 个人护理 |
| H | Home 家居 |
| G | Garment Care 衣物护理 |
| L | Lighting 照明 |
| S | Stationery 文具办公 |
| A | Apparel 服装配饰 |
