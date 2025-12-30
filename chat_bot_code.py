import requests
from bs4 import BeautifulSoup
from datetime import datetime
import psycopg2
import logging
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
import chromadb
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
from openai import OpenAI
import gradio as gr
import re

# -------------------- OpenAI 설정 --------------------
client = OpenAI(api_key="")
embedding_function = OpenAIEmbeddingFunction(api_key=client.api_key, model_name="text-embedding-3-small")

# ✅ ChromaDB Persistent 설정 (신규 방식)
chroma_client = chromadb.PersistentClient(path="./chroma_db")

collection = chroma_client.get_or_create_collection(
    name="cu-notices",
    embedding_function=embedding_function
)

# -------------------- 교수명 추출 --------------------
def extract_professor_name(user_query):
    cleaned = re.sub(r"(교수님|교수|관련|정보|알려줘|알려주세요|찾아줘|에 대해 알려줘|에 관해 알려줘|에 관해서 알려줘)", "", user_query)
    return cleaned.strip()

# -------------------- GPT 질문 처리 --------------------
def simplify_query(query):
    stop_phrases = ["관련", "공지", "정보", "알려줘", "알려주세요", "에 대해", "에 관해", "에 관한", "찾아줘", "검색"]
    for phrase in stop_phrases:
        query = query.replace(phrase, "")
    return query.strip()

def generate_gpt_reply(user_query):
    simplified_query = simplify_query(user_query)

    try:
        results = collection.query(query_texts=[simplified_query], n_results=20)
        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
    except Exception as e:
        logging.error(f"ChromaDB 쿼리 실패: {e}")
        return "❌ 정보 검색 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요."

    if not docs:
        return "관련된 정보를 찾지 못했습니다. 다른 질문을 입력해 주세요."

    core_keywords = [
        "대구가톨릭대학교", "DCU",
        "장학금", "등록금", "휴학", "졸업", "강의실", "도서관", "시험",
        "스쿨버스", "셔틀버스", "통학버스", "버스 운행", "버스 안내",
        "채용", "강의", "입학", "성적", "면접", "취업"
    ]

    professor_keywords = ["교수", "교수님"]

    normal_results = []
    professor_results = []

    for doc, meta in zip(docs, metas):
        source = meta.get("source", "")

        # 교수 정보 따로 저장
        if source == "professor":
            professor_results.append(doc)
            continue

        # 일반 공지 필터링
        if any(k in doc.lower() for k in core_keywords):
            link = meta.get("link")
            normal_results.append(f"{doc}\n(링크: {link})" if link else doc)

    # 취업일 경우 외부 안내 포함
    if "취업" in user_query:
        external_info = (
            "또한, 외부 취업정보를 확인할 수 있는 사이트는 다음과 같습니다:\n"
            "- 사람인: https://www.saramin.co.kr\n"
            "- 잡코리아: https://www.jobkorea.co.kr"
        )
        if not normal_results:
            return f"내부 공지사항에서는 관련된 취업 정보를 찾지 못했습니다.\n\n{external_info}"
        else:
            return f"📢 내부 공지사항의 취업 관련 정보입니다:\n\n" + "\n\n".join(normal_results) + "\n\n" + external_info

    # 교수 질문일 때만 교수정보 출력
    if any(k in user_query for k in professor_keywords):
        if professor_results:
            return "\n\n".join(professor_results)
        else:
            return "해당 교수님에 대한 정보를 찾을 수 없습니다."

    # 일반 질문 결과
    if normal_results:
        context = "\n".join(normal_results)
        prompt = (
            f"학생이 '{user_query}' 라고 물었습니다. 아래는 대구가톨릭대학교(DCU) 관련 정보입니다:\n\n"
            f"{context}\n\n"
            f"이 정보를 바탕으로 학생에게 한국어로 친절하게 답변해줘."
        )

        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "너는 대학교 정보를 안내하는 챗봇이야. 질문에 대해 데이터베이스 정보를 바탕으로 한국어로 대답해."},
                    {"role": "user", "content": prompt}
                ]
            )
            return response.choices[0].message.content

        except Exception as e:
            logging.error(f"OpenAI 응답 오류: {e}")
            return "GPT 응답 생성 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요."

    return "관련된 정보를 찾지 못했습니다. 다른 질문을 입력해 주세요."


