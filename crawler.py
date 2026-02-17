#!/usr/bin/env python3
"""기업 리서치 크롤러 - 취업 준비용 기업/직무 정보 자동 수집 CLI 도구"""

import argparse
import json
import os
import re
import time
from datetime import datetime, timedelta
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

# 주요 채용 사이트 URL 템플릿
JOB_SITES = {
    "사람인": "https://www.saramin.co.kr/zf_user/search?searchType=search&searchword={query}",
    "잡코리아": "https://www.jobkorea.co.kr/Search/?stext={query}",
    "원티드": "https://www.wanted.co.kr/search?query={query}",
    "링크드인": "https://www.linkedin.com/jobs/search/?keywords={query}&location=South+Korea",
}


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


def get_date_range(days=7):
    """최근 N일 기간의 시작/종료 날짜 반환 (YYYY.MM.DD 형식)"""
    today = datetime.now()
    start = today - timedelta(days=days)
    return start.strftime("%Y.%m.%d"), today.strftime("%Y.%m.%d")


def get_current_year():
    """현재 연도 반환"""
    return datetime.now().strftime("%Y")


# ─── 검색 엔진 ──────────────────────────────────────────

def search_google(query, num_results=MAX_RESULTS, recent=False):
    """Google 검색으로 URL 목록 수집

    Args:
        query: 검색어
        num_results: 최대 결과 수
        recent: True이면 최근 1개월 결과만 필터링
    """
    print_step(f"Google 검색: {query}")
    url = f"https://www.google.com/search?q={quote_plus(query)}&hl=ko&num={num_results}"
    if recent:
        url += "&tbs=qdr:m"
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


def search_naver_news(query, num_results=MAX_RESULTS, recent_days=7):
    """네이버 뉴스 검색 (최신순, 날짜 필터링)

    Args:
        query: 검색어
        num_results: 최대 결과 수
        recent_days: 최근 N일 이내 뉴스만 검색 (0이면 필터링 없음)
    """
    print_step(f"네이버 뉴스 검색: {query}")
    url = f"https://search.naver.com/search.naver?where=news&query={quote_plus(query)}"
    # 최신순 정렬 + 날짜 필터링
    url += "&sort=1"  # 최신순
    if recent_days > 0:
        ds, de = get_date_range(recent_days)
        url += f"&pd=4&ds={ds}&de={de}"
    resp = safe_request(url, "네이버 뉴스 검색")
    if not resp:
        return []
    soup = BeautifulSoup(resp.text, "html.parser")
    results = []
    # 뉴스 아이템 파싱
    news_items = soup.select("div.news_area, li.bx")
    for item in news_items:
        a_tag = item.select_one("a.news_tit")
        if not a_tag:
            continue
        href = a_tag.get("href", "")
        title = a_tag.get_text(strip=True)
        if not href.startswith("http"):
            continue
        # 날짜 정보 추출 시도
        date_text = ""
        info_spans = item.select("span.info")
        for span in info_spans:
            text = span.get_text(strip=True)
            # 날짜 패턴 매칭 (예: "1일 전", "2025.12.01.", "3시간 전")
            if re.search(r'\d', text) and not text.startswith("언론사"):
                date_text = text
                break
        result = {"title": title, "url": href}
        if date_text:
            result["date"] = date_text
        results.append(result)
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
        result = {
            "title": item["title"],
            "url": item["url"],
            "content": text if text else "(본문 추출 실패)",
        }
        if "date" in item:
            result["date"] = item["date"]
        results.append(result)
    return results


# ─── Part 1: 회사 전반 수집 ──────────────────────────────

def collect_company_overview(company):
    """회사 개요, 사업영역, 비전, 핵심가치"""
    print_section(f"[Part 1] {company} 회사 개요 수집")
    urls = search_google(f"{company} 회사 개요 사업영역 비전 핵심가치 주요사업")
    data = crawl_urls(urls, "회사 개요")
    return data


