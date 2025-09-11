import request from './index'

export interface LoginRequest {
  password: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
  expires_in: number
}

export interface UserInfo {
  username: string
  role: string
}

export interface MenuConfig {
  dashboard: boolean
  merge_requests: boolean
  statistics: boolean
  prompt_templates: boolean
}

export const authApi = {
  // 登录
  login: (password: string): Promise<TokenResponse> => {
    return request({
      url: '/auth/login',
      method: 'POST',
      data: { password }
    })
  },

  // 获取用户信息
  getUserInfo: (): Promise<UserInfo> => {
    return request({
      url: '/auth/me',
      method: 'GET'
    })
  },

  // 登出
  logout: (): Promise<void> => {
    return request({
      url: '/auth/logout',
      method: 'POST'
    })
  },

  // 获取菜单配置
  getMenuConfig: (): Promise<MenuConfig> => {
    return request({
      url: '/auth/menu-config',
      method: 'GET'
    })
  }
}
