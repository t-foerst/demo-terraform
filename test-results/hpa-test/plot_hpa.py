#!/usr/bin/env python3
"""
Parst eine kombinierte Log-Datei (combined-log.txt), erzeugt via:

  DB_ID="<deine-db-instance-id>"
  NS="demo-app-manual"
  HPA_NAME="demo-app"

  while true; do
    TS=$(date -u '+%Y-%m-%d %H:%M:%S')
    HPA_LINE=$(kubectl get hpa $HPA_NAME -n $NS --no-headers)
    DB_VAL=$(aws cloudwatch get-metric-statistics \
      --namespace AWS/RDS \
      --metric-name CPUUtilization \
      --dimensions Name=DBInstanceIdentifier,Value=$DB_ID \
      --start-time "$(date -u -d '-5 min' +%Y-%m-%dT%H:%M:%SZ)" \
      --end-time "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
      --period 60 \
      --statistics Average \
      --query 'sort_by(Datapoints,&Timestamp)[-1].Average' \
      --output text)
    echo "$TS $HPA_LINE DBCPU=$DB_VAL" >> combined-log.txt
    sleep 5
  done

Jede Zeile sieht dann so aus:
  2026-08-05 17:00:00 demo-app   Deployment/demo-app   cpu: 139%/70%   2   4   4   40m DBCPU=45.7

Erzeugt:
  - hpa-log.png: Liniendiagramm App-CPU% + Replicas + DB-CPU% über Zeit
  - hpa-data.csv: strukturierte Daten (Tabelle) als Fallback/Anhang
  - Konsolen-Ausgabe: Zeit bis zum ersten Scale-Up

Usage:
  python3 plot_hpa.py combined-log.txt [--out-dir .]
"""

import re
import sys
import csv
import argparse
from datetime import datetime

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

LINE_RE = re.compile(
    r"^(?P<ts>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s+"
    r".*?cpu:\s*(?P<cur>\d+)%/(?P<target>\d+)%\s+"
    r"(?P<minp>\d+)\s+(?P<maxp>\d+)\s+(?P<replicas>\d+)\s+\S+\s+"
    r"DBCPU=(?P<dbcpu>[\d.]+|None)\s*$"
)


def parse(path):
    rows = []
    skipped = 0
    with open(path, "r") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line.strip():
                continue
            m = LINE_RE.match(line)
            if not m:
                # Zeile ohne gueltige Metrik (z.B. HPA-Metrics-Server-Aussetzer) -> ueberspringen
                skipped += 1
                continue
            dbcpu_raw = m.group("dbcpu")
            rows.append(
                {
                    "ts": datetime.strptime(m.group("ts"), "%Y-%m-%d %H:%M:%S"),
                    "cpu": int(m.group("cur")),
                    "target": int(m.group("target")),
                    "replicas": int(m.group("replicas")),
                    "dbcpu": float(dbcpu_raw) if dbcpu_raw != "None" else None,
                }
            )
    if not rows:
        sys.exit("Keine gueltigen Zeilen im Log gefunden. Format pruefen.")
    if skipped:
        print(f"Hinweis: {skipped} Zeile(n) uebersprungen (kein gueltiges Format).")
    rows.sort(key=lambda r: r["ts"])
    t0 = rows[0]["ts"]
    for r in rows:
        r["rel_s"] = (r["ts"] - t0).total_seconds()
    return rows


def find_first_scaleup(rows):
    baseline = rows[0]["replicas"]
    for r in rows:
        if r["replicas"] > baseline:
            return r["rel_s"], baseline, r["replicas"]
    return None


