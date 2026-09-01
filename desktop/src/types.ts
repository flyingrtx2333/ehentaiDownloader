export type TaskStatus = 'ready' | 'running' | 'completed' | 'failed' | 'cancelled'

export interface Task {
  id: string
  kind: 'download' | 'pdf'
  status: TaskStatus
  title: string
  url?: string
  progress: number
  success: number
  failed: number
  total: number
  detail: string
  outputPath?: string
  createdAt: string
}

export interface BridgeEvent {
  type: 'started' | 'progress' | 'log' | 'completed' | 'error'
  taskId?: string
  kind?: 'download' | 'pdf'
  progress?: number
  status?: string
  success?: number
  failed?: number
  total?: number
  message?: string
  error?: string
  outputPath?: string
  failedUrls?: string[]
}

export interface AppSettings {
  savePath: string
  proxyHost: string
  proxyPort: string
  generatePdf: boolean
  pdfAuthor: string
}
