// Prevents an extra console window on Windows in release.
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod commands;

fn main() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![
            commands::list_profiles,
            commands::run_illusion,
            commands::run_volatility,
            commands::run_discounting,
            commands::run_self_motion,
            commands::run_perturbation,
        ])
        .run(tauri::generate_context!())
        .expect("error while running akribia GUI");
}
