# T249
개인 외주

실행/배포 절차는 `RUNBOOK.md`에 정리했습니다.

## 통합 실행 가이드 (웹 기준)
아래 순서로 서버 + CSV 브릿지 + Flutter Web을 실행하면, 기존 기능을 유지하면서
CSV 파일을 실시간 그래프로 표시할 수 있습니다.

### 1) Monitoring Server 실행
```bash
./scripts/run_monitoring_server.sh
```

### 2) CSV → TCP 브릿지 실행
CSV가 생성되는 폴더를 지정해 실행합니다.
```bash
./scripts/run_csv_bridge.sh /path/to/csv_dir
```
기본값:
- MACHINE_NAME: `ShotBlast`
- SENSOR_NAME: `shot_blast_vib1`
- SERVER_HOST: `127.0.0.1`
- SERVER_PORT: `8082`

환경 변수로 변경 가능:
```bash
MACHINE_NAME=VacuumPump1 SENSOR_NAME=pump1_vib ./scripts/run_csv_bridge.sh /path/to/csv_dir
```

### 3) Flutter Web 실행
```bash
BASE_URL=http://localhost:8080 ./scripts/run_flutter_web.sh
```

## CSV 브릿지 사용 설명
- 위치: `TSR_MonitoringServer-master/TSR_MonitoringServer-master/tools/csv_bridge.py`
- CSV 컬럼은 `time, y` 또는 `time, data` 형태를 지원합니다.
- 초당 100개 샘플을 30Hz로 다운샘플링하여 전송합니다.

## 참고
- Flutter 앱은 `BASE_URL`을 `--dart-define`으로 주입합니다.
  - 기본값은 `http://localhost:8080` 입니다.
