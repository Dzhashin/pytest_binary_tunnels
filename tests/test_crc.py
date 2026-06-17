import pytest
import time
import yaml

# Load matrix for parametrization
with open("test_matrix.yaml", "r") as f:
    matrix_data = yaml.safe_load(f)

@pytest.mark.parametrize("case", [
    c for c in matrix_data['tests'] if c['type'] == 'crc'
])
def test_file_integrity(tunnel_mgr, case):
    """
    Тест целостности данных: передача файла через туннель и сверка SHA256.
    """
    # 1. Подготовка файла на трансмиттере
    tunnel_mgr.run_trans(f"wget -O {case['file_path']} {case['file_url']} || true")
    
    # Считаем хэш исходного файла
    hash_cmd = f"sha256sum {case['file_path']} | awk '{{print $1}}'"
    original_hash = tunnel_mgr.run_trans(hash_cmd).stdout.strip()
    print(f"\nOriginal Hash: {original_hash}")

    # 2. Запуск слушателя netcat на ресивере в фоне
    tunnel_mgr.run_rec(f"pkill -9 nc || true")
    # Запускаем nc в фоне и перенаправляем вывод в файл
    tunnel_mgr.run_rec(f"nc -l -p {case['dst_port']} > {case['file_path']} &")
    
    # Ждем, пока порт реально откроется (Wait-until)
    timeout = 15
    start_time = time.time()
    port_opened = False
    while time.time() - start_time < timeout:
        check = tunnel_mgr.run_rec(f"netstat -tln | grep :{case['dst_port']}")
        if check.ok:
            port_opened = True
            break
        time.sleep(0.5)

    if not port_opened:
        pytest.fail(f"Receiver NC failed to start on port {case['dst_port']} within {timeout}s")

    # 3. Передача файла с трансмиттера через MUXLINK (localhost:src_port)
    # -q0 закрывает соединение сразу после передачи (для nc на некоторых системах)
    tunnel_mgr.run_trans(f"nc -q0 localhost {case['src_port']} < {case['file_path']}")
    
    # Ждем немного, чтобы файл дозаписался на диск ресивера
    time.sleep(2)

    # 4. Проверка хэша на ресивере
    received_hash = tunnel_mgr.run_rec(hash_cmd).stdout.strip()
    print(f"Received Hash: {received_hash}")

    assert original_hash == received_hash, f"CRC Mismatch! Data corrupted in tunnel.\nExpected: {original_hash}\nGot: {received_hash}"
