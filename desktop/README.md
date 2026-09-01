# Manga Desk desktop workspace

`Manga Desk` is the task-oriented Tauri + React desktop surface for this
project. It calls the existing Python download and PDF engines through
newline-delimited JSON events, so the renderer never reaches into Tkinter or
changes the process working directory.

## Development

```powershell
cd desktop
npm install
npm run tauri dev
```

The Tauri development shell automatically chooses the repository's
`.venv\Scripts\python.exe` when present. Set `MANGA_DESK_PYTHON` to override
it. A distributable installer still needs a bundled Python runtime before it
can be called standalone; the Python sources and `error.jpg` are already
included as Tauri resources.
