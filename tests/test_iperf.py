import pytest
import json
import time
import yaml

# Load matrix for parametrization
with open("test_matrix.yaml", "r") as f:
    matrix_data = yaml.safe_load(f)

@pytest.mark.parametrize("case", [
    c for c in matrix_data['tests'] if c['type'] == 'iperf3'
])
def test_iperf_throughput(tunnel_mgr, case):
    """
    Тест пропускной способности туннеля через iperf3.
    Подключаемся к localhost:src_port на Трансмиттере.
    """
    # 1. Запуск iperf3 сервера на ресивере
    tunnel_mgr.run_rec(f"pkill -9 iperf3 || true")
    tunnel_mgr.run_rec(f"iperf3 -s -p {case['dst_port']} --daemon")
    
    # Даем секунду на запуск сервера
    time.sleep(1)

    # 2. Запуск iperf3 клиента на трансмиттере (подключаемся к localhost:src_port)
    # Мы используем -J для получения JSON вывода
    cmd = f"iperf3 -c localhost -p {case['src_port']} -b 10G --bytes {case['bytes']} -J"
    result = tunnel_mgr.run_trans(cmd)
    
    # 3. Парсинг результатов
    try:
        data = json.loads(result.stdout)
        # Извлекаем скорость получения (receiver) в Gbits/sec
        # bits_per_second / 1e9 = Gbps
        speed_gbps = data['end']['sum_received']['bits_per_second'] / 1e9
    except (json.JSONDecodeError, KeyError) as e:
        pytest.fail(f"Failed to parse iperf3 JSON output: {e}\nOutput: {result.stdout}")
    
    print(f"\nTest {case['name']}: Speed = {speed_gbps:.2f} Gbps")
    
    # 4. Проверка
    assert speed_gbps >= case['expected_min_gbps'], f"Speed too low! Got {speed_gbps:.2f} Gbps, expected {case['expected_min_gbps']}"