def write_csv(rows, out_path):
    with open(out_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Zeit (relativ)", "Timestamp", "App-CPU (%)", "Target (%)", "Pods", "DB-CPU (%)"])
        for r in rows:
            mm = int(r["rel_s"] // 60)
            ss = int(r["rel_s"] % 60)
            w.writerow(
                [
                    f"{mm}:{ss:02d}",
                    r["ts"].strftime("%H:%M:%S"),
                    r["cpu"],
                    r["target"],
                    r["replicas"],
                    r["dbcpu"] if r["dbcpu"] is not None else "",
                ]
            )


def plot(rows, out_path, scaleup_info):
    times_min = [r["rel_s"] / 60 for r in rows]
    cpu = [r["cpu"] for r in rows]
    replicas = [r["replicas"] for r in rows]
    target = rows[0]["target"]

    # DB-Werte: None-Luecken rausfiltern (eigene x/y-Listen)
    db_times = [r["rel_s"] / 60 for r in rows if r["dbcpu"] is not None]
    db_vals = [r["dbcpu"] for r in rows if r["dbcpu"] is not None]

    fig, ax1 = plt.subplots(figsize=(10, 5.5))

    ax1.set_xlabel("Zeit seit Testbeginn (Minuten)")
    ax1.set_ylabel("App-CPU-Auslastung (%)", color="tab:red")
    ax1.plot(times_min, cpu, color="tab:red", label="App-CPU-Auslastung")
    ax1.axhline(target, color="tab:red", linestyle="--", alpha=0.4, label=f"Target ({target}%)")
    ax1.tick_params(axis="y", labelcolor="tab:red")

    ax2 = ax1.twinx()
    ax2.set_ylabel("Anzahl Pods (Replicas)", color="tab:blue")
    ax2.step(times_min, replicas, color="tab:blue", where="post", linewidth=2, label="Replicas")
    ax2.tick_params(axis="y", labelcolor="tab:blue")
    ax2.set_ylim(0, max(replicas) + 1)

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    all_lines, all_labels = lines1 + lines2, labels1 + labels2

    if db_vals:
        ax3 = ax1.twinx()
        ax3.spines["right"].set_position(("outward", 60))
        ax3.set_ylabel("DB-CPU (RDS, %)", color="tab:green")
        ax3.set_ylim(0, 100)
        (line3,) = ax3.plot(db_times, db_vals, color="tab:green", label="DB-CPU (RDS)")
        ax3.tick_params(axis="y", labelcolor="tab:green")
        all_lines.append(line3)
        all_labels.append("DB-CPU (RDS)")

    if scaleup_info:
        rel_s, before, after = scaleup_info
        ax1.axvline(rel_s / 60, color="black", linestyle=":", alpha=0.7)
        ax1.text(
            rel_s / 60,
            max(cpu) * 0.95 if cpu else 90,
            f" erster Scale-Up\n ({int(rel_s)}s)",
            color="black",
            fontsize=8,
        )

    ax1.legend(all_lines, all_labels, loc="upper right")
    plt.title("HPA-Verlauf: App-CPU, Pod-Anzahl und DB-Last über Zeit")
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    print(f"Diagramm gespeichert: {out_path}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("log_file")
    ap.add_argument("--out-dir", default=".")
    args = ap.parse_args()

    rows = parse(args.log_file)
    scaleup_info = find_first_scaleup(rows)

    csv_path = f"{args.out_dir}/hpa-data.csv"
    png_path = f"{args.out_dir}/hpa-log.png"
    write_csv(rows, csv_path)
    plot(rows, png_path, scaleup_info)

    print(f"CSV gespeichert: {csv_path}")
    print(f"Erste Log-Zeile: {rows[0]['ts']} (rel 0:00), Replicas={rows[0]['replicas']}, CPU={rows[0]['cpu']}%")
    print(f"Letzte Log-Zeile: {rows[-1]['ts']}, Replicas={rows[-1]['replicas']}, CPU={rows[-1]['cpu']}%")

    if scaleup_info:
        rel_s, before, after = scaleup_info
        mm, ss = int(rel_s // 60), int(rel_s % 60)
        print(
            f"\n>>> Zeit bis zum ersten Scale-Up: {int(rel_s)} Sekunden ({mm}:{ss:02d} min) "
            f"— Pods von {before} auf {after} erhöht."
        )
    else:
        print("\n>>> Kein Scale-Up im Log gefunden (Replica-Anzahl blieb konstant).")


if __name__ == "__main__":
    main()
