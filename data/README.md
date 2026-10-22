# data — 共享数据目录

```
data/
├── raw/        原始数据:只读,绝不就地修改
└── processed/   由 raw 生成的数据集,含冻结后的 train/val/test 划分
```

- `raw/` 下按「数据集名称」建子目录,例如 `raw/<数据集名>/images`、`raw/<数据集名>/annotations`
- `processed/` 可再生,可以删掉重来
- 数据内容不进 git(见根目录 `.gitignore`)

> train/val/test 划分在生成 processed 时用固定种子一次性冻结,训练只读这份划分。