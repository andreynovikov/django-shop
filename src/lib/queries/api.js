import axios from 'axios'

const AXIOS_CONFIG = {
  baseURL: (process.env.API_SERVER ?? '') + '/api/v0',
  withCredentials: true,
}

export const apiClient = axios.create(AXIOS_CONFIG)

apiClient.defaults.headers.post['Content-Type'] = 'application/json'
apiClient.defaults.headers.put['Content-Type'] = 'application/json'

apiClient.interceptors.request.use(async function (config) {
  const session = typeof (localStorage) !== 'undefined' && localStorage.getItem('session')

  if (typeof window === 'undefined') {// set referrer when running on server
    config.headers['Referer'] = process.env.NEXT_PUBLIC_ORIGIN
    config.headers['Origin'] = process.env.NEXT_PUBLIC_ORIGIN
  }
  if (config.method === 'post' || config.method === 'put') {
    const response = await axios.get('csrf/', {
      ...AXIOS_CONFIG,
      headers: session ? { 'x-session': session } : {}
    })
    config.headers['x-csrftoken'] = response.data.csrf
  }
  if (session)
    config.headers['x-session'] = session
  return config
}, function (error) {
  return Promise.reject(error)
})

apiClient.interceptors.response.use(function (response) {
  if ('x-session' in response.headers) {
    const session = response.headers['x-session']
    localStorage.setItem("session", session)
  }
  return response
}, function (error) {
  return Promise.reject(error)
})