 # ROMA-01 交易平台配置概览（中文）

 该目录包含 ROMA-01 交易平台的配置文件。

 ## ⚠️ 配置更新

 **平台现已采用“账户中心化配置”**——所有配置集中存放在 `trading_config.yaml` 中。  
 详细说明请参阅 **[README_CONFIG.zh-CN.md](README_CONFIG.zh-CN.md)**。

 ## 快速开始

 1. 编辑 `trading_config.yaml`，填写账户 / 模型 / 智能体信息  
 2. 在 `.env` 文件中设置环境变量  
 3. 启动平台

 更详细的操作指南请参考 **[QUICK_START.md](QUICK_START.md)**。

 ## 目录结构

 ```
 config/
 ├── README.md / README.zh-CN.md              # 当前文件（英文 / 中文，保留旧文档）
 ├── README_CONFIG.md / README_CONFIG.zh-CN.md# 新版配置指南（推荐）
 ├── QUICK_START.md                           # 快速入门指南
 └── trading_config.yaml                      # 主配置文件（账户中心化）
 ```

 ## ⚠️ 旧版文档说明

 下方内容为**旧配置格式**的文档，仅供历史参考。  
 **新部署请使用账户中心化配置**，详见 `README_CONFIG.zh-CN.md`。

 ---

 ## 旧版：全局配置 (`trading_config.yaml`)

 > **说明：** 以下参数仅针对旧格式。新版配置将账户 / 模型 / 智能体拆分管理。

 ### 系统设置

 | 参数 | 类型 | 说明 | 默认值 |
 |------|------|------|--------|
 | `system.scan_interval_minutes` | Integer | 智能体轮询市场并决策的间隔（分钟） | 3 |
 | `system.max_concurrent_agents` | Integer | 同时运行的智能体数量上限 | 6 |
 | `system.log_level` | String | 日志等级（DEBUG / INFO / WARNING / ERROR） | INFO |
 | `system.prompt_language` | String | 系统提示词语言（`en` 或 `zh`） | en |

 ### API 设置

 | 参数 | 类型 | 说明 | 默认值 |
 |------|------|------|--------|
 | `api.host` | String | API 服务监听地址 | 0.0.0.0 |
 | `api.port` | Integer | API 服务端口 | 8080 |

 ### 智能体配置

 `agents` 数组定义需要启用的智能体：

 | 参数 | 类型 | 说明 | 必填 |
 |------|------|------|------|
 | `id` | String | 智能体唯一标识 | 是 |
 | `name` | String | 展示名称 | 是 |
 | `enabled` | Boolean | 是否启用该智能体 | 是 |
 | `config_file` | String | 对应模型配置文件路径 | 是 |

 ## 模型配置（旧版）

 每个模型在 `models/` 目录下有独立 YAML 文件，用于控制该智能体的行为。

 ---

 *更多详细内容与风险参数说明请参考英文原文。建议迁移到账户中心化配置，避免重复维护多份文件。*

