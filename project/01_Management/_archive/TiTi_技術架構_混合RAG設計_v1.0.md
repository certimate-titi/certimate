\# TiTi｜技術架構設計文件  
\#\# 混合 RAG 系統設計 v1.0

\*\*Technical Architecture Document · 2026 年 4 月\*\*

\---

\#\# 一、架構總覽

TiTi 的 RAG 系統分為兩條平行的資料流，最終在「出題規劃層」匯合，產生一份結構化試卷。

\`\`\`  
┌─────────────────────────────────────────────────────────────────┐  
│                        使用者請求（出題）                          │  
└────────────────────────────┬────────────────────────────────────┘  
                             │  
                    ┌────────▼────────┐  
                    │   出題規劃層      │  ← 大綱考點樹 \+ 個人弱點分析  
                    │  (Exam Planner)  │     決定「要出哪些考點、幾題、難度」  
                    └────────┬────────┘  
                             │  考點清單（topic\_list）  
           ┌─────────────────┼─────────────────┐  
           │                                   │  
  ┌────────▼────────┐                ┌─────────▼───────┐  
  │   公共層 RAG     │                │   個人層 RAG     │  
  │  Public Retriever│                │ Personal Retriever│  
  │                 │                │                  │  
  │ • 考古題向量庫   │                │ • 使用者素材向量庫 │  
  │ • 命題大綱       │                │ • 轉譯/解析後文本  │  
  │ • 標準答案       │                │ • 個人筆記        │  
  └────────┬────────┘                └─────────┬────────┘  
           │  召回結果（高信度）               │  召回結果（中/低信度）  
           └─────────────────┬───────────────┘  
                             │  
                    ┌────────▼────────┐  
                    │   結果合併層      │  ← 去重、排序、信度標注  
                    │  (Result Merger) │  
                    └────────┬────────┘  
                             │  
                    ┌────────▼────────┐  
                    │   題目生成層      │  ← LLM 生成 \+ 答案驗證  
                    │ (Question Gen)   │  
                    └────────┬────────┘  
                             │  
                    ┌────────▼────────┐  
                    │   試卷組裝層      │  ← 結構校驗 \+ 信度標示輸出  
                    │  (Exam Builder)  │  
                    └─────────────────┘  
\`\`\`

\---

\#\# 二、資料層設計

\#\#\# 2.1 公共層（Public Layer）

由 TiTi 統一維護，所有使用者共用，是品質錨點的來源。

\`\`\`  
public\_db/  
├── exam\_questions/          \# 考古題主表  
│   ├── question\_id          \# UUID  
│   ├── exam\_type            \# 考試類別（金融/不動產/公職...）  
│   ├── exam\_name            \# 考試名稱（如：證券商業務員）  
│   ├── topic\_id             \# 考點 ID（對應 syllabus\_topics）  
│   ├── year                 \# 年份  
│   ├── question\_text        \# 題目全文  
│   ├── options              \# 選項 JSON（選擇題）  
│   ├── answer               \# 標準答案  
│   ├── explanation          \# 官方解析（若有）  
│   ├── difficulty           \# 難度標定 1–5  
│   ├── question\_type        \# 題型：single / multiple / essay  
│   └── source\_url           \# 考選部或公會來源 URL  
│  
├── syllabus\_topics/         \# 命題大綱考點樹  
│   ├── topic\_id  
│   ├── exam\_name  
│   ├── parent\_topic\_id      \# 樹狀結構  
│   ├── topic\_name           \# 考點名稱  
│   ├── topic\_level          \# 層級（章/節/條）  
│   ├── weight               \# 命題比例（%）  
│   └── keywords             \# 關鍵詞清單  
│  
└── public\_vectors/          \# 公共向量索引  
    ├── vector\_id  
    ├── question\_id          \# FK → exam\_questions  
    ├── topic\_id             \# FK → syllabus\_topics  
    ├── embedding            \# 向量（1536 維，text-embedding-3-large）  
    └── metadata             \# exam\_name, year, difficulty, question\_type  
\`\`\`

\#\#\# 2.2 個人層（Personal Layer）

每位使用者擁有獨立的個人空間，資料完全隔離。

\`\`\`  
personal\_db/{user\_id}/  
├── materials/               \# 上傳素材主表  
│   ├── material\_id  
│   ├── user\_id  
│   ├── file\_name  
│   ├── source\_type          \# pdf / youtube / audio / ppt / note  
│   ├── source\_url           \# YouTube URL 或上傳路徑  
│   ├── raw\_text             \# 轉譯/解析後的純文字  
│   ├── processing\_status    \# pending / processing / done / failed  
│   ├── quality\_score        \# 素材品質評分 0–1  
│   └── created\_at  
│  
├── material\_chunks/         \# 素材切塊  
│   ├── chunk\_id  
│   ├── material\_id          \# FK → materials  
│   ├── topic\_id             \# 標註的考點 ID（可為 null）  
│   ├── chunk\_text           \# 切塊文字  
│   ├── chunk\_index          \# 在素材中的位置  
│   └── confidence           \# 考點標註信心分數 0–1  
│  
├── personal\_vectors/        \# 個人向量索引  
│   ├── vector\_id  
│   ├── chunk\_id             \# FK → material\_chunks  
│   ├── topic\_id  
│   ├── embedding  
│   └── metadata             \# source\_type, quality\_score, confidence  
│  
├── coverage\_analysis/       \# 考點覆蓋度分析快取  
│   ├── exam\_name  
│   ├── topic\_id  
│   ├── chunk\_count          \# 該考點的素材數量  
│   ├── quality\_avg          \# 平均品質分  
│   ├── coverage\_status      \# sufficient / partial / missing  
│   └── updated\_at  
│  
└── learning\_records/        \# 作答歷程  
    ├── record\_id  
    ├── question\_id          \# 來源題目（考古題或 AI 生成）  
    ├── topic\_id  
    ├── is\_correct  
    ├── time\_spent\_sec  
    ├── exam\_session\_id  
    └── created\_at  
\`\`\`

\---

\#\# 三、出題規劃層（Exam Planner）

這是 TiTi 與 NotebookLM 最關鍵的差異——\*\*先規劃再召回，而非先召回再組合\*\*。

\#\#\# 3.1 考點清單生成流程

\`\`\`python  
def generate\_topic\_plan(  
    user\_id: str,  
    exam\_name: str,  
    total\_questions: int,  
    mode: str  \# "standard" | "weakness\_focus" | "custom"  
) \-\> TopicPlan:

    \# Step 1：從大綱取得考點權重  
    topics \= get\_syllabus\_topics(exam\_name)

    \# Step 2：取得使用者弱點分布  
    weakness\_map \= get\_weakness\_map(user\_id, exam\_name)  
    \# weakness\_map \= { topic\_id: weak\_score }  \# 0=強 1=弱

    \# Step 3：依模式計算各考點出題數  
    if mode \== "standard":  
        \# 完全依大綱比例  
        allocation \= allocate\_by\_weight(topics, total\_questions)

    elif mode \== "weakness\_focus":  
        \# 大綱比例 \* 弱點加權（弱點考點多出 1.5–2x）  
        allocation \= allocate\_with\_weakness(  
            topics, total\_questions, weakness\_map, boost=1.8  
        )

    elif mode \== "custom":  
        \# 使用者手動指定考點與題數  
        allocation \= get\_custom\_allocation(user\_id)

    \# Step 4：檢查每個考點的素材覆蓋度  
    for topic in allocation:  
        coverage \= get\_coverage\_status(user\_id, topic.topic\_id)  
        topic.coverage\_status \= coverage   \# sufficient/partial/missing  
        topic.preferred\_source \= decide\_source(coverage)  
        \# preferred\_source:  
        \#   sufficient → "personal\_first"（優先用個人素材）  
        \#   partial    → "mixed"（個人 \+ 公共混合）  
        \#   missing    → "public\_only"（純公共考古題）

    return TopicPlan(topics=allocation)  
\`\`\`

\#\#\# 3.2 出題分配範例

假設使用者要準備「證券商業務員」，出 20 題，弱點在「法規」章節：

\`\`\`  
考點              大綱比例  標準配題  弱點加權後配題  素材狀態  
─────────────────────────────────────────────────────  
證券交易法規       30%       6 題      9 題 (+1.5x)   ✅ sufficient  
財務分析           25%       5 題      5 題            ✅ sufficient  
投資學             20%       4 題      3 題 (-0.8x)   ⚠️ partial  
證券商管理         15%       3 題      2 題            ❌ missing  
市場機制           10%       2 題      1 題            ❌ missing  
─────────────────────────────────────────────────────  
合計                         20 題     20 題  
\`\`\`

\---

\#\# 四、混合 RAG 召回設計

\#\#\# 4.1 召回策略決策樹

\`\`\`  
for each topic in TopicPlan:

    preferred\_source \= topic.preferred\_source

    if preferred\_source \== "public\_only":  
        │  
        └─→ 僅從公共考古題召回  
            results \= public\_retriever.search(  
                topic\_id=topic.topic\_id,  
                n=topic.count \* 3,   \# 多召回供篩選  
                exclude\_seen=True    \# 排除使用者已做過的題  
            )  
            confidence\_label \= "🟢"

    elif preferred\_source \== "personal\_first":  
        │  
        ├─→ 先從個人素材召回  
        │   personal\_results \= personal\_retriever.search(  
        │       user\_id=user\_id,  
        │       topic\_id=topic.topic\_id,  
        │       n=topic.count \* 2  
        │   )  
        │  
        └─→ 不足時補充公共考古題  
            if len(personal\_results) \< topic.count:  
                gap \= topic.count \- len(personal\_results)  
                public\_results \= public\_retriever.search(  
                    topic\_id=topic.topic\_id, n=gap \* 2  
                )  
            confidence\_label \= "🟡"

    elif preferred\_source \== "mixed":  
        │  
        ├─→ 同時召回兩層，各取一半  
        │   personal\_results \= personal\_retriever.search(...)  
        │   public\_results   \= public\_retriever.search(...)  
        │  
        └─→ 合併後排序  
            confidence\_label \= "🟡" or "🔴"（依個人素材 quality\_score）  
\`\`\`

\#\#\# 4.2 向量檢索實作

\#\#\#\# 公共層檢索

\`\`\`python  
def public\_retriever\_search(  
    topic\_id: str,  
    n: int,  
    exam\_name: str,  
    difficulty\_range: tuple \= (1, 5),  
    exclude\_question\_ids: list \= \[\]  
) \-\> list\[PublicChunk\]:

    \# Hybrid Search：向量相似度 \+ metadata 過濾  
    results \= vector\_db.search(  
        collection="public\_vectors",  
        query\_embedding=embed(topic\_id),   \# 用考點名稱做 query  
        filter={  
            "topic\_id": topic\_id,  
            "exam\_name": exam\_name,  
            "difficulty": {"$gte": difficulty\_range\[0\],  
                           "$lte": difficulty\_range\[1\]},  
            "question\_id": {"$nin": exclude\_question\_ids}  
        },  
        top\_k=n,  
        score\_threshold=0.75  
    )

    return \[PublicChunk(  
        question\_id=r.metadata\["question\_id"\],  
        text=r.text,  
        answer=r.metadata\["answer"\],  
        difficulty=r.metadata\["difficulty"\],  
        source="public",  
        confidence="🟢"  
    ) for r in results\]  
\`\`\`

\#\#\#\# 個人層檢索

\`\`\`python  
def personal\_retriever\_search(  
    user\_id: str,  
    topic\_id: str,  
    n: int,  
    min\_quality: float \= 0.5  
) \-\> list\[PersonalChunk\]:

    results \= vector\_db.search(  
        collection=f"personal\_vectors\_{user\_id}",  
        query\_embedding=embed(topic\_id),  
        filter={  
            "topic\_id": topic\_id,  
            "quality\_score": {"$gte": min\_quality}  
        },  
        top\_k=n,  
        score\_threshold=0.70   \# 個人素材閾值略低（容忍度較高）  
    )

    return \[PersonalChunk(  
        chunk\_id=r.metadata\["chunk\_id"\],  
        text=r.text,  
        source\_type=r.metadata\["source\_type"\],  
        quality\_score=r.metadata\["quality\_score"\],  
        source="personal",  
        confidence=decide\_confidence(r.metadata\["quality\_score"\])  
        \# quality \>= 0.8 → 🟡  |  quality \< 0.8 → 🔴  
    ) for r in results\]  
\`\`\`

\#\#\# 4.3 結果合併層（Result Merger）

\`\`\`python  
def merge\_results(  
    public\_chunks: list\[PublicChunk\],  
    personal\_chunks: list\[PersonalChunk\],  
    topic: TopicAllocation  
) \-\> list\[MergedChunk\]:

    all\_chunks \= public\_chunks \+ personal\_chunks

    \# Step 1：去重（相似度 \> 0.92 視為重複，保留公共層版本）  
    deduped \= deduplicate(all\_chunks, threshold=0.92, prefer="public")

    \# Step 2：排序（公共 \> 個人高品質 \> 個人低品質）  
    source\_priority \= {"public": 3, "personal\_high": 2, "personal\_low": 1}  
    sorted\_chunks \= sorted(  
        deduped,  
        key=lambda c: (source\_priority\[c.source\_tier\], c.similarity\_score),  
        reverse=True  
    )

    \# Step 3：取前 N 筆  
    return sorted\_chunks\[:topic.count \* 2\]   \# 保留 2x 供 LLM 篩選  
\`\`\`

\---

\#\# 五、題目生成與驗證

\#\#\# 5.1 生成策略依考點來源決定

\`\`\`python  
def generate\_question(  
    chunk: MergedChunk,  
    topic: TopicAllocation,  
    exam\_context: ExamContext  
) \-\> GeneratedQuestion:

    if chunk.source \== "public":  
        \# 直接使用考古題，不重新生成  
        return use\_original\_question(chunk)

    else:  
        \# 以個人素材為基礎，生成新題  
        prompt \= build\_generation\_prompt(  
            chunk=chunk,  
            exam\_name=exam\_context.exam\_name,  
            topic\_name=topic.topic\_name,  
            question\_type=topic.question\_type,  
            difficulty=topic.target\_difficulty,  
            style\_reference=get\_style\_sample(exam\_context.exam\_name)  
            \# style\_reference：從考古題取 2–3 題作為風格範本  
        )  
        raw \= llm.generate(prompt)  
        question \= parse\_question(raw)

        \# 驗證：答案一致性檢查  
        question \= validate\_answer(question, chunk, exam\_context)

        return question  
\`\`\`

\#\#\# 5.2 答案驗證機制

\`\`\`python  
def validate\_answer(  
    question: GeneratedQuestion,  
    source\_chunk: MergedChunk,  
    exam\_context: ExamContext  
) \-\> GeneratedQuestion:

    \# 方法一：讓另一個 LLM 獨立作答，檢查是否選同一答案  
    verification\_answer \= llm\_judge.answer(  
        question=question.text,  
        options=question.options,  
        context=source\_chunk.text  
    )

    if verification\_answer \!= question.answer:  
        \# 答案不一致 → 降低信度標示 or 放棄此題  
        question.confidence \= "🔴"  
        question.needs\_review \= True

    \# 方法二：選擇題干擾項檢查  
    \# 確保錯誤選項不會「太明顯」或「也說得通」  
    distractor\_score \= evaluate\_distractors(question)  
    if distractor\_score \< 0.6:  
        question.needs\_review \= True

    return question  
\`\`\`

\#\#\# 5.3 生成 Prompt 結構

\`\`\`  
\[系統提示\]  
你是一位專業的{exam\_name}命題老師。  
請根據以下素材，生成一道符合{exam\_name}考試風格的{question\_type}題目。

\[風格範本\]（從考古題取樣）  
範例題一：{sample\_q1}  
範例題二：{sample\_q2}

\[素材內容\]  
{chunk.text}

\[命題要求\]  
\- 考點：{topic\_name}  
\- 難度：{difficulty}/5  
\- 題型：{question\_type}  
\- 選項數：4 個（若為選擇題）  
\- 答案必須能從素材中找到依據

\[輸出格式\]  
{  
  "question": "題目文字",  
  "options": \["A. ...", "B. ...", "C. ...", "D. ..."\],  
  "answer": "A",  
  "explanation": "解析文字（引用素材內容）",  
  "difficulty": 3,  
  "topic\_id": "{topic\_id}"  
}  
\`\`\`

\---

\#\# 六、考點覆蓋度分析

素材上傳後，在出題前先執行覆蓋度分析，主動告知使用者哪些考點素材不足。

\#\#\# 6.1 覆蓋度計算

\`\`\`python  
def analyze\_coverage(user\_id: str, exam\_name: str) \-\> CoverageReport:

    topics \= get\_syllabus\_topics(exam\_name)  
    report \= \[\]

    for topic in topics:  
        chunks \= get\_personal\_chunks\_by\_topic(user\_id, topic.topic\_id)

        \# 計算該考點的素材量與品質  
        chunk\_count \= len(chunks)  
        quality\_avg \= mean(\[c.quality\_score for c in chunks\]) if chunks else 0

        \# 閾值判斷  
        if chunk\_count \>= 5 and quality\_avg \>= 0.7:  
            status \= "sufficient"   \# 充足  
        elif chunk\_count \>= 2 or quality\_avg \>= 0.5:  
            status \= "partial"      \# 部分覆蓋  
        else:  
            status \= "missing"      \# 缺乏

        report.append(TopicCoverage(  
            topic=topic,  
            chunk\_count=chunk\_count,  
            quality\_avg=quality\_avg,  
            coverage\_status=status,  
            suggestion=build\_suggestion(topic, status)  
        ))

    return CoverageReport(  
        exam\_name=exam\_name,  
        topics=report,  
        overall\_readiness=calc\_readiness(report)  \# 0–100%  
    )  
\`\`\`

\#\#\# 6.2 覆蓋度報告呈現（前端邏輯）

\`\`\`  
備考準備度：72%  ████████████░░░░░░

考點覆蓋狀態：  
✅ 證券交易法規     充足（12 筆素材，品質 0.85）  
✅ 財務分析         充足（8 筆素材，品質 0.79）  
⚠️ 投資學           部分覆蓋（3 筆素材，品質 0.62）  
   → 建議補充：投資組合理論、效率市場假說相關教材  
❌ 證券商管理       缺乏（0 筆素材）  
   → 模擬考將僅使用考古題，題目多樣性受限  
❌ 市場機制         缺乏（0 筆素材）  
   → 同上  
\`\`\`

\---

\#\# 七、素材處理 Pipeline

\#\#\# 7.1 完整流程

\`\`\`  
使用者上傳素材  
       │  
       ▼  
┌──────────────┐  
│  格式偵測     │  PDF / YouTube URL / MP3 / PPT  
└──────┬───────┘  
       │  
  ┌────┴────────────────────────────────┐  
  │                                     │  
  ▼（文字型）                           ▼（音訊/影片型）  
┌──────────────┐                  ┌─────────────────┐  
│  文字解析     │                  │   語音轉文字     │  
│  OCR / parse │                  │   Whisper API   │  
└──────┬───────┘                  └────────┬────────┘  
       │                                   │  
       │                          ┌────────▼────────┐  
       │                          │  術語字典後處理   │  
       │                          │  （各考科專屬）   │  
       │                          └────────┬────────┘  
       └──────────────┬────────────────────┘  
                      │  
              ┌───────▼────────┐  
              │   文本清洗      │  去除頁碼/廣告/無關內容  
              └───────┬────────┘  
                      │  
              ┌───────▼────────┐  
              │   考點標註      │  LLM 自動標註 topic\_id  
              │   Tagger       │  \+ 信心分數  
              └───────┬────────┘  
                      │  
              ┌───────▼────────┐  
              │   Chunking     │  依語意切塊（非固定字數）  
              │   策略         │  考點邊界不跨塊切割  
              └───────┬────────┘  
                      │  
              ┌───────▼────────┐  
              │   向量化        │  text-embedding-3-large  
              │   Embedding    │  
              └───────┬────────┘  
                      │  
              ┌───────▼────────┐  
              │   寫入個人      │  personal\_vectors\_{user\_id}  
              │   向量索引      │  
              └───────┬────────┘  
                      │  
              ┌───────▼────────┐  
              │  更新覆蓋度      │  coverage\_analysis 快取  
              │  分析快取       │  
              └────────────────┘  
\`\`\`

\#\#\# 7.2 Chunking 策略

考試素材的 chunking 有別於一般文件，需要考慮考點邊界：

\`\`\`python  
def exam\_aware\_chunking(text: str, topic\_boundaries: list) \-\> list\[Chunk\]:  
    """  
    規則：  
    1\. 優先以「考點邊界」為切割點（章節標題、條號）  
    2\. 每塊維持 300–600 tokens  
    3\. 相鄰塊保留 50 tokens overlap，確保上下文連貫  
    4\. 不在題目中間切割（若素材含有練習題）  
    """  
    chunks \= \[\]  
    current\_chunk \= ""  
    current\_topic \= None

    for sentence in sentences(text):  
        detected\_topic \= detect\_topic\_boundary(sentence, topic\_boundaries)

        \# 遇到新考點邊界 → 強制切割  
        if detected\_topic and detected\_topic \!= current\_topic:  
            if current\_chunk:  
                chunks.append(Chunk(text=current\_chunk, topic\_id=current\_topic))  
            current\_chunk \= sentence  
            current\_topic \= detected\_topic

        \# 超過大小上限 → 在語意斷點切割  
        elif token\_count(current\_chunk \+ sentence) \> 600:  
            chunks.append(Chunk(text=current\_chunk, topic\_id=current\_topic))  
            current\_chunk \= get\_overlap(current\_chunk, 50\) \+ sentence

        else:  
            current\_chunk \+= sentence

    return chunks  
\`\`\`

\---

\#\# 八、向量資料庫架構建議

\#\#\# 8.1 Collection 設計

\`\`\`  
Vector DB（建議：Qdrant / Pinecone / Weaviate）

Collections：  
├── public\_exam\_vectors          \# 共用，所有使用者共享  
│   Payload fields:  
│   \- question\_id: string  
│   \- exam\_name: string  
│   \- topic\_id: string  
│   \- year: int  
│   \- difficulty: int (1-5)  
│   \- question\_type: string  
│   \- answer: string  
│  
└── personal\_vectors\_{user\_id}   \# 每位使用者獨立 Collection  
    Payload fields:  
    \- chunk\_id: string  
    \- material\_id: string  
    \- topic\_id: string  
    \- source\_type: string  
    \- quality\_score: float  
    \- confidence: float  
\`\`\`

\#\#\# 8.2 索引策略

\`\`\`python  
\# 公共層：建立複合索引加速多條件過濾  
public\_collection.create\_payload\_index("exam\_name", "keyword")  
public\_collection.create\_payload\_index("topic\_id", "keyword")  
public\_collection.create\_payload\_index("difficulty", "integer")

\# 個人層：建立品質分數索引，快速過濾低品質素材  
personal\_collection.create\_payload\_index("topic\_id", "keyword")  
personal\_collection.create\_payload\_index("quality\_score", "float")  
\`\`\`

\#\#\# 8.3 Embedding 模型選擇

| 用途 | 建議模型 | 說明 |  
|------|---------|------|  
| 中文考科主體 | \`text-embedding-3-large\` | 中英混合支援佳，1536 維 |  
| 輕量快速查詢 | \`text-embedding-3-small\` | 成本低，適合即時查詢 |  
| 離線/私有部署 | \`BGE-m3\`（BAAI） | 開源，多語言強，可自部署 |

\---

\#\# 九、API 設計

\#\#\# 9.1 核心端點

\`\`\`  
POST /api/exam/generate  
  Body: {  
    user\_id, exam\_name, total\_questions,  
    mode: "standard" | "weakness\_focus" | "custom",  
    custom\_topics?: \[{ topic\_id, count }\]  
  }  
  Response: { exam\_id, questions\[\], coverage\_warnings\[\] }

GET  /api/coverage/{user\_id}/{exam\_name}  
  Response: { overall\_readiness, topics\[{ topic, status, suggestion }\] }

POST /api/material/upload  
  Body: multipart/form-data { file, exam\_name, user\_id }  
  Response: { material\_id, processing\_job\_id }

GET  /api/material/status/{job\_id}  
  Response: { status, coverage\_delta, topics\_added\[\] }

POST /api/exam/submit  
  Body: { exam\_id, user\_id, answers\[\] }  
  Response: { score, topic\_breakdown, weakness\_update }  
\`\`\`

\#\#\# 9.2 召回流程時序

\`\`\`  
Client          ExamPlanner      PublicRAG       PersonalRAG      LLM  
  │                 │                │                │             │  
  │─ generate() ──▶│                │                │             │  
  │                 │─ get\_topics() ─▶               │             │  
  │                 │◀──────────────│                │             │  
  │                 │─ get\_weakness()────────────────▶             │  
  │                 │◀──────────────────────────────-│             │  
  │                 │                │                │             │  
  │                 │─ search() ────▶│                │             │  
  │                 │◀──────────────│                │             │  
  │                 │─ search() ─────────────────────▶             │  
  │                 │◀───────────────────────────────│             │  
  │                 │                │                │             │  
  │                 │─ merge\_and\_rank()              │             │  
  │                 │─ generate\_question() ──────────────────────▶│  
  │                 │◀───────────────────────────────────────────-│  
  │                 │─ validate\_answer() ─────────────────────────▶│  
  │                 │◀────────────────────────────────────────────│  
  │◀── exam\_data ──│                │                │             │  
\`\`\`

\---

\#\# 十、效能與擴展考量

\#\#\# 10.1 召回效能目標

| 操作 | 目標延遲 | 策略 |  
|------|---------|------|  
| 考點覆蓋度分析 | \< 500ms | 快取，素材更新後非同步更新 |  
| 單考點 RAG 召回 | \< 300ms | 向量索引 \+ payload 預過濾 |  
| 20 題試卷生成 | \< 15s | 並行出題（每題獨立 LLM call） |  
| 素材上傳處理 | 背景執行 | Job Queue（BullMQ / Celery） |

\#\#\# 10.2 並行出題設計

\`\`\`python  
async def generate\_exam\_parallel(topic\_plan: TopicPlan) \-\> Exam:  
    tasks \= \[\]  
    for topic in topic\_plan.topics:  
        for i in range(topic.count):  
            tasks.append(  
                asyncio.create\_task(  
                    generate\_single\_question(topic, i)  
                )  
            )  
    questions \= await asyncio.gather(\*tasks)  
    return assemble\_exam(questions)  
\`\`\`

\#\#\# 10.3 成本控制

\`\`\`  
每份 20 題模擬考的估算成本（GPT-4o 計算）：

考古題直接使用（🟢）：0 LLM call    → $0  
AI 生成題（🟡 個人素材）：  
  \- 生成：20 題 × \~800 tokens \= 16,000 tokens ≈ $0.08  
  \- 驗證：20 題 × \~400 tokens \=  8,000 tokens ≈ $0.04  
  小計：≈ $0.12/份

建議策略：  
  \- 考古題優先使用，降低 LLM call 數  
  \- 個人素材生成的題目快取，相同考點不重複生成  
  \- 低品質素材（quality \< 0.5）不進入生成，避免浪費 token  
\`\`\`

\---

\#\# 十一、Phase 1 MVP 最小技術堆疊

\`\`\`  
後端  
├── Framework:    FastAPI（Python）  
├── Vector DB:    Qdrant（self-hosted 或 cloud）  
├── Relational:   PostgreSQL  
├── Job Queue:    BullMQ（Node）or Celery（Python）  
├── LLM:          OpenAI GPT-4o（生成）+ text-embedding-3-large（向量）  
└── STT:          OpenAI Whisper API（音訊轉文字）

前端  
├── Framework:    React \+ TypeScript  
└── 現有平台:     certimate-titi.web.app（已有基礎）

Infrastructure  
├── 素材儲存:     S3 / GCS（使用者上傳）  
├── 向量索引:     Qdrant Cloud（MVP）→ 自部署（Scale）  
└── Cache:        Redis（覆蓋度分析快取）  
\`\`\`

\---

\> \*\*設計核心原則：公共層是品質的地板，個人層是個人化的天花板。混合 RAG 的責任不是「混在一起」，而是讓兩層各司其職，在正確的時機以正確的信度提供正確的素材。\*\*

\---

\*TiTi Technical Architecture Document v1.0 · 2026.04\*  
