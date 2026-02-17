#!/usr/bin/env python3
"""기업 리서치 크롤러 - 취업 준비용 기업/직무 정보 자동 수집 CLI 도구"""

import argparse
import json
import os
import re
import time
from datetime import datetime
from urllib.parse import quote_plus, urljoin, urlparse

import requests
from bs4 import BeautifulSoup

# ─── 설정 ───────────────────────────────────────────────

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

REQUEST_DELAY = 1.5
REQUEST_TIMEOUT = 10
MAX_RESULTS = 5
MAX_CONTENT_LENGTH = 3000

REMOVE_TAGS = ["script", "style", "nav", "footer", "header", "aside", "iframe", "noscript"]


# ─── 유틸리티 ────────────────────────────────────────────

def safe_request(url, description=""):
    """안전한 HTTP 요청 - 에러 시 None 반환"""
    try:
        time.sleep(REQUEST_DELAY)
        resp = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        return resp
    except Exception as e:
        if description:
            print(f"  [SKIP] {description}: {e}")
        return None


def extract_text(html):
    """HTML에서 본문 텍스트만 추출"""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup.find_all(REMOVE_TAGS):
        tag.decompose()
    text = soup.get_text(separator="\n")
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    text = "\n".join(lines)
    if len(text) > MAX_CONTENT_LENGTH:
        text = text[:MAX_CONTENT_LENGTH] + "\n...(truncated)"
    return text


