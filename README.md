# QuarkPan Tree Exporter

基于 `quarkpan` / `quark_client` 的夸克网盘目录树导出工具。

它可以读取夸克分享链接或个人网盘目录，递归获取文件夹与文件结构，并将结果打印到终端，同时保存到 `tree.txt`。

`quark_client` 来自 `quarkpan` 包内部，因此只需要安装 `quarkpan`。

## 功能

* 支持夸克网盘分享链接
* 支持个人网盘根目录、目录 ID 或目录路径
* 支持递归获取子目录文件树
* 支持指定分享链接中的子目录 `pdir_fid`
* 支持限制递归深度
* 支持文本树输出和 JSON 输出
* 可通过环境变量或命令行参数传入 Cookie

## 环境要求

* Python 3.12
* `quarkpan`

安装依赖：

```bash
pip install quarkpan
```

## 快速开始

下载 `get_tree.py` 后，在脚本所在目录执行：

```bash
python get_tree.py "https://pan.quark.cn/s/xxxx"
```

运行后会在终端输出目录树，并默认保存到：

```text
tree.txt
```

## 使用示例

### 1. 获取分享链接根目录文件树

```bash
python get_tree.py "https://pan.quark.cn/s/xxxx"
```

### 2. 分享链接带提取码

```bash
python get_tree.py "https://pan.quark.cn/s/xxxx" --password abcd
```

### 3. 获取分享链接中的指定子目录

```bash
python get_tree.py "https://pan.quark.cn/s/xxxx" --pdir-fid 目录fid
```

### 4. 获取个人网盘根目录

```bash
python get_tree.py 0 --source drive
```

### 5. 获取个人网盘指定目录 ID

```bash
python get_tree.py 目录fid --source drive
```

### 6. 获取个人网盘指定路径

```bash
python get_tree.py "/我的文件夹/子目录" --source drive
```

### 7. 输出 JSON

```bash
python get_tree.py "https://pan.quark.cn/s/xxxx" --json
```

### 8. 指定保存路径

```bash
python get_tree.py "https://pan.quark.cn/s/xxxx" --output download/tree.txt
```

### 9. 限制递归深度

```bash
python get_tree.py "https://pan.quark.cn/s/xxxx" --max-depth 2
```

## Cookie 使用

读取公开分享链接通常不需要 Cookie。

如果需要读取个人网盘目录，可以通过参数传入 Cookie：

```bash
python get_tree.py 0 --source drive --cookie "你的夸克Cookie"
```

也可以使用环境变量。

Windows PowerShell：

```powershell
$env:QUARK_COOKIE="你的夸克Cookie"
python get_tree.py 0 --source drive
```

macOS / Linux：

```bash
export QUARK_COOKIE="你的夸克Cookie"
python get_tree.py 0 --source drive
```

## 参数说明

```text
usage: get_tree.py [-h] [--source {auto,share,drive}] [--pdir-fid PDIR_FID] [--password PASSWORD] [--cookie COOKIE] [--page-size PAGE_SIZE] [--max-depth MAX_DEPTH] [--json] [--output OUTPUT] target

Get a Quark Drive folder tree with quarkpan/quark_client.

positional arguments:
  target                Share URL, Quark folder id, or path in your own drive. Use 0 for drive root.

options:
  -h, --help            show this help message and exit
  --source {auto,share,drive}
                        Input type. Default: auto.
  --pdir-fid PDIR_FID   Folder id inside a share URL. Default: 0.
  --password PASSWORD   Share extraction code/password. If omitted, try to parse from URL text.
  --cookie COOKIE       Quark cookie. Defaults to env QUARK_COOKIE.
  --page-size PAGE_SIZE
                        Page size for each API request. Default: 100.
  --max-depth MAX_DEPTH
                        Limit recursion depth. Root children are depth 1. Default: unlimited.
  --json                Output JSON instead of a text tree.
  --output OUTPUT       Save output to this file. Default: tree.txt.
```

## 常用参数

| 参数            | 说明                             | 默认值                 |
| ------------- | ------------------------------ | ------------------- |
| `target`      | 分享链接、个人网盘目录 ID 或路径             | 必填                  |
| `--source`    | 输入来源，可选 `auto`、`share`、`drive` | `auto`              |
| `--pdir-fid`  | 分享链接中的目录 ID                    | `0`                 |
| `--password`  | 分享链接提取码                        | 空                   |
| `--cookie`    | 夸克 Cookie                      | `QUARK_COOKIE` 环境变量 |
| `--page-size` | 每页请求数量                         | `100`               |
| `--max-depth` | 最大递归深度                         | 不限制                 |
| `--json`      | 输出 JSON 格式                     | 关闭                  |
| `--output`    | 保存文件路径                         | `download/tree.txt` |

## 输出示例

```text
abcd1234
|-- 电影/
|   |-- movie-a.mp4
|   `-- movie-b.mp4
|-- 文档/
|   `-- notes.pdf
`-- README.txt
```

## 注意事项

* 本项目只读取目录结构，不下载文件内容。
* 分享链接失效、需要提取码或访问受限时，接口可能返回错误。
* 个人网盘目录需要有效登录状态或 Cookie。
* 请勿将自己的 Cookie 提交到 GitHub。
* 使用前请确保你的行为符合夸克网盘相关服务条款。
