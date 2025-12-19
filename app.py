import os
import subprocess
import time
import statistics
import tempfile
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

UPLOAD_FOLDER = "/tmp/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Добавили SHA-512 для наглядности (самый "тяжелый" из стандартных)
ALGORITHMS = {
    "MD5": "md5sum",
    "SHA-1": "sha1sum",
    "SHA-256": "sha256sum",
    "SHA-512": "sha512sum",
}


def run_hashing(algo_command, filepath):
    start_time = time.perf_counter()
    result = subprocess.run(
        [algo_command, filepath], capture_output=True, text=True, check=True
    )
    end_time = time.perf_counter()
    # Возвращаем время в миллисекундах сразу
    duration_ms = (end_time - start_time) * 1000
    hash_output = result.stdout.split()[0]
    return duration_ms, hash_output


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/benchmark", methods=["POST"])
def benchmark():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    iterations = int(request.form.get("iterations", 10))

    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    with tempfile.NamedTemporaryFile(delete=False, dir=UPLOAD_FOLDER) as tmp:
        file.save(tmp.name)
        tmp_path = tmp.name

    try:
        results = {}
        file_size = os.path.getsize(tmp_path) / (1024 * 1024)

        for algo_name, command in ALGORITHMS.items():
            raw_times = []  # Список для хранения времени каждой итерации
            last_hash = ""

            # Прогрев (опционально, чтобы первый запуск не выбивался из-за загрузки бинарника)
            subprocess.run([command, tmp_path], capture_output=True)

            for _ in range(iterations):
                duration, h_val = run_hashing(command, tmp_path)
                raw_times.append(round(duration, 4))
                last_hash = h_val

            avg_time = statistics.mean(raw_times)

            results[algo_name] = {
                "avg_time_ms": round(avg_time, 4),
                "raw_times": raw_times,  # Отправляем массив точек на фронт
                "hash": last_hash,
                "hash_length": len(last_hash) * 4,
            }

        return jsonify(
            {
                "file_size_mb": round(file_size, 4),
                "results": results,
                "iterations_count": iterations,
            }
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
