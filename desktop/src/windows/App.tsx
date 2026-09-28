import { FormEvent, useEffect, useMemo, useState } from 'react'
import {
  AlertCircle, Check, ChevronRight, Clock3, Copy,
  Download, FileOutput, FolderOpen, LoaderCircle, Plus,
  Settings2, SlidersHorizontal, X,
} from 'lucide-react'
import type { AppSettings, BridgeEvent, Task } from '../types'
import { restoreTaskTitle } from '../taskTitle'
import Brand from '../Brand'

const defaultSettings: AppSettings = {
  savePath: 'D:\\', proxyHost: '127.0.0.1', proxyPort: '7890', generatePdf: true, pdfAuthor: '',
}

type SessionSnapshot = { tasks?: Task[]; logs?: string[] }

function isTauri() {
  return '__TAURI_INTERNALS__' in window
}

function id() {
  return crypto.randomUUID()
}

function statusLabel(task: Task) {
  const labels = { ready: '等待开始', running: '下载中', completed: '已完成', failed: '需要处理', cancelled: '已取消' }
  return labels[task.status]
}

function ProgressRing({ value }: { value: number }) {
  return <div className="progress-ring" style={{ '--progress': `${value * 3.6}deg` } as React.CSSProperties}><span>{Math.round(value)}%</span></div>
}