# -------------------- LOG 설정 --------------------
logging.basicConfig(
    filename="crawler.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

# -------------------- PostgreSQL 저장 + 벡터 저장 --------------------
def save_to_postgres(data):
    conn = psycopg2.connect(
        dbname="",
        user="",
        password="",
        host="",
        port=
    )
    cur = conn.cursor()
    new_count = 0

    for row in data:
        try:
            cur.execute("""
                INSERT INTO notices (timestamp, source, title, link)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (link) DO NOTHING
            """, row)
            new_count += 1

            title, link, source = row[2], row[3], row[1]
            doc_id = link
            content = f"[{source}] {title}"
            collection.add(
                documents=[content],
                metadatas=[{"source": source, "link": link}],
                ids=[doc_id]
            )

        except Exception as e:
            logging.error(f"INSERT 실패: {e}")
            continue

    conn.commit()

    try:
        cur.execute("SELECT name, office, phone, email, expertise FROM professors")
        rows = cur.fetchall()
        for row in rows:
            name, office, phone, email, expertise = row
            content = f"{name} 교수님 | 연구실: {office} | 연락처: {phone} | 이메일: {email} | 전공: {expertise}"
            collection.add(
                documents=[content],
                metadatas=[{"source": "professor", "name": name}],
                ids=[f"prof-{name}"]
            )
    except Exception as e:
        logging.error(f"교수 정보 추가 실패: {e}")

    conn.close()
    logging.info(f"{new_count}건 저장 완료 (중복 제외)")
    print(f"✅ PostgreSQL에 {new_count}건 저장 완료")

# -------------------- 입학정보처 크롤러 --------------------
def crawl_admission_notices():
    url = "https://ibsi.cu.ac.kr/kor/bbs/BBSMSTR_000000000090/lst.do"
    base_url = "https://ibsi.cu.ac.kr"
    res = requests.get(url)
    soup = BeautifulSoup(res.text, "html.parser")
    rows = soup.select("div.board.notice.list > ul > li")[1:]

    result = []
    for row in rows:
        title_tag = row.select_one("div.ntt_sj a")
        if title_tag:
            title = title_tag.get_text(strip=True)
            onclick_attr = title_tag.get("onclick", "")
            if "bbsMstrView(" in onclick_attr:
                notice_id = onclick_attr.split("bbsMstrView('")[1].split("'")[0]
                link = f"{base_url}/kor/BBSMSTR_000000000090/{notice_id}/view.do"
                result.append([datetime.now().isoformat(), "입학정보처", title, link])
    return result

# -------------------- 학교사이트 크롤러 --------------------
def crawl_school_notices():
    base_url = "https://www.cu.ac.kr"
    target_url = base_url + "/plaza/notice/notice"
    result = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(target_url)

        try:
            page.wait_for_selector("table", timeout=15000)
        except PlaywrightTimeout:
            print("❌ table 요소를 찾지 못했습니다 (타임아웃)")
            page.screenshot(path="school_timeout.png")
            browser.close()
            return []

        soup = BeautifulSoup(page.content(), "html.parser")
        rows = soup.select("table > tbody > tr")

        for row in rows:
            title_tag = row.select_one("td:nth-child(2) a")
            if title_tag:
                title = title_tag.get_text(strip=True)
                href = title_tag.get("href", "")
                if href.startswith("/"):
                    link = base_url + href
                    result.append([datetime.now().isoformat(), "학교사이트", title, link])

        browser.close()

    return result

# -------------------- 실행 루틴 --------------------
def run_crawlers():
    logging.info("크롤링 시작")
    print(f"⏰ 실행: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    all_data = []
    try:
        admission = crawl_admission_notices()
        school = crawl_school_notices()

        print("📘 입학정보처:", len(admission))
        print("🏫 학교사이트:", len(school))

        if admission: print("입학정보처 예시 →", admission[0])
        if school: print("학교사이트 예시 →", school[0])

        all_data.extend(admission)
        all_data.extend(school)

    except Exception as e:
        logging.error(f"크롤링 오류: {e}")
        print("❌ 오류 발생:", e)
        return

    save_to_postgres(all_data)

# -------------------- Gradio UI --------------------
with gr.Blocks(theme=gr.themes.Soft(), title="DCU 챗봇") as demo:
    with gr.Column():
        gr.Markdown("""
        ## 🎓 DCU 챗봇
        질문을 입력하면 최근 공지사항을 기반으로 안내해드릴게요.  
        예) `장학금`, `졸업`, `채용`, `휴학`, `ooo 교수님 정보`
        """)

    chatbot = gr.Chatbot(label="DCU 챗봇", type='messages')
    input_text = gr.Textbox(label="질문을 입력하세요", placeholder="예: 장학금 일정, 채용 공지 등")
    submit_btn = gr.Button("질문하기")
    state = gr.State([])

    def chatbot_reply(msg, history):
        full_reply = generate_gpt_reply(msg)
        history.append({"role": "user", "content": msg})
        reply = ""
        for char in full_reply:
            reply += char
        yield history + [{"role": "assistant", "content": reply}], history + [{"role": "assistant", "content": reply}]

    submit_btn.click(
        fn=chatbot_reply,
        inputs=[input_text, state],
        outputs=[chatbot, state]
    )

# -------------------- 메인 실행 --------------------
if __name__ == "__main__":
    run_crawlers()
    demo.launch(server_name="0.0.0.0", server_port=8000)