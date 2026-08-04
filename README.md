# Orbit AI Work OS

可运行的 AI 工作操作系统 MVP，包含真实用户认证、会议录音处理、智能日报、企业知识库与 RAG 问答。

## 技术栈

- Frontend: Next.js 15、TypeScript、Tailwind CSS、Shadcn UI
- Backend: FastAPI、SQLAlchemy、JWT
- Database: PostgreSQL 16
- AI: OpenAI Responses API、Audio Transcriptions、Embeddings
- Storage: 本地持久卷（生产环境可替换为 S3/R2）

## 启动方式

1. 安装 Docker Desktop。
2. 将 `.env.example` 复制为 `.env`，填写 `OPENAI_API_KEY` 和安全的 `JWT_SECRET`。
3. 启动数据库与后端：`docker compose up --build`。
4. 安装前端依赖：`npm install`。
5. 启动前端：`npm run dev`。
6. 打开 `http://localhost:3000`，创建账号后开始使用。

后端接口文档位于 `http://localhost:8000/docs`。

## AI 模式

- 配置 `OPENAI_API_KEY`：使用真实 OpenAI 转写、总结、Embedding 与问答。
- 未配置 API Key：系统进入演示模式，所有演示生成结果会带 `demo` 标记，方便在没有外部凭据时完整体验产品流程。

## 已实现功能

- 注册、登录、JWT 会话验证、退出登录
- 音频上传、后台转写、结构化会议总结、状态轮询
- 基于指定日期会议与用户补充内容生成日报
- PDF、DOCX、TXT、Markdown 上传、解析、分块和 Embedding
- 文档检索、AI 问答和引用片段展示
- 用户级数据隔离、文件类型及 100MB 大小限制
- Dashboard 真实统计、响应式侧边栏和业务导航

## 生产化建议

上线前应将 BackgroundTasks 替换为 Celery/Redis，将本地文件存储替换为 S3/R2，增加数据库迁移、Refresh Token、邮件验证、审计日志、限流、病毒扫描以及 workspace 级多租户权限。