def print_section(title):
    """섹션 구분 출력"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def print_step(msg):
    """진행 상황 출력"""
    print(f"  >> {msg}")


# ─── 검색 엔진 ──────────────────────────────────────────

def search_google(query, num_results=MAX_RESULTS):
    """Google 검색으로 URL 목록 수집"""
    print_step(f"Google 검색: {query}")
    url = f"https://www.google.com/search?q={quote_plus(query)}&hl=ko&num={num_results}"
    resp = safe_request(url, "Google 검색")
    if not resp:
        return []
    soup = BeautifulSoup(resp.text, "html.parser")
    results = []
    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"]
        if href.startswith("/url?q="):
            real_url = href.split("/url?q=")[1].split("&")[0]
            if real_url.startswith("http") and "google.com" not in real_url:
                results.append(real_url)
                if len(results) >= num_results:
                    break
    return results


def search_naver_news(query, num_results=MAX_RESULTS):
    """네이버 뉴스 검색"""
    print_step(f"네이버 뉴스 검색: {query}")
    url = f"https://search.naver.com/search.naver?where=news&query={quote_plus(query)}"
    resp = safe_request(url, "네이버 뉴스 검색")
    if not resp:
        return []
    soup = BeautifulSoup(resp.text, "html.parser")
    results = []
    for a_tag in soup.select("a.news_tit"):
        href = a_tag.get("href", "")
        title = a_tag.get_text(strip=True)
        if href.startswith("http"):
            results.append({"title": title, "url": href})
            if len(results) >= num_results:
                break
    return results


def search_naver_blog(query, num_results=MAX_RESULTS):
    """네이버 블로그 검색"""
    print_step(f"네이버 블로그 검색: {query}")
    url = f"https://search.naver.com/search.naver?where=blog&query={quote_plus(query)}"
    resp = safe_request(url, "네이버 블로그 검색")
    if not resp:
        return []
    soup = BeautifulSoup(resp.text, "html.parser")
    results = []
    for a_tag in soup.select("a.api_txt_lines.total_tit"):
        href = a_tag.get("href", "")
        title = a_tag.get_text(strip=True)
        if href.startswith("http"):
            results.append({"title": title, "url": href})
            if len(results) >= num_results:
                break
    return results


def crawl_url(url, description=""):
    """URL 크롤링 후 본문 텍스트 추출"""
    resp = safe_request(url, description)
    if not resp:
        return ""
    try:
        return extract_text(resp.text)
    except Exception:
        return ""


def crawl_urls(urls, label=""):
    """URL 리스트 크롤링"""
    results = []
    for i, url in enumerate(urls):
        desc = f"{label} ({i+1}/{len(urls)})" if label else ""
        print_step(f"크롤링 중: {url[:80]}...")
        text = crawl_url(url, desc)
        if text:
            results.append({"url": url, "content": text})
    return results


def crawl_news_items(items, label=""):
    """뉴스/블로그 아이템 크롤링"""
    results = []
    for i, item in enumerate(items):
        desc = f"{label} ({i+1}/{len(items)})"
        print_step(f"크롤링 중: {item['title'][:50]}...")
        text = crawl_url(item["url"], desc)
        results.append({
            "title": item["title"],
            "url": item["url"],
            "content": text if text else "(본문 추출 실패)",
        })
    return results


# ─── Part 1: 그룹 전반 수집 ──────────────────────────────

def collect_group_overview(group):
    """그룹 개요, 사업영역, 비전, 핵심가치"""
    print_section(f"[Part 1] {group} 그룹 개요 수집")
    urls = search_google(f"{group} 그룹 개요 사업영역 비전 핵심가치")
    data = crawl_urls(urls, "그룹 개요")
    return data


def collect_group_news(group):
    """그룹 최근 뉴스"""
    print_section(f"[Part 1] {group} 그룹 최근 뉴스 수집")
    items = search_naver_news(f"{group} 그룹")
    data = crawl_news_items(items, "그룹 뉴스")
    return data


def collect_group_culture(group):
    """기업문화, 근무환경, 분위기"""
    print_section(f"[Part 1] {group} 그룹 기업문화 수집")
    items = search_naver_blog(f"{group} 그룹 기업문화 근무환경 후기")
    data = crawl_news_items(items, "기업문화")
    return data


def collect_group_finance(group):
    """재무 실적, 매출 정보"""
    print_section(f"[Part 1] {group} 그룹 재무 실적 수집")
    urls = search_google(f"{group} 그룹 매출 실적 재무")
    data = crawl_urls(urls, "재무 실적")
    return data


# ─── Part 2: 계열사 직무 수집 ────────────────────────────

def collect_subsidiary_overview(subsidiary):
    """계열사 회사 개요"""
    print_section(f"[Part 2] {subsidiary} 회사 개요 수집")
    urls = search_google(f"{subsidiary} 회사 개요 사업 소개")
    data = crawl_urls(urls, "계열사 개요")
    return data


def collect_job_info(subsidiary, job):
    """직무 소개, 하는 일, 업무내용"""
    print_section(f"[Part 2] {subsidiary} {job} 직무 정보 수집")
    urls = search_google(f"{subsidiary} {job} 직무 소개 업무내용 하는일")
    data = crawl_urls(urls, "직무 정보")
    return data


def collect_job_news(subsidiary, job):
    """관련 뉴스"""
    print_section(f"[Part 2] {subsidiary} {job} 관련 뉴스 수집")
    items = search_naver_news(f"{subsidiary} {job}")
    data = crawl_news_items(items, "직무 뉴스")
    return data


def collect_job_postings(subsidiary, job):
    """채용 공고, 자격요건, 우대사항"""
    print_section(f"[Part 2] {subsidiary} {job} 채용 공고 수집")
    urls = search_google(f"{subsidiary} {job} 채용 공고 자격요건 우대사항")
    data = crawl_urls(urls, "채용 공고")
    return data


def collect_tech_stack(subsidiary, job):
    """기술스택, 필요 역량"""
    print_section(f"[Part 2] {subsidiary} {job} 기술스택 수집")
    urls = search_google(f"{subsidiary} {job} 기술스택 필요역량 자격요건")
    data = crawl_urls(urls, "기술스택")
    return data


def collect_interview_reviews(subsidiary, job):
    """면접 후기"""
    print_section(f"[Part 2] {subsidiary} {job} 면접 후기 수집")
    items = search_naver_blog(f"{subsidiary} {job} 면접 후기")
    data = crawl_news_items(items, "면접 후기")
    return data


# ─── 리포트 생성 ─────────────────────────────────────────

def format_items_md(items, section_title):
    """수집 데이터를 Markdown 형식으로 변환"""
    md = f"### {section_title}\n\n"
    if not items:
        md += "_수집된 데이터가 없습니다._\n\n"
        return md
    for i, item in enumerate(items, 1):
        if "title" in item:
            md += f"**{i}. {item['title']}**\n"
        if "url" in item:
            md += f"- 출처: {item['url']}\n"
        content = item.get("content", "")
        if content:
            preview = content[:500] + "..." if len(content) > 500 else content
            md += f"\n```\n{preview}\n```\n\n"
        md += "---\n\n"
    return md


def generate_markdown_report(group, subsidiary, job, data):
    """Markdown 리포트 생성"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    md = f"# 기업 리서치 리포트\n\n"
    md += f"- **생성일시**: {now}\n"
    md += f"- **그룹**: {group}\n"
    md += f"- **계열사**: {subsidiary}\n"
    md += f"- **직무**: {job}\n\n"
    md += "---\n\n"

    # Part 1
    md += "## Part 1. 그룹 전반 정보\n\n"
    md += format_items_md(data.get("group_overview", []), "그룹 개요 / 사업영역 / 비전 / 핵심가치")
    md += format_items_md(data.get("group_news", []), "최근 뉴스")
    md += format_items_md(data.get("group_culture", []), "기업문화 / 근무환경 / 분위기")
    md += format_items_md(data.get("group_finance", []), "재무 실적 / 매출 정보")

    # Part 2
    md += "## Part 2. 계열사 직무 정보\n\n"
    md += format_items_md(data.get("subsidiary_overview", []), "계열사 회사 개요")
    md += format_items_md(data.get("job_info", []), "직무 소개 / 하는 일 / 업무내용")
    md += format_items_md(data.get("job_news", []), "관련 뉴스")
    md += format_items_md(data.get("job_postings", []), "채용 공고 / 자격요건 / 우대사항")
    md += format_items_md(data.get("tech_stack", []), "기술스택 / 필요 역량")
    md += format_items_md(data.get("interview_reviews", []), "면접 후기")

    return md