def collect_company_news(company):
    """회사 최근 뉴스 (최신순, 최근 1주일)"""
    print_section(f"[Part 1] {company} 최근 뉴스 수집")
    items = search_naver_news(f"{company}", recent_days=7)
    data = crawl_news_items(items, "회사 뉴스")
    return data


def collect_company_culture(company):
    """기업문화, 근무환경, 복지, 분위기"""
    print_section(f"[Part 1] {company} 기업문화 수집")
    items = search_naver_blog(f"{company} 기업문화 근무환경 복지 후기 워라밸")
    data = crawl_news_items(items, "기업문화")
    return data


def collect_company_finance(company):
    """재무 실적, 매출, 영업이익 정보"""
    print_section(f"[Part 1] {company} 재무 실적 수집")
    year = get_current_year()
    urls = search_google(f"{company} 매출 실적 재무 영업이익 {year}")
    data = crawl_urls(urls, "재무 실적")
    return data


def collect_company_industry(company):
    """산업 동향, 경쟁사, 시장 전망"""
    print_section(f"[Part 1] {company} 산업 동향 수집")
    urls = search_google(f"{company} 산업 동향 경쟁사 시장 점유율 전망")
    data = crawl_urls(urls, "산업 동향")
    return data


def collect_company_recent(company):
    """최근 이슈: 신사업, 프로젝트, 투자, 협력 (최근 1개월)"""
    print_section(f"[Part 1] {company} 최근 이슈 수집")
    year = get_current_year()
    urls = search_google(
        f"{company} 신사업 프로젝트 투자 협력 MOU {year}",
        recent=True,
    )
    data = crawl_urls(urls, "최근 이슈")
    # 네이버 뉴스에서도 최근 이슈 보강
    items = search_naver_news(f"{company} 신사업 투자 협력", recent_days=30)
    news_data = crawl_news_items(items, "최근 이슈 뉴스")
    return data + news_data


# ─── Part 2: 직무 정보 수집 ──────────────────────────────

def collect_job_info(company, job):
    """직무 소개, 하는 일, 업무내용"""
    print_section(f"[Part 2] {company} {job} 직무 정보 수집")
    urls = search_google(f"{company} {job} 직무 소개 업무내용 하는일 역할")
    data = crawl_urls(urls, "직무 정보")
    return data


def collect_job_news(company, job):
    """직무 관련 최신 뉴스"""
    print_section(f"[Part 2] {company} {job} 관련 뉴스 수집")
    items = search_naver_news(f"{company} {job}", recent_days=30)
    data = crawl_news_items(items, "직무 뉴스")
    return data


def collect_job_postings(company, job):
    """채용 공고, 자격요건, 우대사항"""
    print_section(f"[Part 2] {company} {job} 채용 공고 수집")
    year = get_current_year()
    urls = search_google(f"{company} {job} 채용 공고 자격요건 우대사항 {year}")
    data = crawl_urls(urls, "채용 공고")
    return data


def collect_tech_stack(company, job):
    """기술스택, 필요 역량"""
    print_section(f"[Part 2] {company} {job} 기술스택 수집")
    urls = search_google(f"{company} {job} 기술스택 필요역량 자격요건 툴")
    data = crawl_urls(urls, "기술스택")
    return data


def collect_interview_reviews(company, job):
    """면접 후기, 면접 질문"""
    print_section(f"[Part 2] {company} {job} 면접 후기 수집")
    items = search_naver_blog(f"{company} {job} 면접 후기 질문 면접경험")
    data = crawl_news_items(items, "면접 후기")
    return data


def collect_salary_benefits(company, job):
    """연봉, 복지, 처우, 워라밸 정보"""
    print_section(f"[Part 2] {company} {job} 연봉/복지 수집")
    items = search_naver_blog(f"{company} {job} 연봉 복지 처우 워라밸 현직자")
    data = crawl_news_items(items, "연봉/복지")
    return data


