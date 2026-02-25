"""
Simulador de sensores ECG e IMU para RehabiDesk - Versión Alta Fidelidad (50Hz)
"""
import time
import csv
import os
import numpy as np
from datetime import datetime

STREAM_FILE = "sensor_data_stream.csv"
# REDUCCIÓN CLAVE: 0.02s = 50 muestras por segundo (mínimo para visualización fluida)
SAMPLE_RATE = 0.02  

def init_stream_file():
    with open(STREAM_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['timestamp', 'ecg', 'accel_x', 'accel_y', 'accel_z', 
                        'gyro_x', 'gyro_y', 'gyro_z', 'status_ecg', 'status_imu'])

def generate_ecg_sample(t, base_bpm=75):
    heart_rate = base_bpm / 60.0
    beat_period = 1.0 / heart_rate
    t_in_beat = t % beat_period
    normalized_t = t_in_beat / beat_period
    
    ecg = 0.0
    
    # === ONDA P (Aumentada para mejor visibilidad) ===
    if 0.0 <= normalized_t < 0.12:
        p_phase = normalized_t / 0.12
        ecg = 0.12 * np.sin(np.pi * p_phase)
    
    # === COMPLEJO QRS (Morfología más ancha para evitar picos rectos) ===
    elif 0.15 <= normalized_t < 0.30:
        qrs_phase = (normalized_t - 0.15) / 0.15
        if qrs_phase < 0.1: # Q
            ecg = -0.05 * np.sin(np.pi * (qrs_phase/0.1))
        elif qrs_phase < 0.4: # R
            r_inner = (qrs_phase - 0.1) / 0.3
            ecg = 1.0 * np.sin(np.pi * r_inner)
        else: # S
            s_inner = (qrs_phase - 0.4) / 0.6
            ecg = -0.1 * np.sin(np.pi * s_inner)
    
    # === ONDA T (Repolarización más suave) ===
    elif 0.40 <= normalized_t < 0.65:
        t_phase = (normalized_t - 0.40) / 0.25
        ecg = 0.25 * np.sin(np.pi * t_phase)
    
    else:
        ecg = 0.0
    
    # Ruido blanco reducido para que la línea se vea limpia como en la imagen 2
    noise = np.random.normal(0, 0.01)
    ecg += noise
    
    return ecg, "NORMAL"

def generate_imu_sample(t, exercise_phase='extension'):
    movement_freq = 0.3
    cycle_time = t * movement_freq
    
    # Suavizado del ángulo de rodilla
    if exercise_phase == 'extension':
        base_angle = 45 + 15 * np.sin(2 * np.pi * cycle_time)
    else:
        base_angle = 60 + 35 * np.sin(2 * np.pi * cycle_time)
    
    angle = max(0, min(100, base_angle))
    
    accel_x = angle
    accel_y = np.random.normal(0, 0.2)
    accel_z = 9.81 + np.random.normal(0, 0.1)
    
    return accel_x, accel_y, accel_z, 0, 0, 0, "NORMAL"

def run_simulator():
    print(f"🚀 Iniciando Simulador a {1/SAMPLE_RATE} Hz...")
    init_stream_file()
    
    start_time = time.time()
    sample_count = 0
    
    # Aumentamos la ventana a 250 para ver 5 segundos de datos a 50Hz
    MAX_SAMPLES = 250 
    
    try:
        while True:
            current_time = time.time() - start_time
            exercise_phase = 'extension' if (sample_count // 100) % 2 == 0 else 'flexion'
            
            ecg, status_ecg = generate_ecg_sample(current_time)
            imu = generate_imu_sample(current_time, exercise_phase)
            
            # Gestión eficiente de la ventana deslizante
            with open(STREAM_FILE, 'r') as f:
                lines = f.readlines()
            
            with open(STREAM_FILE, 'w', newline='') as f:
                f.write(lines[0]) # Header
                # Mantenemos las últimas N muestras para que la gráfica se mueva
                if len(lines) > MAX_SAMPLES:
                    f.writelines(lines[-(MAX_SAMPLES-1):])
                else:
                    f.writelines(lines[1:])
                
                writer = csv.writer(f)
                writer.writerow([
                    datetime.now().strftime('%H:%M:%S.%f')[:-3],
                    f"{ecg:.4f}", f"{imu[0]:.2f}", f"{imu[1]:.2f}", f"{imu[2]:.2f}",
                    "0", "0", "0", status_ecg, imu[6]
                ])
            
            sample_count += 1
            if sample_count % 50 == 0:
                print(f"Enviando datos... T: {current_time:.2f}s | ECG: {ecg:.3f}")
            
            time.sleep(SAMPLE_RATE)
            
    except KeyboardInterrupt:
        print("\nSimulador detenido.")

if __name__ == '__main__':
    run_simulator()