# ─── 메인 ───────────────────────────────────────────────

def run_crawler(group, subsidiary, job, output_dir):
    """크롤러 실행"""
    print(f"\n{'#'*60}")
    print(f"  기업 리서치 크롤러 시작")
    print(f"  그룹: {group} | 계열사: {subsidiary} | 직무: {job}")
    print(f"{'#'*60}")

    data = {}

    # Part 1: 그룹 전반
    data["group_overview"] = collect_group_overview(group)
    data["group_news"] = collect_group_news(group)
    data["group_culture"] = collect_group_culture(group)
    data["group_finance"] = collect_group_finance(group)

    # Part 2: 계열사 직무
    data["subsidiary_overview"] = collect_subsidiary_overview(subsidiary)
    data["job_info"] = collect_job_info(subsidiary, job)
    data["job_news"] = collect_job_news(subsidiary, job)
    data["job_postings"] = collect_job_postings(subsidiary, job)
    data["tech_stack"] = collect_tech_stack(subsidiary, job)
    data["interview_reviews"] = collect_interview_reviews(subsidiary, job)

    # 출력 디렉토리 생성
    os.makedirs(output_dir, exist_ok=True)

    # 파일명 생성
    safe_name = f"{group}_{subsidiary}_{job}".replace(" ", "_")

    # JSON 원본 저장
    json_path = os.path.join(output_dir, f"{safe_name}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\n  [저장] JSON: {json_path}")

    # Markdown 리포트 저장
    md_content = generate_markdown_report(group, subsidiary, job, data)
    md_path = os.path.join(output_dir, f"{safe_name}.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)
    print(f"  [저장] Markdown: {md_path}")

    print(f"\n{'#'*60}")
    print(f"  크롤링 완료!")
    print(f"{'#'*60}\n")

    return data


def main():
    parser = argparse.ArgumentParser(
        description="기업 리서치 크롤러 - 취업 준비용 기업/직무 정보 자동 수집 도구"
    )
    parser.add_argument("--group", required=True, help="기업 그룹명 (예: 효성, LG, GS)")
    parser.add_argument("--subsidiary", required=True, help="계열사명 (예: 효성중공업)")
    parser.add_argument("--job", required=True, help="직무명 (예: AI플랫폼운영)")
    parser.add_argument("--output", default="research_output", help="출력 디렉토리 (기본: research_output/)")

    args = parser.parse_args()
    run_crawler(args.group, args.subsidiary, args.job, args.output)


if __name__ == "__main__":
    main()
