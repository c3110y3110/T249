#!/usr/bin/env python3
import argparse
import csv
import io
import pickle
import socket
import time
from pathlib import Path
from typing import Iterable, List, Optional, Set, Tuple


SEP = b"\o"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Watch a directory for CSV files and stream them to the monitoring server "
            "using the existing TCP protocol."
        )
    )
    parser.add_argument("--watch-dir", required=True, help="Directory to watch for CSV files.")
    parser.add_argument("--host", default="127.0.0.1", help="Monitoring server host.")
    parser.add_argument("--port", type=int, default=8082, help="Monitoring server TCP port.")
    parser.add_argument("--machine-name", required=True, help="Machine name to register.")
    parser.add_argument(
        "--sensor-name",
        default="shot_blast_vib1",
        help="Sensor/channel name used by the app.",
    )
    parser.add_argument(
        "--sensor-type",
        default="VIB",
        choices=["VIB", "TEMP"],
        help="Sensor type for server statistics.",
    )
    parser.add_argument(
        "--output-rate",
        type=int,
        default=30,
        help="Samples per second to send to the server.",
    )
    parser.add_argument(
        "--poll-interval",
        type=float,
        default=1.0,
        help="Seconds between directory scans.",
    )
    parser.add_argument(
        "--replay-sleep",
        action="store_true",
        help="Sleep 1 second between each second of data to mimic real-time.",
    )
    return parser.parse_args()


def detect_columns(fieldnames: List[str]) -> Tuple[str, str]:
    lower_map = {name.lower(): name for name in fieldnames}
    time_key = lower_map.get("time") or fieldnames[0]
    for key in ("y", "data", "amplitude", "value"):
        if key in lower_map:
            return time_key, lower_map[key]
    if len(fieldnames) < 2:
        raise ValueError("CSV needs at least two columns (time, value).")
    return time_key, fieldnames[1]


def load_csv(path: Path) -> Iterable[Tuple[str, float]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError(f"No headers found in {path}.")
        time_key, value_key = detect_columns(reader.fieldnames)
        for row in reader:
            raw_value = row.get(value_key)
            if raw_value is None:
                continue
            try:
                value = float(raw_value)
            except ValueError:
                continue
            yield row.get(time_key, ""), value


def downsample(values: List[float], target_count: int) -> List[float]:
    if target_count <= 0:
        return []
    if len(values) <= target_count:
        return values
    step = len(values) / target_count
    return [values[int(i * step)] for i in range(target_count)]


def group_by_time(rows: Iterable[Tuple[str, float]]) -> Iterable[Tuple[str, List[float]]]:
    current_time: Optional[str] = None
    bucket: List[float] = []
    for time_value, data_value in rows:
        if current_time is None:
            current_time = time_value
        if time_value != current_time:
            yield current_time, bucket
            current_time = time_value
            bucket = []
        bucket.append(data_value)
    if current_time is not None and bucket:
        yield current_time, bucket


class TcpBridgeClient:
    def __init__(self, host: str, port: int, machine_name: str):
        self.host = host
        self.port = port
        self.machine_name = machine_name
        self.socket: Optional[socket.socket] = None

    def connect(self) -> None:
        self.socket = socket.create_connection((self.host, self.port))
        self.send_event("name", self.machine_name)

    def send_event(self, event: str, data) -> None:
        if self.socket is None:
            raise RuntimeError("TCP connection is not established.")
        payload = pickle.dumps((event, data)) + SEP
        self.socket.sendall(payload)

    def close(self) -> None:
        if self.socket is not None:
            self.socket.close()
            self.socket = None


def stream_file(
    client: TcpBridgeClient,
    path: Path,
    sensor_name: str,
    sensor_type: str,
    output_rate: int,
    replay_sleep: bool,
) -> None:
    rows = load_csv(path)
    for _, values in group_by_time(rows):
        sampled = downsample(values, output_rate)
        if not sampled:
            continue
        payload = {sensor_name: {"type": sensor_type, "data": sampled}}
        client.send_event("DataUpdate", payload)
        if replay_sleep:
            time.sleep(1)


def watch_directory(
    watch_dir: Path,
    client: TcpBridgeClient,
    sensor_name: str,
    sensor_type: str,
    output_rate: int,
    poll_interval: float,
    replay_sleep: bool,
) -> None:
    processed: Set[Path] = set()
    while True:
        files = sorted(watch_dir.glob("*.csv"))
        for path in files:
            if path in processed:
                continue
            stream_file(
                client,
                path,
                sensor_name,
                sensor_type,
                output_rate,
                replay_sleep,
            )
            processed.add(path)
        time.sleep(poll_interval)


def main() -> None:
    args = parse_args()
    watch_dir = Path(args.watch_dir)
    if not watch_dir.exists():
        raise SystemExit(f"Watch directory not found: {watch_dir}")

    client = TcpBridgeClient(args.host, args.port, args.machine_name)
    try:
        client.connect()
        watch_directory(
            watch_dir=watch_dir,
            client=client,
            sensor_name=args.sensor_name,
            sensor_type=args.sensor_type,
            output_rate=args.output_rate,
            poll_interval=args.poll_interval,
            replay_sleep=args.replay_sleep,
        )
    finally:
        client.close()


if __name__ == "__main__":
    main()
