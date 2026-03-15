#!/usr/bin/env python3
"""기업 리서치 크롤러 - 웹 인터페이스"""

import json
import os
import queue
import threading
import uuid
from datetime import datetime

from flask import Flask, Response, jsonify, render_template, request, send_file

import crawler

app = Flask(__name__)

# 작업 상태 저장소
tasks = {}


class CrawlerTask:
    """크롤링 작업 관리"""

    def __init__(self, company, job):
        self.id = str(uuid.uuid4())
        self.company = company
        self.job = job
        self.status = "pending"  # pending, running, completed, error, cancelled
        self.progress = []
        self.queue = queue.Queue()
        self.data = None
        self.error = None
        self.cancelled = False
        self.created_at = datetime.now()

    def send_event(self, event_type, message, detail=""):
        self.progress.append({"type": event_type, "message": message, "detail": detail})
        self.queue.put({"type": event_type, "message": message, "detail": detail})


def patched_print_section(task, original_func):
    """print_section을 패치하여 웹으로 진행상황 전송"""

    def wrapper(title):
        task.send_event("section", title)
        original_func(title)

    return wrapper


def patched_print_step(task, original_func):
    """print_step을 패치하여 웹으로 진행상황 전송"""

    def wrapper(msg):
        task.send_event("step", msg)
        original_func(msg)

    return wrapper


def patched_safe_request(task, original_func):
    """safe_request를 패치하여 취소 지원"""

    def wrapper(url, description=""):
        if task.cancelled:
            return None
        return original_func(url, description)

    return wrapper


def run_crawler_task(task):
    """백그라운드에서 크롤러 실행"""
    try:
        task.status = "running"
        task.send_event("start", f"{task.company} / {task.job} 리서치 시작")

        # 진행상황 출력 함수를 패치
        orig_section = crawler.print_section
        orig_step = crawler.print_step
        orig_safe_request = crawler.safe_request
        crawler.print_section = patched_print_section(task, orig_section)
        crawler.print_step = patched_print_step(task, orig_step)
        crawler.safe_request = patched_safe_request(task, orig_safe_request)

        try:
            output_dir = "research_output"
            task.data = crawler.run_crawler(task.company, task.job, output_dir)

            if task.cancelled:
                task.status = "cancelled"
                task.send_event("error", "사용자에 의해 취소되었습니다.")
            else:
                task.status = "completed"
                total_items = sum(len(v) for v in task.data.values())
                task.send_event("complete", f"크롤링 완료! 총 {total_items}건 수집")
        finally:
            crawler.print_section = orig_section
            crawler.print_step = orig_step
            crawler.safe_request = orig_safe_request

    except Exception as e:
        task.status = "error"
        task.error = str(e)
        task.send_event("error", f"오류 발생: {e}")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/crawl", methods=["POST"])
def start_crawl():
    """크롤링 시작 API"""
    data = request.get_json()
    company = data.get("company", "").strip()
    job = data.get("job", "").strip()

    if not company or not job:
        return jsonify({"error": "회사명과 직무명을 모두 입력해주세요."}), 400

    task = CrawlerTask(company, job)
    tasks[task.id] = task

    thread = threading.Thread(target=run_crawler_task, args=(task,), daemon=True)
    thread.start()

    return jsonify({"task_id": task.id})


@app.route("/api/progress/<task_id>")
def stream_progress(task_id):
    """SSE로 진행상황 스트리밍"""
    task = tasks.get(task_id)
    if not task:
        return jsonify({"error": "작업을 찾을 수 없습니다."}), 404

    def generate():
        while True:
            try:
                event = task.queue.get(timeout=30)
                data = json.dumps(event, ensure_ascii=False)
                yield f"data: {data}\n\n"
                if event["type"] in ("complete", "error"):
                    break
            except queue.Empty:
                # 타임아웃 시 keep-alive 전송
                yield f"data: {json.dumps({'type': 'ping', 'message': ''})}\n\n"

    return Response(generate(), mimetype="text/event-stream")


@app.route("/api/cancel/<task_id>", methods=["POST"])
def cancel_crawl(task_id):
    """크롤링 취소 API"""
    task = tasks.get(task_id)
    if not task:
        return jsonify({"error": "작업을 찾을 수 없습니다."}), 404
    if task.status != "running":
        return jsonify({"error": "실행 중인 작업이 아닙니다."}), 400

    task.cancelled = True
    return jsonify({"ok": True})