def collect_career_page(company):
    """회사 공식 채용 페이지 검색"""
    print_section(f"[Part 2] {company} 공식 채용 페이지 검색")
    urls = search_google(f"{company} 채용 홈페이지 careers 공식 채용사이트")
    data = crawl_urls(urls, "채용 페이지")
    return data


def collect_job_posting_links(company, job):
    """주요 채용 사이트 직접 링크 생성 및 Google 검색 보강"""
    print_section(f"[Part 3] {company} {job} 채용 사이트 링크 수집")

    query = f"{company} {job}"
    results = []

    # 1. 주요 채용 사이트 직접 URL 생성
    for site_name, url_template in JOB_SITES.items():
        site_url = url_template.format(query=quote_plus(query))
        print_step(f"{site_name} 링크 생성: {site_url[:80]}...")
        results.append({
            "title": f"{site_name} - {company} {job} 검색",
            "url": site_url,
            "content": f"{site_name}에서 '{company} {job}' 검색 결과 페이지입니다. 링크를 클릭하여 최신 채용공고를 확인하세요.",
        })

    # 2. Google 검색으로 채용 사이트 내 공고 직접 탐색
    year = get_current_year()
    site_urls = search_google(
        f"{company} {job} 채용 {year} site:saramin.co.kr OR site:jobkorea.co.kr OR site:wanted.co.kr"
    )
    for url in site_urls:
        print_step(f"채용공고 크롤링: {url[:80]}...")
        text = crawl_url(url, "채용 사이트 공고")
        if text:
            # URL에서 사이트 이름 추출
            domain = urlparse(url).netloc
            results.append({
                "title": f"[{domain}] 채용 공고",
                "url": url,
                "content": text,
            })

    return results


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
        if "date" in item:
            md += f"- 날짜: {item['date']}\n"
        if "url" in item:
            md += f"- 출처: {item['url']}\n"
        content = item.get("content", "")
        if content:
            preview = content[:500] + "..." if len(content) > 500 else content
            md += f"\n```\n{preview}\n```\n\n"
        md += "---\n\n"
    return md


def format_links_md(items, section_title):
    """채용 링크 목록을 Markdown 형식으로 변환"""
    md = f"### {section_title}\n\n"
    if not items:
        md += "_수집된 링크가 없습니다._\n\n"
        return md
    for i, item in enumerate(items, 1):
        title = item.get("title", "링크")
        url = item.get("url", "")
        md += f"**{i}. [{title}]({url})**\n"
        content = item.get("content", "")
        if content and not content.startswith(("사람인에서", "잡코리아에서", "원티드에서", "링크드인에서")):
            preview = content[:300] + "..." if len(content) > 300 else content
            md += f"\n```\n{preview}\n```\n\n"
        else:
            md += f"- {content}\n\n"
        md += "---\n\n"
    return md


