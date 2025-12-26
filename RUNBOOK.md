# T249 실행/배포 가이드

아래는 **미니PC(리눅스)에서 서버 구동**, **안드로이드/웹 접속**, **실시간 데이터 입력**까지 전부 분리해서 정리한 가이드입니다.

## 0) 구성 요약 (분리 구조)

- **MonitoringServer (미니PC)**  
  TCP 8082로 센서 데이터 수신, HTTP 8080으로 API 제공
- **Data Sender (미니PC 또는 장비 PC)**  
  장비/CSV/실시간 스트림 데이터를 TCP 8082로 전송
- **Client**
  - Android 앱: `BASE_URL`로 미니PC API 접속
  - Web 앱: Flutter Web 빌드 후 브라우저에서 접속

---

## 1) 미니PC(리눅스)에서 MonitoringServer 실행

### 1-1. 준비
```bash
cd /path/to/T249/TSR_MonitoringServer-master/TSR_MonitoringServer-master
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 1-2. 서버 실행
```bash
python src/main.py
```

### 1-3. 서버 설정 위치
`resources/config.yml`에서 포트/경로를 설정합니다.

- `SERVER.PORT`: HTTP API 포트 (기본 8080)
- `SERVER.TCP_PORT`: 데이터 수신 포트 (기본 8082)
- `SERVER.HOST`: 바인딩 주소 (기본 0.0.0.0)

파일: `TSR_MonitoringServer-master/TSR_MonitoringServer-master/resources/config.yml`

---

## 2) 데이터 입력 방식 (기존 코드 기준)

### 2-1. TCP 실시간 수신 (프로덕션)
DAQ 시스템은 **TCP 8082**로 아래 형식의 데이터를 전송합니다.

- 이벤트: `DataUpdate`
- payload: `{sensor_name: {type: "VIB|TEMP", data: [float, ...]}}`

이 프로토콜은 기존 `TSR_DAQSystem-master` 내부 `DataSender`가 사용합니다.
관련 코드:
- `TSR_DAQSystem-master/TSR_DAQSystem-master/src/background/data_sender.py`

### 2-2. CSV 파일 감시 (테스트/샘플)
CSV 폴더를 감시해서 새 파일을 발견하면 자동 전송합니다.

```bash
cd /path/to/T249
MACHINE_NAME=ShotBlast SENSOR_NAME=shot_blast_vib1 ./scripts/run_csv_bridge.sh /path/to/watch_dir
```

센서가 여러 개면 **브리지 프로세스를 여러 개 실행**하세요.

### 2-3. 서버 IP/포트 수정 위치 (데이터 입력 측)
**어디로 보낼지(서버 IP/포트)를 바꾸는 위치는 아래입니다.**

- CSV 브리지 (테스트)
  - 스크립트 기본값: `scripts/run_csv_bridge.sh`
    - `SERVER_HOST`, `SERVER_PORT`
  - 실행 시 오버라이드:
    ```bash
    SERVER_HOST=<미니PC_IP> SERVER_PORT=8082 ./scripts/run_csv_bridge.sh /path/to/watch_dir
    ```
  - 직접 실행 시:
    ```bash
    python tools/csv_bridge.py --host <미니PC_IP> --port 8082 ...
    ```

- 실제 DAQ 송신 (프로덕션)
  - DAQ 설정에 **송신 대상 IP/포트**가 저장됩니다.
  - 설정 구조: `DataSendModeConfig`
    - `TSR_DAQSystem-master/TSR_DAQSystem-master/src/config/configs.py`
  - 적용 위치: `TSR_DAQSystem-master/TSR_DAQSystem-master/src/background/daq_system.py`
  - 실제 값은 **DAQ 설정 UI**를 통해 저장되는 방식입니다.

---

## 3) Android 앱 실행/배포

### 3-1. 개발기기에서 실행
`BASE_URL`에 **미니PC IP**를 넣어 실행합니다.

```bash
cd /path/to/T249/tsr_monitoring_app-master/tsr_monitoring_app-master
flutter run -d <android-device-id> --dart-define=BASE_URL=http://<미니PC_IP>:8080
```

### 3-2. APK 빌드
```bash
flutter build apk --release --dart-define=BASE_URL=http://<미니PC_IP>:8080
```

#### IP를 어디에 적는지?
- 실행/빌드 시 `--dart-define=BASE_URL=...`에 입력
- 기본값을 코드에 박으려면 아래 파일의 `BASE_URL` 수정
  - `tsr_monitoring_app-master/tsr_monitoring_app-master/lib/util/constants.dart`
- 앱 내 설정 화면에서 서버 주소 변경 가능  
  - 설정 → 서버 주소 입력 → 저장  
  - 저장값이 있으면 그 값을 우선 사용, 없으면 `BASE_URL` 기본값 사용

---

## 4) Web 앱 실행/배포

### 4-1. 개발 모드 (로컬)
```bash
cd /path/to/T249
./scripts/run_flutter_web.sh
```
> Chrome 필요

### 4-2. 정적 빌드 후 배포 (권장)
```bash
cd /path/to/T249/tsr_monitoring_app-master/tsr_monitoring_app-master
flutter build web --release --dart-define=BASE_URL=http://<미니PC_IP>:8080
```

빌드 결과는 `build/web`에 생성됩니다.  
이 폴더를 **미니PC에서 정적 웹 서버로 호스팅**하면 다른 휴대폰에서 접속 가능합니다.

예시 (미니PC에서):
```bash
cd /path/to/build/web
python3 -m http.server 9090 --bind 0.0.0.0
```

휴대폰에서 접속:  
`http://<미니PC_IP>:9090`

---

## 5) 방화벽/네트워크 체크

미니PC 방화벽에서 아래 포트가 열려 있어야 합니다:
- `8080` (API)
- `8082` (TCP 데이터)
- `9090` (웹 호스팅 시)

### OS별 빠른 체크
- macOS: `ipconfig getifaddr en0`
- Linux: `ip addr show | grep "inet "`
- Windows: `ipconfig`

### OS별 서버 실행 예시

**Linux**
```bash
cd /path/to/T249/TSR_MonitoringServer-master/TSR_MonitoringServer-master
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python src/main.py
```

**Windows (PowerShell)**
```powershell
cd C:\path\to\T249\TSR_MonitoringServer-master\TSR_MonitoringServer-master
py -3.11 -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python src\main.py
```

**macOS**
```bash
cd /path/to/T249/TSR_MonitoringServer-master/TSR_MonitoringServer-master
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python src/main.py
```

### OS별 웹 정적 서버

**Linux/macOS**
```bash
cd /path/to/build/web
python3 -m http.server 9090 --bind 0.0.0.0
```

**Windows (PowerShell)**
```powershell
cd C:\path\to\build\web
py -3 -m http.server 9090 --bind 0.0.0.0
```

---

## 6) 문제 발생 시 체크리스트

1. 서버 실행 로그에 `ShotBlast connected`가 뜨는지 확인  
2. `BASE_URL`이 **미니PC IP**로 정확히 들어갔는지 확인  
3. 미니PC와 휴대폰이 **같은 네트워크**인지 확인  
4. CSV 브리지/DAQ가 **TCP 8082로 연결되는지** 확인
