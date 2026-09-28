import type { Task } from './types'

const pendingTitle = '正在识别作品标题'

export function restoreTaskTitle(task: Task): Task {
  if (task.kind !== 'download' || task.title !== pendingTitle || !task.outputPath) return task
  const folder = task.outputPath.replace(/[\\/]+$/, '').split(/[\\/]/).pop()
  return folder ? { ...task, title: folder } : task
}
