mod backend;
use backend::{BackendProcess, spawn_backend};
use tauri::{Emitter, Manager};

#[tauri::command]
async fn start_backend(app: tauri::AppHandle) -> Result<String, String> {
    let state = app.state::<BackendProcess>();
    spawn_backend(app.clone(), &state)
}

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_fs::init())
        .plugin(tauri_plugin_process::init())
        .manage(BackendProcess(std::sync::Mutex::new(None)))
        .invoke_handler(tauri::generate_handler![start_backend])
        .setup(|app| {
            let handle = app.handle().clone();
            tauri::async_runtime::spawn(async move {
                if let Err(e) = start_backend(handle.clone()).await {
                    let _ = handle.emit("backend-status", format!("error: {e}"));
                }
            });
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error running tauri application");
}