@app.route("/api/result/<task_id>")
def get_result(task_id):
    """크롤링 결과 조회"""
    task = tasks.get(task_id)
    if not task:
        return jsonify({"error": "작업을 찾을 수 없습니다."}), 404
    if task.status != "completed":
        return jsonify({"error": "아직 완료되지 않았습니다.", "status": task.status}), 400

    # Markdown 리포트 생성
    md_content = crawler.generate_markdown_report(task.company, task.job, task.data)

    return jsonify({
        "company": task.company,
        "job": task.job,
        "data": task.data,
        "markdown": md_content,
        "total_items": sum(len(v) for v in task.data.values()),
    })


@app.route("/api/download/<task_id>/<file_type>")
def download_file(task_id, file_type):
    """파일 다운로드 (json 또는 md)"""
    task = tasks.get(task_id)
    if not task or task.status != "completed":
        return jsonify({"error": "결과를 찾을 수 없습니다."}), 404

    safe_name = f"{task.company}_{task.job}".replace(" ", "_")
    output_dir = "research_output"

    if file_type == "json":
        path = os.path.join(output_dir, f"{safe_name}.json")
        if os.path.exists(path):
            return send_file(path, as_attachment=True, download_name=f"{safe_name}.json")
    elif file_type == "md":
        path = os.path.join(output_dir, f"{safe_name}.md")
        if os.path.exists(path):
            return send_file(path, as_attachment=True, download_name=f"{safe_name}.md")

    return jsonify({"error": "파일을 찾을 수 없습니다."}), 404


@app.route("/api/history")
def get_history():
    """이전 리서치 결과 목록"""
    output_dir = "research_output"
    if not os.path.exists(output_dir):
        return jsonify([])

    results = []
    for f in sorted(os.listdir(output_dir), reverse=True):
        if f.endswith(".json"):
            name = f.replace(".json", "")
            parts = name.split("_", 1)
            if len(parts) == 2:
                filepath = os.path.join(output_dir, f)
                mtime = os.path.getmtime(filepath)
                results.append({
                    "company": parts[0],
                    "job": parts[1],
                    "filename": name,
                    "date": datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M"),
                })
    return jsonify(results)


@app.route("/api/history/<filename>")
def get_history_detail(filename):
    """이전 리서치 결과 상세 조회"""
    output_dir = "research_output"
    json_path = os.path.join(output_dir, f"{filename}.json")
    md_path = os.path.join(output_dir, f"{filename}.md")

    if not os.path.exists(json_path):
        return jsonify({"error": "결과를 찾을 수 없습니다."}), 404

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    md_content = ""
    if os.path.exists(md_path):
        with open(md_path, "r", encoding="utf-8") as f:
            md_content = f.read()

    parts = filename.split("_", 1)
    return jsonify({
        "company": parts[0] if len(parts) >= 1 else "",
        "job": parts[1] if len(parts) >= 2 else "",
        "data": data,
        "markdown": md_content,
        "total_items": sum(len(v) for v in data.values()),
    })


@app.route("/api/compare", methods=["POST"])
def compare_results():
    """두 리서치 결과 비교"""
    data = request.get_json()
    files = data.get("files", [])
    if len(files) != 2:
        return jsonify({"error": "비교할 파일 2개를 선택해주세요."}), 400

    output_dir = "research_output"
    results = []
    for filename in files:
        json_path = os.path.join(output_dir, f"{filename}.json")
        if not os.path.exists(json_path):
            return jsonify({"error": f"{filename} 파일을 찾을 수 없습니다."}), 404
        with open(json_path, "r", encoding="utf-8") as f:
            file_data = json.load(f)
        parts = filename.split("_", 1)
        results.append({
            "company": parts[0] if len(parts) >= 1 else "",
            "job": parts[1] if len(parts) >= 2 else "",
            "data": file_data,
            "total_items": sum(len(v) for v in file_data.values()),
        })
    return jsonify(results)


@app.route("/api/history/<filename>", methods=["DELETE"])
def delete_history(filename):
    """리서치 기록 삭제"""
    output_dir = "research_output"
    deleted = False
    for ext in (".json", ".md"):
        path = os.path.join(output_dir, f"{filename}{ext}")
        if os.path.exists(path):
            os.remove(path)
            deleted = True
    if not deleted:
        return jsonify({"error": "파일을 찾을 수 없습니다."}), 404
    return jsonify({"ok": True})


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
