# 代码审查系统前端

## 包管理器

本项目使用 [Bun](https://bun.sh/) 作为包管理器，它比 npm 更快、更高效。

## 安装依赖

```bash
# 安装所有依赖
bun install
```

## 开发

```bash
# 启动开发服务器
bun run dev

# 或者直接使用
bun dev
```

## 构建

```bash
# 构建生产版本
bun run build

# 或者直接使用
bun build
```

## 代码检查

```bash
# 运行 ESLint
bun run lint

# 类型检查
bun run type-check
```

## 预览构建结果

```bash
# 预览生产构建
bun run preview
```

## 添加新依赖

```bash
# 添加生产依赖
bun add <package-name>

# 添加开发依赖
bun add -d <package-name>

# 添加全局依赖
bun add -g <package-name>
```

## 删除依赖

```bash
# 删除依赖
bun remove <package-name>
```

## 更新依赖

```bash
# 更新所有依赖
bun update

# 更新特定依赖
bun update <package-name>
```

## 为什么选择 Bun？

- **速度更快**: Bun 的安装速度比 npm 快 10-100 倍
- **内存效率**: 更低的内存使用量
- **兼容性**: 完全兼容 npm 生态系统
- **内置工具**: 包含测试运行器、打包工具等
- **TypeScript 支持**: 原生支持 TypeScript

## 环境要求

- Node.js 18+ 或 Bun 1.0+
- 推荐使用 Bun 1.2.18 或更高版本
