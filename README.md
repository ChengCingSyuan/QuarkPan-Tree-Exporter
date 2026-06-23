# QuarkPan-Tree-Exporter
一个基于 quarkpan / quark_client 的夸克网盘目录树导出工具。支持读取夸克分享链接或个人网盘目录 ID，递归获取文件夹结构，并将结果输出到终端，同时自动保存为 download/tree.txt。

**标题**

QuarkPan Tree Exporter

**介绍**

一个基于 `quarkpan` / `quark_client` 的夸克网盘目录树导出工具。支持读取夸克分享链接或个人网盘目录 ID，递归获取文件夹结构，并将结果输出到终端，同时自动保存为 `download/tree.txt`。

**简短说明**

```markdown
# QuarkPan Tree Exporter

基于 quarkpan 的夸克网盘目录树导出脚本，可递归获取分享链接或个人网盘目录下的文件结构，并保存为文本文件。

## 功能

- 支持夸克分享链接
- 支持个人网盘目录 ID 或路径
- 支持递归获取子目录
- 支持限制最大递归深度
- 支持文本树和 JSON 输出
- 默认保存到 `download/tree.txt`

## 使用方法

```bash
python get_tree.py "https://pan.quark.cn/s/xxxx"
```

带提取码：

```bash
python get_tree.py "https://pan.quark.cn/s/xxxx" --password abcd
```

输出 JSON：

```bash
python get_tree.py "https://pan.quark.cn/s/xxxx" --json
```

指定保存路径：

```bash
python get_tree.py "https://pan.quark.cn/s/xxxx" --output download/tree.txt
```

## 依赖

```bash
pip install quarkpan
```
```
