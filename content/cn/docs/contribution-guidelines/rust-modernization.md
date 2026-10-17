---
title: "Rust 渐进式现代化路线图"
linkTitle: "Rust 现代化"
weight: 7
description: "HugeGraph 各组件渐进式 Rust 实验的状态与贡献入口。"
---

本页是 HugeGraph 生态渐进式 Rust 现代化工作的文档入口。它用于汇总仍在推进的提案，并不代表项目承诺重写现有组件，也不代表相关功能已经发布。

## 路线图

| 领域 | 仓库 | 跟踪 Issue | 当前成熟度 | 负责人 |
| --- | --- | --- | --- | --- |
| 工具链 | `apache/hugegraph-toolchain` | [#748](https://github.com/apache/hugegraph-toolchain/issues/748) | 提案跟踪 | 待在 Issue 中确认 |
| Server、HStore 与 PD | `apache/hugegraph` | [#3110](https://github.com/apache/hugegraph/issues/3110) | 提案跟踪 | 待在 Issue 中确认 |
| 图计算 | `apache/hugegraph-computer` | [#355](https://github.com/apache/hugegraph-computer/issues/355) | 提案跟踪 | 待在 Issue 中确认 |
| 文档中心 | `apache/hugegraph-doc` | [#462](https://github.com/apache/hugegraph-doc/issues/462) | 提案跟踪 | 待在 Issue 中确认 |

上述 Issue 是范围和状态的事实来源。在代码、测试和文档被接受之前，不应把提案描述为已经实现。

## 统一成熟度术语

- **提案跟踪（Proposal tracking）**：已有 Issue，但尚无被接受的实现。
- **实验（Experiment）**：已有可评估的概念验证；API、格式和行为可能变化，不提供兼容性保证。
- **预览（Preview）**：已有安装和验证文档，可供选择性评估，但尚不推荐作为生产环境默认方案。
- **生产就绪（Production-ready）**：维护者已经明确支持范围、兼容性、升级与回滚、运行限制及发布版本。

每个 Rust 相关页面都应注明成熟度、负责仓库或 Issue、支持平台、已知限制，以及包含该行为的发布版本。规划中的行为必须明确标记为**提案**。

## 交付门槛

文档应随实现同步演进：

1. **RFC 或提案**：记录目标、非目标、负责人、兼容性风险和验收标准。
2. **概念验证**：提供可复现的构建与测试步骤，并列出已知限制。
3. **预览**：补充兼容性矩阵、迁移与回滚、基准测试和故障排查。
4. **生产就绪**：说明支持的版本与平台、升级保证、运行指南和对应发布版本。

## 如何参与

请选择一个关联的跟踪 Issue，并先确认计划工作没有被其他贡献者认领。适合作为第一步的贡献包括：

- 根据已接受的工作同步路线图表格；
- 在负责仓库中提出 Rust 工具链与 workspace 约定；
- 添加兼容性、平台或基准报告模板；
- 用可复现命令记录已接受的概念验证；
- 保持中英文内容一致。

基准测试结论必须包含源码版本、硬件、数据集、配置、命令和可重复结果，否则不应发布。
