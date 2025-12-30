RAG 기반 학교 공지 챗봇 (Korean)
프로젝트 개요

본 프로젝트는 대학교 공지사항을 자동으로 수집·분석하여 사용자 질문에 정확한 답변을 제공하는 RAG(Retrieval-Augmented Generation) 기반 챗봇입니다.
LLM이 사전 학습된 지식에만 의존하지 않고, **실제 학교 공지 데이터를 검색(Retrieval)하여 이를 기반으로 응답을 생성(Generation)**하도록 설계되었습니다.

핵심 기능

공지사항 자동 크롤링

Selenium / Playwright 기반

지정된 학교 공지 페이지 및 사용자 입력 URL 지원

주기적 실행 (예: 1시간 단위)

데이터 관리

신규 공지사항만 필터링하여 저장

PostgreSQL에 원문 데이터 저장

ChromaDB를 활용한 벡터 데이터베이스 구성

RAG 기반 질의 응답

사용자 질문 → 임베딩 생성

벡터 DB에서 관련 문서 검색

검색 결과를 컨텍스트로 LLM 응답 생성

LLM 연동

OpenAI GPT-3.5 Turbo 사용

LLaMA 3 모델 적용 고려

Hugging Face 임베딩 및 llama_index 연동

UI

Gradio 기반 웹 인터페이스

실시간 질문/응답 지원

로그 관리

크롤링 및 챗봇 동작 로그 파일 기록

시스템 아키텍처 (RAG 구조)
[사용자 질문]
        ↓
[질문 임베딩 생성]
        ↓
[ChromaDB 벡터 검색]
        ↓
[관련 공지 문서 추출]
        ↓
[LLM(GPT / LLaMA)]
        ↓
[최종 응답 생성]

사용 기술

Language: Python

Crawler: Selenium, Playwright

Database: PostgreSQL

Vector DB: ChromaDB

LLM: OpenAI GPT-3.5 Turbo, LLaMA 3

Embedding: OpenAI / Hugging Face

Framework: llama_index

UI: Gradio

기대 효과

학교 공지사항 탐색 시간 단축

정확한 출처 기반 답변 제공

LLM 환각(Hallucination) 최소화

확장 가능한 RAG 챗봇 구조 확보
----------------------------------------------------------------------------------------------------------------------------------------------------------------------
RAG-based University Announcement Chatbot (English)
Project Overview

This project is a Retrieval-Augmented Generation (RAG) based chatbot designed to provide accurate answers to user queries using real university announcement data.
Instead of relying solely on pre-trained LLM knowledge, the chatbot retrieves relevant documents and generates responses grounded in actual data.

Key Features

Automated Announcement Crawling

Built with Selenium / Playwright

Supports predefined university pages and user-defined URLs

Periodic execution (e.g., hourly)

Data Management

Stores only newly detected announcements

Raw data stored in PostgreSQL

Vector embeddings stored in ChromaDB

RAG-based Question Answering

User query → embedding generation

Semantic search via vector database

LLM response generated using retrieved documents

LLM Integration

OpenAI GPT-3.5 Turbo

Planned support for LLaMA 3

Hugging Face embeddings via llama_index

User Interface

Gradio-based web UI

Real-time Q&A interaction

Logging

Crawling and chatbot activity logging

System Architecture (RAG Pipeline)
[User Query]
     ↓
[Query Embedding]
     ↓
[Vector Search (ChromaDB)]
     ↓
[Relevant Documents Retrieved]
     ↓
[LLM (GPT / LLaMA)]
     ↓
[Final Answer]

Tech Stack

Language: Python

Crawler: Selenium, Playwright

Database: PostgreSQL

Vector Database: ChromaDB

LLM: OpenAI GPT-3.5 Turbo, LLaMA 3

Embedding: OpenAI / Hugging Face

Framework: llama_index

UI: Gradio

Benefits

Faster access to university announcements

Answers grounded in real, up-to-date data

Reduced LLM hallucination

Scalable and extensible RAG architecture