def generate_markdown_report(company, job, data):
    """Markdown 리포트 생성"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    ds, de = get_date_range(7)

    md = f"# 기업 리서치 리포트\n\n"
    md += f"- **생성일시**: {now}\n"
    md += f"- **회사**: {company}\n"
    md += f"- **직무**: {job}\n"
    md += f"- **뉴스 기준**: 최근 1주일 ({ds} ~ {de})\n\n"
    md += "---\n\n"

    # Part 1: 회사 전반 정보
    md += "## Part 1. 회사 전반 정보\n\n"
    md += format_items_md(data.get("company_overview", []), "회사 개요 / 사업영역 / 비전 / 핵심가치")
    md += format_items_md(data.get("company_news", []), "최근 뉴스 (최근 1주일)")
    md += format_items_md(data.get("company_culture", []), "기업문화 / 근무환경 / 복지")
    md += format_items_md(data.get("company_finance", []), "재무 실적 / 매출 / 영업이익")
    md += format_items_md(data.get("company_industry", []), "산업 동향 / 경쟁사 / 시장 전망")
    md += format_items_md(data.get("company_recent", []), "최근 이슈 / 신사업 / 투자 / 협력")

    # Part 2: 직무 정보
    md += "## Part 2. 직무 정보\n\n"
    md += format_items_md(data.get("job_info", []), "직무 소개 / 하는 일 / 업무내용")
    md += format_items_md(data.get("job_news", []), "직무 관련 뉴스")
    md += format_items_md(data.get("job_postings", []), "채용 공고 / 자격요건 / 우대사항")
    md += format_items_md(data.get("tech_stack", []), "기술스택 / 필요 역량")
    md += format_items_md(data.get("interview_reviews", []), "면접 후기 / 면접 질문")
    md += format_items_md(data.get("salary_benefits", []), "연봉 / 복지 / 처우")
    md += format_items_md(data.get("career_page", []), "공식 채용 페이지")

    # Part 3: 채용공고 바로가기
    md += "## Part 3. 채용공고 바로가기\n\n"
    md += "> 아래 링크를 클릭하면 각 채용 사이트에서 해당 회사/직무의 채용공고를 바로 확인할 수 있습니다.\n\n"
    md += format_links_md(data.get("job_posting_links", []), "채용 사이트 검색 링크")

    return md


# ─── 메인 ───────────────────────────────────────────────

def run_crawler(company, job, output_dir):
    """크롤러 실행"""
    print(f"\n{'#'*60}")
    print(f"  기업 리서치 크롤러 시작")
    print(f"  회사: {company} | 직무: {job}")
    print(f"  날짜: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'#'*60}")

    data = {}

    # Part 1: 회사 전반
    data["company_overview"] = collect_company_overview(company)
    data["company_news"] = collect_company_news(company)
    data["company_culture"] = collect_company_culture(company)
    data["company_finance"] = collect_company_finance(company)
    data["company_industry"] = collect_company_industry(company)
    data["company_recent"] = collect_company_recent(company)

    # Part 2: 직무 정보
    data["job_info"] = collect_job_info(company, job)
    data["job_news"] = collect_job_news(company, job)
    data["job_postings"] = collect_job_postings(company, job)
    data["tech_stack"] = collect_tech_stack(company, job)
    data["interview_reviews"] = collect_interview_reviews(company, job)
    data["salary_benefits"] = collect_salary_benefits(company, job)
    data["career_page"] = collect_career_page(company)

    # Part 3: 채용공고 바로가기
    data["job_posting_links"] = collect_job_posting_links(company, job)

    # 출력 디렉토리 생성
    os.makedirs(output_dir, exist_ok=True)

    # 파일명 생성
    safe_name = f"{company}_{job}".replace(" ", "_")

    # JSON 원본 저장
    json_path = os.path.join(output_dir, f"{safe_name}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\n  [저장] JSON: {json_path}")

    # Markdown 리포트 저장
    md_content = generate_markdown_report(company, job, data)
    md_path = os.path.join(output_dir, f"{safe_name}.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)
    print(f"  [저장] Markdown: {md_path}")

    print(f"\n{'#'*60}")
    print(f"  크롤링 완료!")
    print(f"  수집 항목: {sum(len(v) for v in data.values())}건")
    print(f"{'#'*60}\n")

    return data


def main():
    parser = argparse.ArgumentParser(
        description="기업 리서치 크롤러 - 취업 준비용 기업/직무 정보 자동 수집 도구",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  python crawler.py --company "GS네오텍" --job "백엔드개발"
  python crawler.py --company "삼성전자" --job "SW개발" --output ./results
  python crawler.py --company "LG에너지솔루션" --job "데이터분석"
        """,
    )
    parser.add_argument("--company", required=True, help="회사명 (예: GS네오텍, 삼성전자, LG에너지솔루션)")
    parser.add_argument("--job", required=True, help="직무명 (예: 백엔드개발, AI엔지니어, 데이터분석)")
    parser.add_argument("--output", default="research_output", help="출력 디렉토리 (기본: research_output/)")

    args = parser.parse_args()
    run_crawler(args.company, args.job, args.output)


if __name__ == "__main__":
    main()
