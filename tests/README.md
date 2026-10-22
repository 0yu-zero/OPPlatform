# tests — 跨端(E2E)测试

这里放**不属于任何单个端**的测试,例如:

- 启动 web-backend 服务,通过 HTTP 触发 platform 训练
- 端与端之间的数据契约测试

各端自己的单元测试放在 `apps/<端>/tests/`。