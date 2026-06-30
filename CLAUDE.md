# CLAUDE.md

本文件为 AI Agent 在本仓库中处理代码时提供指导。

## 关于本仓库

yt-dlp 是一个功能丰富的命令行音视频下载器。仅支持 Python **3.10+**（CPython 和 PyPy），并且没有强制运行时依赖；可选 extras 会被打包进发布 wheel。本仓库是一个**下游 fork**，会定期从 `upstream`（yt-dlp/yt-dlp）合并，并携带少量本地新增内容（见 [Fork-specific additions](#fork-specific-additions-not-in-upstream-yt-dlp)）。阅读代码时请记住这些新增内容；从 upstream 同步时，也应预期这些位置会出现合并冲突。

## 开发工作流

[`hatch`](https://hatch.pypa.io)（≥1.10.0）是标准入口；它使用 `uv` 在 `.venv` 下创建环境。

- `hatch run setup`：安装 pre-commit hook（每次提交前自动运行 `hatch fmt`）。
- `hatch run yt-dlp -- <args>`：以 `python -Werror -Xdev -m yt_dlp` 运行本地包。
- `hatch shell`：进入已安装开发依赖的 venv。
- `hatch fmt`：应用 ruff + autopep8 修复（只检查时使用 `hatch fmt --check`）。
- `hatch test`：`devscripts/run_tests.py` 的包装器；语义见 [Running tests](#running-tests)。

不使用 hatch 时（完整命令列表见 `CONTRIBUTING.md` → “DEVELOPER INSTRUCTIONS”）：`python -m devscripts.install_deps --include-group dev`、`python -m devscripts.run_tests`、`ruff check --fix . && autopep8 --in-place .`。

`Makefile` 目标用于发布产物（`make all` = lazy extractors + zipapp + docs + pypi-files）以及直接 pytest 路径（`make test`、`make offlinetest`、`make codetest`）。

## 运行测试

使用 pytest，文件为 `test/test_*.py`。测试套件使用 **`-Werror`（警告视为错误）**、`strict_markers`、`strict_config`。唯一的自定义 marker 是 `download`（需要网络）。

- 离线/核心测试集：`make offlinetest` → `pytest -Werror -m "not download"`。（`hatch test core` 通过包装器执行相同操作。）
- 包含网络的完整测试集：`make test`。
- 单个文件：`python -m pytest -Werror test/test_utils.py`。
- 单个测试：`python -m pytest -Werror "test/test_download.py::TestDownload::test_Youtube"`。

除非设置了 `CI` 或传入 `--flaky`，`devscripts/run_tests.py` 会自动添加 `--disallow-flaky`。Networking handler 测试会通过 `handler` fixture 以及 `test/conftest.py` 中的 marker（`skip_handler`、`handler_flaky` 等），在已安装的 request handler 上参数化运行。

### 提取器测试

每个提取器都在类级别声明 `_TESTS`（dict 列表）；`test/test_download.py::TestDownload::test_<Name>` 会运行它们。`hatch test` 包装器会展开提取器名称：

- `hatch test YourExtractor` → `test_download.py::TestDownload::test_YourExtractor`
- `hatch test YourExtractor_all` → 该提取器的每个测试。额外测试命名为 `_1`、`_2` 等；带有 `only_matching` 的条目不计入数量。

需要登录的提取器从 `test/local_parameters.json` 读取凭据（`usenetrc`、`username`/`password`、`cookiefile`/`cookiesfrombrowser`）。见 `test/helper.py`。

## 代码风格（ruff + autopep8，配置在 `pyproject.toml`）

容易踩坑的点：

- 120 列行宽限制。内联和多行字符串使用**单引号**，docstring 使用**双引号**。`avoid-escape=false`，因此不要为了转义字符而切换引号。
- `flake8-import-conventions` 禁止对许多标准库模块使用 `from os ...`、`from re ...`、`from json ...` 等导入形式（完整列表在 `[tool.ruff.lint.flake8-import-conventions]` 下）；应导入模块并使用限定名。
- 多个旧的 `yt_dlp.compat.*` / `yt_dlp.utils.*` 辅助工具被禁用：使用 `str` 而不是 `compat_str`，使用 `urllib.parse` 而不是 `compat_urlparse`，使用 `jwt_encode` 而不是 `jwt_encode_hs256` 等。（完整表格在 `[tool.ruff.lint.flake8-tidy-imports.banned-api]`。）
- 不要用 `# noqa` 抑制 linter 规则；唯一认可的例外是在 GraphQL 查询模板内为 printf 风格格式化使用 `UP031`。

### yt-dlp 编码约定（提取器代码）

完整指南见 `CONTRIBUTING.md` → “yt-dlp coding conventions”；关键规则如下：

- **info dict 中唯一强制字段是 `id` 和（`url` | `formats`）。** 其他所有字段都必须以**非致命**方式提取：使用 `traverse_obj`、`dict.get`、`*_or_none` 辅助函数以及 `fatal=False`。对于色情网站，`age_limit` 也是强制字段。
- **Regex**：不要捕获不用的分组（使用 `(?:...)`）；保持模式宽松，避免上游标记的小改动破坏提取；在重要位置选择正确的量词，而不是贪婪的 `.*`。
- 优先使用 `traverse_obj` 和 `InfoExtractor` 辅助方法（`_html_search_regex`、`_search_regex`、`_og_search_*`、`_download_json`、`_match_id`），不要手写解析。提供 fallback，并将它们**折叠**起来（在一次 `traverse_obj` 调用中使用多个路径），而不是写冗长的 try/except 链。

## 架构

### 下载流水线

`YoutubeDL`（`yt_dlp/YoutubeDL.py`，约 5000 行）是编排器，也是所有嵌入场景使用的对象。一次运行流程如下：

1. `download(url_list)` → `extract_info(url)` 选择匹配的 `InfoExtractor` 并调用 `ie._real_extract(url)`，后者返回一个 **info dict**，这是核心数据结构，文档位于 `yt_dlp/extractor/common.py`（约 L119-L440）。
2. `process_video_result` / `process_info` 解析并排序 formats（`FormatSorter`），然后将选定的 format 交给某个**下载器**（`yt_dlp/downloader/`）。
3. **Post-processors**（`yt_dlp/postprocessor/`，主要基于 FFmpeg）围绕下载过程运行，包括音频提取、字幕嵌入、元数据、SponsorBlock 等。

### 提取器 — `yt_dlp/extractor/`（约 1000 个模块；代码库主体）

- 全部继承自 `extractor/common.py` 中的 `InfoExtractor`，后者提供 `_download_webpage`、`_download_json`、`_html_search_regex`、`_og_search_*`、`_match_id` 等。
- **注册**：类名以 `IE` 结尾，并且必须导入到 `yt_dlp/extractor/_extractors.py` 中；按字母顺序，分组使用括号导入，且**组内最后一个 import 需要尾随逗号**。这是 `list_extractor_classes()` 扫描的索引；`supportedsites.md` 由它生成（`make supportedsites`）。
- `yt_dlp/extractor/lazy_extractors.py` 由 `devscripts/make_lazy_extractors.py` **生成**（`make lazy-extractors`）；不要手动编辑。

### 网络 — `yt_dlp/networking/`

`RequestDirector` 位于可插拔的 `RequestHandler` 前端，每个 handler 是不同的传输实现：`_urllib`（标准库，始终可用）、`_requests`（requests）、`_websockets`、`_curlcffi`（浏览器伪装，`curl-cffi` extra）。Handler 注册到 `_REQUEST_HANDLERS`，并在运行时被选择和配置；`ImpersonateTarget` 驱动伪装请求。conftest 中的 `handler` fixture 会在已安装的 handler 上参数化 networking 测试。

### 其他核心部分

- `yt_dlp/utils/`：`_utils.py`（大型辅助函数集合）、`traversal.py`（`traverse_obj`，首选的安全提取原语）、`_jsruntime.py`（外部 JS 运行时：node/deno/bun/quickjs），以及 `_legacy.py`/`_deprecated.py`。
- `yt_dlp/jsinterp.py`：内部 JS 解释器，主要用于 YouTube signature/n-challenge 求解；`yt_dlp/aes.py` 是相关加密实现。
- `yt_dlp/options.py`：基于 optparse 的 CLI 解析；`devscripts/cli_to_api.py` 将 CLI flags 转换为 `YoutubeDL` params。
- `yt_dlp/plugins.py`：运行时插件加载（用户/插件提取器、post-processors、overrides）。
- `yt_dlp/cookies.py`、`cache.py`、`update.py`、`socks.py`、`webvtt.py`。

## Fork-specific additions（不在 upstream yt-dlp 中）

这些内容是本 fork 本地特有的，也是最容易造成困惑的地方：

- **`yt_dlp/third_api/`**：fallback 层，在原生提取器无法解析视频时调用第三方 RapidAPI / 聚合服务（Snap、AllIn-One、ZM、YouTube、Instagram Hiker）。它在核心流水线中有两处接入：
  - `InfoExtractor._extract_use_third_mutil_api`（`extractor/common.py` 约 L4556）→ `MutilThirdIE(self).extract_video_info(...)`。
  - `YoutubeDL.extract_info_use_thirdapi`（`YoutubeDL.py` 约 L4971），它通过 `smuggle_url` 将 `__third_api__` / `__force_third_api__` / `__video_id__` 塞入 URL（由 `third_api/allapi.py:parse_api` 解析）。`ThirdApiGuard` 会对这些调用做限速。
- **`yt_dlp/potoken/`**：PO-token 生成胶水代码。
- **仓库根目录维护脚本**（`merge_upstream.bat`、`debug.py`、`debug/`、`pr_*.py`、`deno_damage.sh`、`pull_requests.json`、 `win*.bat`）是个人 triage / upstream 同步工具；不属于发布包，也不会由测试套件覆盖。

从 `upstream` 合并时，预期正是在这些自定义区域出现冲突：`extractor/common.py` 中的 `third_api` import 和 `_extract_use_third_mutil_api`，以及 `YoutubeDL.py` 中的 `extract_info_use_thirdapi` 代码块。

