// 环境配置
export const env = {
  // API基础URL，可通过环境变量覆盖
  API_BASE_URL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080',
  
  // 应用标题
  APP_TITLE: import.meta.env.VITE_APP_TITLE || 'GitLab代码审查系统',
  
  // 是否为开发环境
  IS_DEV: import.meta.env.DEV,
  
  // 是否为生产环境
  IS_PROD: import.meta.env.PROD,
}

// 开发环境默认配置
if (env.IS_DEV) {
  console.log('🔧 开发环境配置:', {
    API_BASE_URL: env.API_BASE_URL,
    APP_TITLE: env.APP_TITLE,
  })
}