export default function App({ defaultSavePath = 'D:\\' }: { defaultSavePath?: string }) {
  const [section, setSection] = useState<'downloads' | 'pdf' | 'history' | 'settings'>('downloads')
  const [settings, setSettings] = useState<AppSettings>(() => {
    const saved = localStorage.getItem('manga-desk.settings')
    return saved ? { ...defaultSettings, savePath: defaultSavePath, ...JSON.parse(saved) } : { ...defaultSettings, savePath: defaultSavePath }
  })
  const [url, setUrl] = useState('')
  const [folderName, setFolderName] = useState('')
  const [pdfFolder, setPdfFolder] = useState('')
  const [pdfName, setPdfName] = useState('')
  const [tasks, setTasks] = useState<Task[]>([])
  const [selectedId, setSelectedId] = useState('')
  const [logs, setLogs] = useState<string[]>([])
  const [sessionReady, setSessionReady] = useState(!isTauri())

  const selectedTask = useMemo(() => tasks.find((task) => task.id === selectedId) ?? tasks[0], [tasks, selectedId])
  const activeCount = tasks.filter((task) => task.status === 'running').length

  useEffect(() => localStorage.setItem('manga-desk.settings', JSON.stringify(settings)), [settings])

  useEffect(() => {
    if (!isTauri()) return
    const loadSession = async () => {
      const { invoke } = await import('@tauri-apps/api/core')
      try {
        const snapshot = await invoke<SessionSnapshot>('load_session')
        const restoredTasks = Array.isArray(snapshot.tasks) ? snapshot.tasks.map((task) => task.status === 'running'
          ? { ...task, status: 'cancelled' as const, detail: '上次关闭时未完成。' }
          : task).map(restoreTaskTitle) : []
        setTasks(restoredTasks)
        setLogs(Array.isArray(snapshot.logs) ? snapshot.logs.slice(-200) : [])
        setSelectedId(restoredTasks[0]?.id ?? '')
      } finally {
        setSessionReady(true)
      }
    }
    void loadSession()
  }, [])

  useEffect(() => {
    if (!isTauri() || !sessionReady) return
    const timer = window.setTimeout(() => {
      void import('@tauri-apps/api/core').then(({ invoke }) => invoke('save_session', {
        session: { version: 1, tasks, logs: logs.slice(-200) },
      }))
    }, 250)
    return () => window.clearTimeout(timer)
  }, [logs, sessionReady, tasks])

  useEffect(() => {
    if (!isTauri()) return
    let unlisten: (() => void) | undefined
    void import('@tauri-apps/api/event').then(({ listen }) => listen<BridgeEvent>('task-event', (event) => {
      const payload = event.payload
      if (payload.type === 'log' && payload.message) setLogs((items) => [...items.slice(-199), payload.message!])
      if (!payload.taskId) return
      setTasks((items) => items.map((task) => {
        if (task.id !== payload.taskId) return task
        if (payload.type === 'metadata' && payload.title) return { ...task, title: payload.title }
        if (payload.type === 'progress') return {
          ...task, status: 'running', progress: payload.progress ?? task.progress,
          detail: payload.status ?? task.detail, success: payload.success ?? task.success,
          failed: payload.failed ?? task.failed, total: payload.total ?? task.total,
        }
        if (payload.type === 'completed') return restoreTaskTitle({
          ...task, status: payload.status === 'completed' ? 'completed' : 'failed',
          progress: payload.status === 'completed' ? 100 : task.progress,
          detail: payload.error ?? (payload.status === 'completed' ? '任务已完成。' : '任务未完成。'),
          outputPath: payload.outputPath,
        })
        return task
      }))
    }).then((fn) => { unlisten = fn }))
    return () => unlisten?.()
  }, [])

  async function startTask(task: Task, action: 'download' | 'pdf', payload: object) {
    setTasks((items) => [task, ...items])
    setSelectedId(task.id)
    setLogs((items) => [...items, `已创建 ${action === 'download' ? '下载' : 'PDF'} 任务。`])
    if (!isTauri()) {
      setLogs((items) => [...items, '当前是浏览器预览；请使用 Tauri 桌面壳执行本地任务。'])
      return
    }
    const { invoke } = await import('@tauri-apps/api/core')
    try {
      await invoke('start_task', { action, payload: { ...payload, task_id: task.id } })
    } catch (error) {
      setTasks((items) => items.map((item) => item.id === task.id ? { ...item, status: 'failed', detail: String(error) } : item))
      setLogs((items) => [...items, `启动失败：${String(error)}`])
    }
  }

  function submitDownload(event: FormEvent) {
    event.preventDefault()
    const taskId = id()
    void startTask({
      id: taskId, kind: 'download', status: 'running', title: folderName.trim() || '正在识别作品标题', url,
      progress: 0, success: 0, failed: 0, total: 0, detail: '正在连接…', createdAt: new Date().toISOString(),
    }, 'download', {
      url, save_path: settings.savePath, folder_name: folderName,
      proxy_host: settings.proxyHost, proxy_port: settings.proxyPort,
      generate_pdf: settings.generatePdf, pdf_author: settings.pdfAuthor,
    })
  }

  function submitPdf(event: FormEvent) {
    event.preventDefault()
    const taskId = id()
    void startTask({
      id: taskId, kind: 'pdf', status: 'running', title: pdfName.trim() || '生成 PDF',
      progress: 0, success: 0, failed: 0, total: 0, detail: '正在读取图片文件夹…', createdAt: new Date().toISOString(),
    }, 'pdf', { folder_path: pdfFolder, output_name: pdfName, author: settings.pdfAuthor })
  }

  async function cancelSelected() {
    if (!selectedTask || !isTauri()) return
    const { invoke } = await import('@tauri-apps/api/core')
    await invoke('cancel_task', { taskId: selectedTask.id })
    setTasks((items) => items.map((task) => task.id === selectedTask.id ? { ...task, status: 'cancelled', detail: '已停止任务。' } : task))
  }

  async function selectOrOpenTask(task: Task) {
    setSelectedId(task.id)
    if (!task.outputPath || !isTauri()) return
    const { invoke } = await import('@tauri-apps/api/core')
    try {
      await invoke('open_output', { path: task.outputPath })
    } catch (error) {
      setLogs((items) => [...items, `无法打开输出位置：${String(error)}`])
    }
  }

  const nav = [
    ['downloads', Download, '下载队列'], ['pdf', FileOutput, 'PDF 工具'],
    ['history', Clock3, '历史记录'], ['settings', Settings2, '偏好设置'],
  ] as const

  return <main className="app-shell">
    <aside className="sidebar">
      <Brand />
      <nav>{nav.map(([key, Icon, label]) => <button key={key} className={section === key ? 'nav-item active' : 'nav-item'} onClick={() => setSection(key)}><Icon size={17}/><span>{label}</span>{key === 'downloads' && activeCount > 0 && <em>{activeCount}</em>}</button>)}</nav>
    </aside>

    <section className="workspace">
      <header className="topbar"><h1>{section === 'downloads' ? '下载队列' : section === 'pdf' ? 'PDF 工具' : section === 'history' ? '任务历史' : '偏好设置'}</h1><div className="topbar-actions"><button className="icon-button" aria-label="打开设置" onClick={() => setSection('settings')}><SlidersHorizontal size={18}/></button></div></header>

      {section === 'downloads' && <>
        <form className="create-task" onSubmit={submitDownload}>
          <div className="task-number">01</div><div className="form-content"><label htmlFor="url">作品第一页地址</label><input id="url" value={url} onChange={(event) => setUrl(event.target.value)} placeholder="https://e-hentai.org/s/…" autoComplete="off" required/><div className="inline-options"><input id="name" value={folderName} onChange={(event) => setFolderName(event.target.value)} placeholder="可选：自定义文件夹名称"/><label className="check"><input type="checkbox" checked={settings.generatePdf} onChange={(event) => setSettings({ ...settings, generatePdf: event.target.checked })}/><span>完成后生成 PDF</span></label></div></div><button className="primary-button" type="submit"><Plus size={18}/>创建任务</button>
        </form>
        <section className="task-list" aria-label="下载任务"><div className="section-line"><span>任务</span><span>{tasks.length} 个任务</span></div>{tasks.map((task) => <button key={task.id} className={selectedId === task.id ? 'task-row selected' : 'task-row'} onClick={() => void selectOrOpenTask(task)} title={task.outputPath ? '打开输出位置' : undefined}><div className={`status-dot ${task.status}`}/><div className="task-main"><strong>{restoreTaskTitle(task).title}</strong><span>{task.detail}</span></div><div className="task-progress"><div><span>{task.total ? `${task.success}/${task.total} 页` : statusLabel(task)}</span><b>{Math.round(task.progress)}%</b></div><div className="track"><i style={{ width: `${task.progress}%` }}/></div></div><ChevronRight size={17}/></button>)}</section>
      </>}

      {section === 'pdf' && <form className="tool-form" onSubmit={submitPdf}><div className="tool-intro"><span className="tool-icon"><FileOutput size={23}/></span><div><h2>从图片文件夹生成 PDF</h2><p>按自然排序合并 JPG、PNG、WebP 图片。</p></div></div><label>图片文件夹<input value={pdfFolder} onChange={(event) => setPdfFolder(event.target.value)} placeholder="D:\\Manga\\作品名称" required/></label><label>输出文件名<input value={pdfName} onChange={(event) => setPdfName(event.target.value)} placeholder="留空则使用文件夹名称"/></label><button className="primary-button" type="submit"><FileOutput size={18}/>生成 PDF</button></form>}

      {section === 'history' && <section className="task-list" aria-label="已保存任务"><div className="section-line"><span>已保存任务</span><span>{tasks.length} 项</span></div>{tasks.map((task) => <button key={task.id} className="task-row" onClick={() => { setSection('downloads'); void selectOrOpenTask(task) }} title={task.outputPath ? '打开输出位置' : undefined}><div className={`status-dot ${task.status}`}/><div className="task-main"><strong>{restoreTaskTitle(task).title}</strong><span>{task.detail}</span></div><div className="task-progress"><div><span>{task.total ? `${task.success}/${task.total} 页` : statusLabel(task)}</span><b>{Math.round(task.progress)}%</b></div><div className="track"><i style={{ width: `${task.progress}%` }}/></div></div><ChevronRight size={17}/></button>)}</section>}

      {section === 'settings' && <section className="settings-form"><div className="section-line"><span>下载设置</span></div><label>默认保存位置<input value={settings.savePath} onChange={(event) => setSettings({ ...settings, savePath: event.target.value })}/></label><div className="two-column"><label>代理主机<input value={settings.proxyHost} onChange={(event) => setSettings({ ...settings, proxyHost: event.target.value })}/></label><label>代理端口<input value={settings.proxyPort} onChange={(event) => setSettings({ ...settings, proxyPort: event.target.value })}/></label></div><label>PDF 作者（可选）<input value={settings.pdfAuthor} onChange={(event) => setSettings({ ...settings, pdfAuthor: event.target.value })}/></label><p className="setting-note"><AlertCircle size={15}/>下载任务使用显式保存路径。</p></section>}
    </section>

    <aside className="inspector"><div className="inspector-title"><span>任务详情</span>{selectedTask?.status === 'running' && <button className="quiet-button" onClick={() => void cancelSelected()}><X size={15}/>停止</button>}</div>{selectedTask && <><ProgressRing value={selectedTask.progress}/><div className="inspect-copy"><span className={`pill ${selectedTask.status}`}>{selectedTask.status === 'completed' ? <Check size={13}/> : selectedTask.status === 'failed' ? <AlertCircle size={13}/> : <LoaderCircle size={13}/>} {statusLabel(selectedTask)}</span><h2>{restoreTaskTitle(selectedTask).title}</h2><p>{selectedTask.detail}</p></div><dl><div><dt>成功</dt><dd>{selectedTask.success}</dd></div><div><dt>失败</dt><dd className={selectedTask.failed ? 'danger' : ''}>{selectedTask.failed}</dd></div><div><dt>总页数</dt><dd>{selectedTask.total || '—'}</dd></div></dl>{selectedTask.outputPath && <button className="path-button" onClick={() => void selectOrOpenTask(selectedTask)} title="打开输出位置"><FolderOpen size={16}/>{selectedTask.outputPath}</button>}</>}<div className="log-panel"><div><span>活动记录</span><button onClick={() => navigator.clipboard.writeText(logs.join('\n'))} aria-label="复制日志"><Copy size={14}/></button></div><pre>{logs.slice(-8).join('\n')}</pre></div></aside>
  </main>
}
