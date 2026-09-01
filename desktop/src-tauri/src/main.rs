use std::{
    collections::HashMap,
    io::{BufRead, BufReader},
    path::PathBuf,
    process::{Child, Command, Stdio},
    sync::Mutex,
};

use serde_json::{json, Value};
use tauri::{AppHandle, Emitter, Manager, State};

struct TaskManager(Mutex<HashMap<String, Child>>);

enum Engine {
    Frozen(PathBuf),
    Python { executable: String, script: PathBuf },
}

fn locate_engine(app: &AppHandle) -> Result<Engine, String> {
    // Release builds ship an isolated PyInstaller engine next to the app;
    // end users do not need Python or a virtual environment installed.
    if let Ok(resource_dir) = app.path().resource_dir() {
        let packaged = resource_dir.join("manga-engine").join("manga-engine.exe");
        if packaged.exists() {
            return Ok(Engine::Frozen(packaged));
        }
    }

    // Development intentionally remains source-based for fast iteration.
    let cwd = std::env::current_dir().map_err(|error| error.to_string())?;
    let local = cwd.join("..").join("..").join("desktop_api.py");
    if !local.exists() {
        return Err("找不到本地 Python 引擎。请从 desktop/src-tauri 启动 Tauri。".into());
    }
    let executable = std::env::var("MANGA_DESK_PYTHON").unwrap_or_else(|_| {
        local.parent()
            .map(|root| root.join(".venv").join("Scripts").join("python.exe"))
            .filter(|candidate| candidate.exists())
            .map(|candidate| candidate.to_string_lossy().into_owned())
            .unwrap_or_else(|| "python".into())
    });
    Ok(Engine::Python { executable, script: local })
}

#[tauri::command]
fn start_task(app: AppHandle, manager: State<'_, TaskManager>, action: String, payload: Value) -> Result<(), String> {
    if action != "download" && action != "pdf" { return Err("未知任务类型。".into()); }
    let task_id = payload.get("task_id").and_then(Value::as_str).ok_or("缺少 task_id。")?.to_owned();
    let mut command = match locate_engine(&app)? {
        Engine::Frozen(path) => Command::new(path),
        Engine::Python { executable, script } => {
            let mut command = Command::new(executable);
            command.arg("-X").arg("utf8").arg(script);
            command
        }
    };
    let mut child = command
        .arg(&action)
        .arg(payload.to_string())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .map_err(|error| format!("无法启动 Python 引擎：{error}"))?;

    let stdout = child.stdout.take().ok_or("无法读取 Python 输出。")?;
    let stderr = child.stderr.take().ok_or("无法读取 Python 错误输出。")?;
    manager.0.lock().map_err(|_| "任务管理器不可用。")?.insert(task_id.clone(), child);

    let output_app = app.clone();
    let output_task_id = task_id.clone();
    std::thread::spawn(move || {
        for line in BufReader::new(stdout).lines().map_while(Result::ok) {
            match serde_json::from_str::<Value>(&line) {
                Ok(event) => { let _ = output_app.emit("task-event", event); }
                Err(_) => { let _ = output_app.emit("task-event", json!({"type": "log", "taskId": output_task_id, "message": line})); }
            }
        }
    });

    let error_app = app.clone();
    let error_task_id = task_id;
    std::thread::spawn(move || {
        for line in BufReader::new(stderr).lines().map_while(Result::ok) {
            let _ = error_app.emit("task-event", json!({"type": "log", "taskId": error_task_id, "message": format!("引擎：{line}")}));
        }
    });
    Ok(())
}

#[tauri::command]
fn cancel_task(manager: State<'_, TaskManager>, task_id: String) -> Result<(), String> {
    let mut tasks = manager.0.lock().map_err(|_| "任务管理器不可用。")?;
    let process = tasks.get_mut(&task_id).ok_or("任务不存在或已经结束。")?;
    process.kill().map_err(|error| format!("无法停止任务：{error}"))
}

fn main() {
    tauri::Builder::default()
        .manage(TaskManager(Mutex::new(HashMap::new())))
        .invoke_handler(tauri::generate_handler![start_task, cancel_task])
        .run(tauri::generate_context!())
        .expect("启动 Manga Desk 时发生错误");
}
